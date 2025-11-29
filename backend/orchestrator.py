"""
Orchestrator - The "boss agent" that coordinates all other agents.

This module contains the LangGraph flow that:
1. Parses the user message to extract policyId and/or claimId
2. Decides which agents to call based on the extracted IDs
3. Calls the appropriate agents (PolicyAgent, ClaimsAgent, DocsAgent)
4. Merges the results and applies business rules
5. Sends the data to the LLM for a friendly response

The orchestrator is the central brain of the system.
"""

import re
import logging
from typing import Optional, TypedDict
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


class Orchestrator:
    """
    The main orchestrator that coordinates all agents.
    
    This is the "boss agent" that:
    1. Receives the user message
    2. Parses it to extract IDs
    3. Calls the appropriate agents
    4. Applies business rules
    5. Returns structured data for the LLM
    """
    
    def __init__(self):
        """Initialize the orchestrator with its helper agents."""
        settings = get_settings()
        
        # Initialize agents based on environment
        use_mock = settings.env == "local"
        self.policy_agent = PolicyAgent(use_mock=use_mock)
        self.claims_agent = ClaimsAgent(use_mock=use_mock)
        self.docs_agent = DocsAgent(store_type=settings.docs_store_type)
        
        logger.info(f"Orchestrator initialized for env={settings.env}")
    
    def process(self, input_data: OrchestratorInput) -> OrchestratorResult:
        """
        Process a user request through the agent pipeline.
        
        Args:
            input_data: Dictionary with userId and message
            
        Returns:
            OrchestratorResult with policy, claim, documents, flags, and answer
        """
        user_id = input_data["userId"]
        message = input_data["message"]
        
        logger.info(f"Processing request from user {user_id}: {message[:50]}...")
        
        # Step 1: Parse the message to extract IDs
        policy_id, claim_id = MessageParser.parse(message)
        
        # Step 2: Call agents based on what we found
        policy_data = None
        claim_data = None
        docs_data = None
        
        # Always try to get policy if policy_id is available
        if policy_id:
            try:
                policy_data = self.policy_agent.get_policy(policy_id)
            except Exception as e:
                logger.error(f"Error fetching policy: {e}")
        
        # Try to get claim if claim_id is available
        if claim_id:
            try:
                claim_data = self.claims_agent.get_claim(claim_id)
            except Exception as e:
                logger.error(f"Error fetching claim: {e}")
        
        # If we have a claim but no policy_id, try to get policy from claim
        if claim_data and not policy_id:
            policy_id = claim_data.get("policyId")
            if policy_id:
                try:
                    policy_data = self.policy_agent.get_policy(policy_id)
                except Exception as e:
                    logger.error(f"Error fetching policy from claim: {e}")
        
        # Get document status if we have a claim
        if claim_data:
            try:
                claim_type = claim_data.get("claimType", "")
                docs_data = self.docs_agent.get_docs_for_claim(claim_id, claim_type)
            except Exception as e:
                logger.error(f"Error fetching documents: {e}")
        elif policy_id:
            # If only policy, get policy-level documents
            try:
                docs_data = self.docs_agent.get_docs_for_policy(policy_id)
            except Exception as e:
                logger.error(f"Error fetching policy documents: {e}")
        
        # Step 3: Apply business rules
        flags = BusinessRules.apply(
            policy=policy_data,
            claim=claim_data,
            documents=docs_data,
            policy_id=policy_id,
            claim_id=claim_id
        )
        
        # Step 4: Return the structured result (answer will be filled by LLM layer)
        result: OrchestratorResult = {
            "policy": policy_data,
            "claim": claim_data,
            "documents": docs_data,
            "flags": flags,
            "answer": ""  # Will be filled by LLM layer
        }
        
        logger.info("Orchestrator processing complete")
        return result
