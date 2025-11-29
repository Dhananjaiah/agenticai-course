"""
DocsAgent - Fetches document status from the document storage.

This agent is responsible for:
- Checking which documents are required for a policy or claim
- Checking which documents have been uploaded
- Identifying missing documents

For local/test environments, it uses mock data.
For staging/prod, it would connect to S3, SharePoint, or other storage.
"""

from typing import Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocsData:
    """
    Document status data structure.
    
    Attributes:
        requiredDocs: List of documents required for the policy/claim
        uploadedDocs: List of documents that have been uploaded
        missingDocs: List of documents still needed (computed)
    """
    requiredDocs: list[str]
    uploadedDocs: list[str]
    missingDocs: list[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Mock data for local development and testing
# In production, this would come from S3, SharePoint, etc.

# Required documents by claim type
REQUIRED_DOCS_BY_CLAIM_TYPE = {
    "Hospitalization": ["KYC", "Hospital Final Bill", "Discharge Summary", "Doctor Prescription"],
    "Accident": ["KYC", "Police Report", "Hospital Records", "Photos of Damage"],
    "Outpatient": ["KYC", "Doctor Prescription", "Medical Bills"],
    "Theft": ["KYC", "Police Report", "Proof of Ownership", "Photos"],
}

# Mock uploaded documents by claim ID
MOCK_UPLOADED_DOCS = {
    "CLM-8899": ["KYC", "Discharge Summary"],  # Missing: Hospital Final Bill, Doctor Prescription
    "CLM-1001": ["KYC", "Hospital Final Bill", "Discharge Summary", "Doctor Prescription"],  # Complete
    "CLM-2002": ["KYC", "Police Report"],  # Missing: Hospital Records, Photos of Damage
    "CLM-3003": ["KYC"],  # Missing: Doctor Prescription, Medical Bills
}

# Default required docs for policies without claims
DEFAULT_POLICY_DOCS = ["KYC", "Policy Application Form", "ID Proof"]

# Mock uploaded documents by policy ID (for policy-level docs)
MOCK_POLICY_DOCS = {
    "POL-1234": ["KYC", "Policy Application Form", "ID Proof"],  # Complete
    "POL-5678": ["KYC", "ID Proof"],  # Missing: Policy Application Form
    "POL-9999": ["KYC"],  # Missing: Policy Application Form, ID Proof
}


class DocsAgent:
    """
    Agent that checks document status for policies and claims.
    
    This agent is called by the orchestrator to determine:
    - What documents are required
    - What documents have been uploaded
    - What documents are still missing
    """
    
    def __init__(self, store_type: str = "mock"):
        """
        Initialize the DocsAgent.
        
        Args:
            store_type: Type of document storage ("mock", "s3", "sharepoint")
                        For local environment, this is always "mock".
        """
        self.store_type = store_type
        logger.info(f"DocsAgent initialized (store_type={store_type})")
    
    def get_docs_for_claim(self, claim_id: str, claim_type: str) -> Optional[dict]:
        """
        Get document status for a specific claim.
        
        Args:
            claim_id: The claim identifier (e.g., "CLM-8899")
            claim_type: The type of claim (e.g., "Hospitalization")
            
        Returns:
            A dictionary containing document status, or None if error.
            
        Example return value:
            {
                "requiredDocs": ["KYC", "Hospital Final Bill", "Discharge Summary"],
                "uploadedDocs": ["KYC", "Discharge Summary"],
                "missingDocs": ["Hospital Final Bill"]
            }
        """
        logger.info(f"DocsAgent: Checking documents for claim {claim_id}")
        
        if self.store_type == "mock":
            # Get required documents based on claim type
            required = REQUIRED_DOCS_BY_CLAIM_TYPE.get(claim_type, ["KYC"])
            
            # Get uploaded documents for this claim
            uploaded = MOCK_UPLOADED_DOCS.get(claim_id, [])
            
            # Calculate missing documents
            missing = [doc for doc in required if doc not in uploaded]
            
            result = DocsData(
                requiredDocs=required,
                uploadedDocs=uploaded,
                missingDocs=missing
            )
            
            logger.info(f"DocsAgent: Claim {claim_id} has {len(missing)} missing documents")
            return result.to_dict()
        else:
            # TODO: Implement real S3/SharePoint lookup for staging/prod
            # For now, fall back to mock
            logger.warning(f"Store type {self.store_type} not implemented, falling back to mock")
            return self.get_docs_for_claim(claim_id, claim_type)
    
    def get_docs_for_policy(self, policy_id: str) -> Optional[dict]:
        """
        Get document status for a policy (policy-level documents).
        
        Args:
            policy_id: The policy identifier (e.g., "POL-1234")
            
        Returns:
            A dictionary containing document status, or None if error.
        """
        logger.info(f"DocsAgent: Checking documents for policy {policy_id}")
        
        if self.store_type == "mock":
            required = DEFAULT_POLICY_DOCS
            uploaded = MOCK_POLICY_DOCS.get(policy_id, [])
            missing = [doc for doc in required if doc not in uploaded]
            
            result = DocsData(
                requiredDocs=required,
                uploadedDocs=uploaded,
                missingDocs=missing
            )
            
            logger.info(f"DocsAgent: Policy {policy_id} has {len(missing)} missing documents")
            return result.to_dict()
        else:
            logger.warning(f"Store type {self.store_type} not implemented, falling back to mock")
            return self.get_docs_for_policy(policy_id)
