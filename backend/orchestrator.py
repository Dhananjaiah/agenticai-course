"""
Orchestrator - The "boss agent" that coordinates all other agents using LangGraph.

This module contains the LangGraph StateGraph flow that:
1. Parses the user message to extract policyId and/or claimId
2. Decides which agents to call based on the extracted IDs
3. Calls the appropriate agents (PolicyAgent, ClaimsAgent, DocsAgent)
4. Merges the results and applies business rules
5. Sends the data to the LLM for a friendly response

The orchestrator uses LangGraph to define a stateful, directed graph
that coordinates the agent workflow.
"""

import re
import logging
from typing import Optional, TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from backend.agents import PolicyAgent, ClaimsAgent, DocsAgent
from backend.config.settings import get_settings

logger = logging.getLogger(__name__)


class OrchestratorInput(TypedDict):
    """Input to the orchestrator from the /chat endpoint."""
    userId: str
    message: str


class OrchestratorResult(TypedDict):
    """Result from the orchestrator containing all gathered data."""
    policy: Optional[dict]
    claim: Optional[dict]
    documents: Optional[dict]
    flags: dict
    answer: str


class MessageParser:
    """
    Parses user messages to extract policy IDs and claim IDs.
    
    Patterns recognized:
    - Policy IDs: POL-XXXX (e.g., POL-1234, POL-5678)
    - Claim IDs: CLM-XXXX (e.g., CLM-8899, CLM-1001)
    """
    
    # Regex patterns for ID extraction
    POLICY_ID_PATTERN = r'POL-\d+'
    CLAIM_ID_PATTERN = r'CLM-\d+'
    
    @classmethod
    def extract_policy_id(cls, message: str) -> Optional[str]:
        """
        Extract policy ID from a message.
        
        Args:
            message: User's message text
            
        Returns:
            Policy ID if found, None otherwise
        """
        match = re.search(cls.POLICY_ID_PATTERN, message, re.IGNORECASE)
        if match:
            return match.group().upper()
        return None
    
    @classmethod
    def extract_claim_id(cls, message: str) -> Optional[str]:
        """
        Extract claim ID from a message.
        
        Args:
            message: User's message text
            
        Returns:
            Claim ID if found, None otherwise
        """
        match = re.search(cls.CLAIM_ID_PATTERN, message, re.IGNORECASE)
        if match:
            return match.group().upper()
        return None
    
    @classmethod
    def parse(cls, message: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse a message and extract both policy ID and claim ID.
        
        Args:
            message: User's message text
            
        Returns:
            Tuple of (policy_id, claim_id), either can be None
        """
        policy_id = cls.extract_policy_id(message)
        claim_id = cls.extract_claim_id(message)
        
        logger.info(f"Parsed message: policy_id={policy_id}, claim_id={claim_id}")
        return policy_id, claim_id


class BusinessRules:
    """
    Applies business rules to the gathered data.
    
    This layer checks conditions and sets flags that will be used
    by the LLM to generate appropriate responses.
    """
    
    @staticmethod
    def apply(
        policy: Optional[dict],
        claim: Optional[dict],
        documents: Optional[dict],
        policy_id: Optional[str],
        claim_id: Optional[str]
    ) -> dict:
        """
        Apply business rules and return a flags dictionary.
        
        Args:
            policy: Policy data (or None if not found)
            claim: Claim data (or None if not found)
            documents: Documents data (or None if not fetched)
            policy_id: The requested policy ID
            claim_id: The requested claim ID
            
        Returns:
            Dictionary of flags indicating various conditions
        """
        flags = {
            "policy_not_found": False,
            "claim_not_found": False,
            "policy_claim_mismatch": False,
            "pending_documents": False,
            "claim_approved": False,
            "claim_rejected": False,
            "claim_under_review": False,
            "policy_expired": False,
            "missing_docs_list": [],
            "approved_amount": None,
            "rejection_reason": None,
        }
        
        # Check if policy was requested but not found
        if policy_id and not policy:
            flags["policy_not_found"] = True
            logger.warning(f"Business rule: Policy {policy_id} not found")
        
        # Check if claim was requested but not found
        if claim_id and not claim:
            flags["claim_not_found"] = True
            logger.warning(f"Business rule: Claim {claim_id} not found")
        
        # Check policy-claim mismatch
        if policy and claim:
            if policy.get("policyId") != claim.get("policyId"):
                flags["policy_claim_mismatch"] = True
                logger.warning("Business rule: Policy-claim mismatch detected")
        
        # Check claim status
        if claim:
            status = claim.get("status", "")
            
            if status == "APPROVED":
                flags["claim_approved"] = True
                flags["approved_amount"] = claim.get("approvedAmount")
                logger.info("Business rule: Claim is approved")
            
            elif status == "REJECTED":
                flags["claim_rejected"] = True
                flags["rejection_reason"] = claim.get("reasonIfRejected")
                logger.info("Business rule: Claim is rejected")
            
            elif status in ("OPEN", "UNDER_REVIEW"):
                flags["claim_under_review"] = True
                logger.info(f"Business rule: Claim is {status}")
        
        # Check for pending documents
        if documents:
            missing = documents.get("missingDocs", [])
            if missing:
                flags["pending_documents"] = True
                flags["missing_docs_list"] = missing
                logger.info(f"Business rule: {len(missing)} documents pending")
        
        # Check policy status
        if policy:
            if policy.get("status") == "EXPIRED":
                flags["policy_expired"] = True
                logger.info("Business rule: Policy is expired")
        
        return flags


# ============================================================================
# LangGraph State and Node Definitions
# ============================================================================


class AgentState(TypedDict):
    """
    LangGraph state schema for the insurance assistant workflow.
    
    This state is passed through each node in the graph and accumulates
    information as the workflow progresses.
    
    Attributes:
        user_id: The ID of the user making the request
        message: The original user message
        policy_id: Extracted policy ID (if any)
        claim_id: Extracted claim ID (if any)
        policy: Policy data fetched from PolicyAgent
        claim: Claim data fetched from ClaimsAgent
        documents: Document status from DocsAgent
        flags: Business rule flags
        answer: Final response (filled by LLM)
        error: Any error message
    """
    user_id: str
    message: str
    policy_id: Optional[str]
    claim_id: Optional[str]
    policy: Optional[dict]
    claim: Optional[dict]
    documents: Optional[dict]
    flags: dict
    answer: str
    error: Optional[str]


def create_parse_node(parser: type[MessageParser]):
    """
    Create the parse node for the LangGraph workflow.
    
    This node parses the user message to extract policy and claim IDs.
    """
    def parse_message(state: AgentState) -> AgentState:
        """Parse the user message to extract IDs."""
        logger.info("LangGraph Node: parse_message")
        message = state["message"]
        policy_id, claim_id = parser.parse(message)
        
        return {
            **state,
            "policy_id": policy_id,
            "claim_id": claim_id,
        }
    
    return parse_message


def create_policy_node(policy_agent: PolicyAgent):
    """
    Create the policy agent node for the LangGraph workflow.
    
    This node fetches policy data using the PolicyAgent.
    """
    def fetch_policy(state: AgentState) -> AgentState:
        """Fetch policy data if policy_id is available."""
        logger.info("LangGraph Node: fetch_policy")
        policy_id = state.get("policy_id")
        policy_data = None
        
        if policy_id:
            try:
                policy_data = policy_agent.get_policy(policy_id)
                logger.info(f"PolicyAgent: Retrieved policy {policy_id}")
            except Exception as e:
                logger.error(f"PolicyAgent error: {e}")
        
        return {
            **state,
            "policy": policy_data,
        }
    
    return fetch_policy


def create_claims_node(claims_agent: ClaimsAgent):
    """
    Create the claims agent node for the LangGraph workflow.
    
    This node fetches claim data using the ClaimsAgent.
    """
    def fetch_claim(state: AgentState) -> AgentState:
        """Fetch claim data if claim_id is available."""
        logger.info("LangGraph Node: fetch_claim")
        claim_id = state.get("claim_id")
        claim_data = None
        
        if claim_id:
            try:
                claim_data = claims_agent.get_claim(claim_id)
                logger.info(f"ClaimsAgent: Retrieved claim {claim_id}")
            except Exception as e:
                logger.error(f"ClaimsAgent error: {e}")
        
        return {
            **state,
            "claim": claim_data,
        }
    
    return fetch_claim


def create_policy_from_claim_node(policy_agent: PolicyAgent):
    """
    Create a node to fetch policy from claim data.
    
    If we have a claim but no policy_id, try to get policy from the claim's policyId.
    """
    def fetch_policy_from_claim(state: AgentState) -> AgentState:
        """Fetch policy data from claim if needed."""
        logger.info("LangGraph Node: fetch_policy_from_claim")
        claim_data = state.get("claim")
        policy_data = state.get("policy")
        policy_id = state.get("policy_id")
        
        # If we have a claim but no policy, try to get policy from claim
        if claim_data and not policy_data and not policy_id:
            policy_id_from_claim = claim_data.get("policyId")
            if policy_id_from_claim:
                try:
                    policy_data = policy_agent.get_policy(policy_id_from_claim)
                    logger.info(f"PolicyAgent: Retrieved policy {policy_id_from_claim} from claim")
                    return {
                        **state,
                        "policy": policy_data,
                        "policy_id": policy_id_from_claim,
                    }
                except Exception as e:
                    logger.error(f"PolicyAgent error (from claim): {e}")
        
        return state
    
    return fetch_policy_from_claim


def create_docs_node(docs_agent: DocsAgent):
    """
    Create the documents agent node for the LangGraph workflow.
    
    This node fetches document status using the DocsAgent.
    """
    def fetch_documents(state: AgentState) -> AgentState:
        """Fetch document status for claim or policy."""
        logger.info("LangGraph Node: fetch_documents")
        claim_data = state.get("claim")
        policy_id = state.get("policy_id")
        claim_id = state.get("claim_id")
        docs_data = None
        
        if claim_data:
            try:
                claim_type = claim_data.get("claimType", "")
                docs_data = docs_agent.get_docs_for_claim(claim_id, claim_type)
                logger.info(f"DocsAgent: Retrieved docs for claim {claim_id}")
            except Exception as e:
                logger.error(f"DocsAgent error: {e}")
        elif policy_id:
            try:
                docs_data = docs_agent.get_docs_for_policy(policy_id)
                logger.info(f"DocsAgent: Retrieved docs for policy {policy_id}")
            except Exception as e:
                logger.error(f"DocsAgent error: {e}")
        
        return {
            **state,
            "documents": docs_data,
        }
    
    return fetch_documents


def create_business_rules_node():
    """
    Create the business rules node for the LangGraph workflow.
    
    This node applies business rules to the gathered data.
    """
    def apply_business_rules(state: AgentState) -> AgentState:
        """Apply business rules and set flags."""
        logger.info("LangGraph Node: apply_business_rules")
        
        flags = BusinessRules.apply(
            policy=state.get("policy"),
            claim=state.get("claim"),
            documents=state.get("documents"),
            policy_id=state.get("policy_id"),
            claim_id=state.get("claim_id")
        )
        
        return {
            **state,
            "flags": flags,
        }
    
    return apply_business_rules


# Conditional routing functions for the graph


def should_fetch_policy(state: AgentState) -> Literal["fetch_policy", "fetch_claim"]:
    """Determine if we should fetch policy data first."""
    if state.get("policy_id"):
        return "fetch_policy"
    return "fetch_claim"


def should_fetch_policy_from_claim(state: AgentState) -> Literal["fetch_policy_from_claim", "fetch_documents"]:
    """Determine if we need to fetch policy from claim data."""
    claim_data = state.get("claim")
    policy_data = state.get("policy")
    
    if claim_data and not policy_data:
        return "fetch_policy_from_claim"
    return "fetch_documents"


class Orchestrator:
    """
    The main LangGraph orchestrator that coordinates all agents.
    
    This orchestrator uses LangGraph StateGraph to define a workflow that:
    1. Receives the user message
    2. Parses it to extract IDs
    3. Calls the appropriate agents using graph nodes
    4. Applies business rules
    5. Returns structured data for the LLM
    
    The workflow is defined as a directed graph where each node represents
    an agent or processing step, and edges define the flow between nodes.
    """
    
    def __init__(self):
        """Initialize the orchestrator with its helper agents and LangGraph workflow."""
        settings = get_settings()
        
        # Initialize agents based on environment
        use_mock = settings.env == "local"
        self.policy_agent = PolicyAgent(use_mock=use_mock)
        self.claims_agent = ClaimsAgent(use_mock=use_mock)
        self.docs_agent = DocsAgent(store_type=settings.docs_store_type)
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info(f"LangGraph Orchestrator initialized for env={settings.env}")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph workflow.
        
        The workflow is structured as:
        
        START -> parse_message -> fetch_policy -> fetch_claim -> 
                 fetch_policy_from_claim -> fetch_documents -> 
                 apply_business_rules -> END
        
        Returns:
            Compiled LangGraph StateGraph
        """
        # Create the graph with our state schema
        workflow = StateGraph(AgentState)
        
        # Create node functions with injected dependencies
        parse_node = create_parse_node(MessageParser)
        policy_node = create_policy_node(self.policy_agent)
        claims_node = create_claims_node(self.claims_agent)
        policy_from_claim_node = create_policy_from_claim_node(self.policy_agent)
        docs_node = create_docs_node(self.docs_agent)
        rules_node = create_business_rules_node()
        
        # Add nodes to the graph
        workflow.add_node("parse_message", parse_node)
        workflow.add_node("fetch_policy", policy_node)
        workflow.add_node("fetch_claim", claims_node)
        workflow.add_node("fetch_policy_from_claim", policy_from_claim_node)
        workflow.add_node("fetch_documents", docs_node)
        workflow.add_node("apply_business_rules", rules_node)
        
        # Define the edges (workflow flow)
        # START -> parse_message
        workflow.add_edge(START, "parse_message")
        
        # parse_message -> fetch_policy -> fetch_claim
        workflow.add_edge("parse_message", "fetch_policy")
        workflow.add_edge("fetch_policy", "fetch_claim")
        
        # fetch_claim -> fetch_policy_from_claim -> fetch_documents
        workflow.add_edge("fetch_claim", "fetch_policy_from_claim")
        workflow.add_edge("fetch_policy_from_claim", "fetch_documents")
        
        # fetch_documents -> apply_business_rules -> END
        workflow.add_edge("fetch_documents", "apply_business_rules")
        workflow.add_edge("apply_business_rules", END)
        
        # Compile the graph
        return workflow.compile()
    
    def process(self, input_data: OrchestratorInput) -> OrchestratorResult:
        """
        Process a user request through the LangGraph workflow.
        
        Args:
            input_data: Dictionary with userId and message
            
        Returns:
            OrchestratorResult with policy, claim, documents, flags, and answer
        """
        user_id = input_data["userId"]
        message = input_data["message"]
        
        logger.info(f"Processing request from user {user_id}: {message[:50]}...")
        
        # Initialize the state
        initial_state: AgentState = {
            "user_id": user_id,
            "message": message,
            "policy_id": None,
            "claim_id": None,
            "policy": None,
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        # Execute the LangGraph workflow
        final_state = self.graph.invoke(initial_state)
        
        # Convert to OrchestratorResult format
        result: OrchestratorResult = {
            "policy": final_state.get("policy"),
            "claim": final_state.get("claim"),
            "documents": final_state.get("documents"),
            "flags": final_state.get("flags", {}),
            "answer": ""  # Will be filled by LLM layer
        }
        
        logger.info("LangGraph workflow processing complete")
        return result
    
    def get_graph_visualization(self) -> str:
        """
        Get a Mermaid diagram representation of the workflow.
        
        Returns:
            Mermaid diagram string for visualization
        """
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.warning(f"Could not generate graph visualization: {e}")
            return ""
