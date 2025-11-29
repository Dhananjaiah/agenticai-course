"""
LLM Answer Builder - Generates friendly responses using LangChain LLM models.

This module:
1. Takes structured data from the orchestrator (policy, claim, docs, flags)
2. Formats it into a prompt for the LLM using LangChain
3. Calls the LLM to generate a customer-friendly response
4. Returns the response

For local/test environments, it can bypass the LLM and return hard-coded responses.
Supports OpenAI, Azure OpenAI, and other LangChain-compatible LLM providers.
"""

import logging
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.base import BaseLanguageModel

from backend.config.settings import get_settings
from backend.orchestrator import OrchestratorResult

logger = logging.getLogger(__name__)


class LLMAnswerBuilder:
    """
    Builds customer-friendly answers using LangChain LLM models.
    
    The builder:
    - Takes structured data from the orchestrator
    - Creates a prompt with the data using LangChain ChatPromptTemplate
    - Calls the LLM via LangChain (or returns a mock response)
    - Returns the final answer
    
    Supports OpenAI and other LangChain-compatible LLM providers.
    """
    
    # System prompt that tells the LLM how to respond
    SYSTEM_PROMPT = """You are a helpful insurance assistant. 
Your job is to explain policy and claim information to customers in simple, friendly language.

Guidelines:
- Be concise but informative
- Use simple language, avoid jargon
- If documents are missing, clearly list what's needed
- If a claim is approved, mention the approved amount
- If a claim is rejected, explain the reason kindly
- Always be polite and helpful

Respond in 2-3 sentences maximum."""

    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """
        Initialize the LLM answer builder.
        
        Args:
            llm: Optional LangChain LLM model. If not provided, will attempt
                 to create one from settings or use mock responses.
        """
        self.settings = get_settings()
        self.llm = llm
        self._chain = None
        
        # Create LangChain prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template("{user_prompt}")
        ])
        
        # Initialize LLM chain if API key is available
        if not self.settings.llm_bypass and self.settings.llm_api_key:
            self._initialize_llm_chain()
        
        logger.info(f"LLMAnswerBuilder initialized (bypass={self.settings.llm_bypass})")
    
    def _initialize_llm_chain(self):
        """
        Initialize the LangChain LLM chain.
        
        This sets up the chain with the configured LLM provider.
        """
        try:
            if self.llm is None:
                # Try to create OpenAI LLM if API key is available
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    api_key=self.settings.llm_api_key,
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    max_tokens=200
                )
                logger.info("Initialized ChatOpenAI LLM")
            
            # Create the chain: prompt -> llm -> output parser
            self._chain = self.prompt_template | self.llm | StrOutputParser()
            logger.info("LangChain chain initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import LLM provider: {e}")
            self._chain = None
        except Exception as e:
            logger.error(f"Error initializing LLM chain: {e}")
            self._chain = None
    
    def _create_prompt(self, result: OrchestratorResult) -> str:
        """
        Create a prompt for the LLM based on the orchestrator result.
        
        Args:
            result: The structured result from the orchestrator
            
        Returns:
            A formatted prompt string for the LLM
        """
        prompt_parts = ["Based on the following information, provide a helpful response:\n"]
        
        # Add policy info if available
        if result["policy"]:
            policy = result["policy"]
            prompt_parts.append(f"\nPolicy Information:")
            prompt_parts.append(f"- Policy ID: {policy.get('policyId')}")
            prompt_parts.append(f"- Customer: {policy.get('customerName')}")
            prompt_parts.append(f"- Product: {policy.get('productType')}")
            prompt_parts.append(f"- Status: {policy.get('status')}")
            prompt_parts.append(f"- Valid: {policy.get('startDate')} to {policy.get('endDate')}")
        
        # Add claim info if available
        if result["claim"]:
            claim = result["claim"]
            prompt_parts.append(f"\nClaim Information:")
            prompt_parts.append(f"- Claim ID: {claim.get('claimId')}")
            prompt_parts.append(f"- Type: {claim.get('claimType')}")
            prompt_parts.append(f"- Status: {claim.get('status')}")
            prompt_parts.append(f"- Requested Amount: ${claim.get('requestedAmount'):,.2f}")
            if claim.get('approvedAmount'):
                prompt_parts.append(f"- Approved Amount: ${claim.get('approvedAmount'):,.2f}")
            if claim.get('reasonIfRejected'):
                prompt_parts.append(f"- Rejection Reason: {claim.get('reasonIfRejected')}")
        
        # Add document info if available
        if result["documents"]:
            docs = result["documents"]
            if docs.get("missingDocs"):
                prompt_parts.append(f"\nMissing Documents: {', '.join(docs['missingDocs'])}")
        
        # Add flags information
        flags = result["flags"]
        prompt_parts.append(f"\nStatus Flags:")
        if flags.get("policy_not_found"):
            prompt_parts.append("- Policy was not found")
        if flags.get("claim_not_found"):
            prompt_parts.append("- Claim was not found")
        if flags.get("policy_claim_mismatch"):
            prompt_parts.append("- The claim doesn't match the policy")
        if flags.get("pending_documents"):
            prompt_parts.append("- Documents are pending")
        if flags.get("claim_approved"):
            prompt_parts.append("- Claim has been approved")
        if flags.get("claim_rejected"):
            prompt_parts.append("- Claim has been rejected")
        if flags.get("claim_under_review"):
            prompt_parts.append("- Claim is under review")
        if flags.get("policy_expired"):
            prompt_parts.append("- Policy has expired")
        
        return "\n".join(prompt_parts)
    
    def _generate_mock_response(self, result: OrchestratorResult) -> str:
        """
        Generate a mock response without calling the LLM.
        Used for local development and testing.
        
        Args:
            result: The structured result from the orchestrator
            
        Returns:
            A mock response string
        """
        flags = result["flags"]
        parts = []
        
        # Handle not found cases
        if flags.get("policy_not_found"):
            return "I couldn't find the policy you're looking for. Please check the policy number and try again."
        
        if flags.get("claim_not_found"):
            return "I couldn't find the claim you're looking for. Please check the claim number and try again."
        
        # Build response based on what we have
        policy = result["policy"]
        claim = result["claim"]
        docs = result["documents"]
        
        if policy:
            status = policy.get("status", "").lower()
            parts.append(f"Your policy {policy.get('policyId')} is {status}.")
        
        if claim:
            claim_id = claim.get("claimId")
            claim_status = claim.get("status", "")
            
            if claim_status == "APPROVED":
                amount = claim.get("approvedAmount", 0)
                parts.append(f"Claim {claim_id} has been approved for ${amount:,.2f}.")
            elif claim_status == "REJECTED":
                reason = claim.get("reasonIfRejected", "unspecified reasons")
                parts.append(f"Claim {claim_id} was rejected due to: {reason}.")
            elif claim_status in ("OPEN", "UNDER_REVIEW"):
                parts.append(f"Claim {claim_id} is currently under review.")
        
        # Add missing docs info
        if docs and docs.get("missingDocs"):
            missing = docs["missingDocs"]
            if len(missing) == 1:
                parts.append(f"We still need the {missing[0]} before we can proceed.")
            else:
                parts.append(f"We still need the following documents: {', '.join(missing)}.")
        
        if not parts:
            return "I don't have enough information to help you. Please provide a policy number (like POL-1234) or claim number (like CLM-8899)."
        
        return " ".join(parts)
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM using LangChain.
        
        Args:
            prompt: The formatted prompt
            
        Returns:
            The LLM's response
        """
        if self._chain is None:
            logger.warning("LangChain chain not initialized, returning placeholder")
            return "This is a placeholder response. Configure LLM_API_KEY for real responses."
        
        try:
            # Invoke the LangChain chain
            response = self._chain.invoke({"user_prompt": prompt})
            return response
        except Exception as e:
            logger.error(f"Error calling LLM via LangChain: {e}")
            raise
    
    def build_answer(self, result: OrchestratorResult) -> str:
        """
        Build the final customer-facing answer.
        
        Args:
            result: The structured result from the orchestrator
            
        Returns:
            A friendly, customer-facing response string
        """
        logger.info("Building answer from orchestrator result")
        
        # If LLM is bypassed (for testing/local), use mock response
        if self.settings.llm_bypass or not self.settings.llm_api_key:
            logger.info("Using mock response (LLM bypassed or no API key)")
            return self._generate_mock_response(result)
        
        # Create prompt and call LLM
        prompt = self._create_prompt(result)
        logger.debug(f"Generated prompt: {prompt[:200]}...")
        
        try:
            answer = self._call_llm(prompt)
            logger.info("LLM response received successfully")
            return answer
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            # Fall back to mock response on error
            return self._generate_mock_response(result)
