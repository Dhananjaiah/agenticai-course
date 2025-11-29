"""
PolicyAgent - Fetches policy data from the policy database.

This agent is responsible for:
- Looking up policy information by policyId
- Returning normalized policy data in a consistent format

For local/test environments, it uses mock data.
For staging/prod, it would connect to a real policy database.
"""

from typing import Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PolicyData:
    """
    Normalized policy data structure.
    
    Attributes:
        policyId: Unique identifier for the policy
        customerName: Name of the policy holder
        productType: Type of insurance product (e.g., "Health", "Auto", "Life")
        startDate: Policy start date (ISO format)
        endDate: Policy end date (ISO format)
        status: Current policy status (e.g., "ACTIVE", "EXPIRED", "CANCELLED")
        sumInsured: Total coverage amount
    """
    policyId: str
    customerName: str
    productType: str
    startDate: str
    endDate: str
    status: str
    sumInsured: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Mock data for local development and testing
# In production, this would come from a real database
MOCK_POLICIES = {
    "POL-1234": PolicyData(
        policyId="POL-1234",
        customerName="John Smith",
        productType="Health",
        startDate="2024-01-01",
        endDate="2024-12-31",
        status="ACTIVE",
        sumInsured=500000.0
    ),
    "POL-5678": PolicyData(
        policyId="POL-5678",
        customerName="Jane Doe",
        productType="Auto",
        startDate="2024-06-01",
        endDate="2025-05-31",
        status="ACTIVE",
        sumInsured=100000.0
    ),
    "POL-9999": PolicyData(
        policyId="POL-9999",
        customerName="Bob Wilson",
        productType="Life",
        startDate="2022-01-01",
        endDate="2023-12-31",
        status="EXPIRED",
        sumInsured=1000000.0
    ),
}


class PolicyAgent:
    """
    Agent that fetches and returns policy information.
    
    This agent is called by the orchestrator when a user asks about
    their policy status or when policy data is needed for context.
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize the PolicyAgent.
        
        Args:
            use_mock: If True, use mock data. If False, connect to real DB.
                      For local environment, this is always True.
        """
        self.use_mock = use_mock
        logger.info(f"PolicyAgent initialized (use_mock={use_mock})")
    
    def get_policy(self, policy_id: str) -> Optional[dict]:
        """
        Fetch policy data by policy ID.
        
        Args:
            policy_id: The unique identifier for the policy (e.g., "POL-1234")
            
        Returns:
            A dictionary containing policy data, or None if not found.
            
        Example return value:
            {
                "policyId": "POL-1234",
                "customerName": "John Smith",
                "productType": "Health",
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
                "status": "ACTIVE",
                "sumInsured": 500000.0
            }
        """
        logger.info(f"PolicyAgent: Looking up policy {policy_id}")
        
        if self.use_mock:
            # Use mock data for local development
            policy = MOCK_POLICIES.get(policy_id)
            if policy:
                logger.info(f"PolicyAgent: Found policy {policy_id}")
                return policy.to_dict()
            else:
                logger.warning(f"PolicyAgent: Policy {policy_id} not found")
                return None
        else:
            # TODO: Implement real database lookup for staging/prod
            # This would connect to POLICY_DB_URL and run a query
            # For now, fall back to mock data
            logger.warning("Real DB not implemented, falling back to mock")
            policy = MOCK_POLICIES.get(policy_id)
            return policy.to_dict() if policy else None
