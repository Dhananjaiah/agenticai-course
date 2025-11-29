"""
ClaimsAgent - Fetches claim data from the claims database.

This agent is responsible for:
- Looking up claim information by claimId
- Returning normalized claim data in a consistent format

For local/test environments, it uses mock data.
For staging/prod, it would connect to a real claims database.
"""

from typing import Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClaimData:
    """
    Normalized claim data structure.
    
    Attributes:
        claimId: Unique identifier for the claim
        policyId: The policy this claim is linked to
        status: Current claim status (OPEN, APPROVED, REJECTED, UNDER_REVIEW)
        claimType: Type of claim (e.g., "Hospitalization", "Accident", "Theft")
        requestedAmount: Amount the customer requested
        approvedAmount: Amount approved (None if not yet decided)
        lastUpdated: Last update timestamp (ISO format)
        reasonIfRejected: Rejection reason (None if not rejected)
    """
    claimId: str
    policyId: str
    status: str
    claimType: str
    requestedAmount: float
    approvedAmount: Optional[float]
    lastUpdated: str
    reasonIfRejected: Optional[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Mock data for local development and testing
# In production, this would come from a real database
MOCK_CLAIMS = {
    "CLM-8899": ClaimData(
        claimId="CLM-8899",
        policyId="POL-1234",
        status="UNDER_REVIEW",
        claimType="Hospitalization",
        requestedAmount=75000.0,
        approvedAmount=None,
        lastUpdated="2024-03-15T10:30:00Z",
        reasonIfRejected=None
    ),
    "CLM-1001": ClaimData(
        claimId="CLM-1001",
        policyId="POL-1234",
        status="APPROVED",
        claimType="Hospitalization",
        requestedAmount=50000.0,
        approvedAmount=45000.0,
        lastUpdated="2024-02-01T14:00:00Z",
        reasonIfRejected=None
    ),
    "CLM-2002": ClaimData(
        claimId="CLM-2002",
        policyId="POL-5678",
        status="REJECTED",
        claimType="Accident",
        requestedAmount=30000.0,
        approvedAmount=None,
        lastUpdated="2024-03-01T09:15:00Z",
        reasonIfRejected="Policy does not cover this type of accident"
    ),
    "CLM-3003": ClaimData(
        claimId="CLM-3003",
        policyId="POL-1234",
        status="OPEN",
        claimType="Outpatient",
        requestedAmount=5000.0,
        approvedAmount=None,
        lastUpdated="2024-03-20T16:45:00Z",
        reasonIfRejected=None
    ),
}


class ClaimsAgent:
    """
    Agent that fetches and returns claim information.
    
    This agent is called by the orchestrator when a user asks about
    their claim status or when claim data is needed for context.
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize the ClaimsAgent.
        
        Args:
            use_mock: If True, use mock data. If False, connect to real DB.
                      For local environment, this is always True.
        """
        self.use_mock = use_mock
        logger.info(f"ClaimsAgent initialized (use_mock={use_mock})")
    
    def get_claim(self, claim_id: str) -> Optional[dict]:
        """
        Fetch claim data by claim ID.
        
        Args:
            claim_id: The unique identifier for the claim (e.g., "CLM-8899")
            
        Returns:
            A dictionary containing claim data, or None if not found.
            
        Example return value:
            {
                "claimId": "CLM-8899",
                "policyId": "POL-1234",
                "status": "UNDER_REVIEW",
                "claimType": "Hospitalization",
                "requestedAmount": 75000.0,
                "approvedAmount": null,
                "lastUpdated": "2024-03-15T10:30:00Z",
                "reasonIfRejected": null
            }
        """
        logger.info(f"ClaimsAgent: Looking up claim {claim_id}")
        
        if self.use_mock:
            # Use mock data for local development
            claim = MOCK_CLAIMS.get(claim_id)
            if claim:
                logger.info(f"ClaimsAgent: Found claim {claim_id}")
                return claim.to_dict()
            else:
                logger.warning(f"ClaimsAgent: Claim {claim_id} not found")
                return None
        else:
            # TODO: Implement real database lookup for staging/prod
            # This would connect to CLAIMS_DB_URL and run a query
            # For now, fall back to mock data
            logger.warning("Real DB not implemented, falling back to mock")
            claim = MOCK_CLAIMS.get(claim_id)
            return claim.to_dict() if claim else None
    
    def get_claims_by_policy(self, policy_id: str) -> list[dict]:
        """
        Fetch all claims for a given policy.
        
        Args:
            policy_id: The policy identifier (e.g., "POL-1234")
            
        Returns:
            A list of claim dictionaries for the given policy.
        """
        logger.info(f"ClaimsAgent: Looking up claims for policy {policy_id}")
        
        claims = []
        for claim in MOCK_CLAIMS.values():
            if claim.policyId == policy_id:
                claims.append(claim.to_dict())
        
        logger.info(f"ClaimsAgent: Found {len(claims)} claims for policy {policy_id}")
        return claims
