"""
Tests for the agent functionality.

These tests verify that the PolicyAgent, ClaimsAgent, and DocsAgent
correctly return mock data in the expected format.
"""

import pytest
from backend.agents import PolicyAgent, ClaimsAgent, DocsAgent


class TestPolicyAgent:
    """Tests for the PolicyAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = PolicyAgent(use_mock=True)
    
    def test_get_policy_found(self):
        """Test getting an existing policy."""
        result = self.agent.get_policy("POL-1234")
        
        assert result is not None
        assert result["policyId"] == "POL-1234"
        assert result["customerName"] == "John Smith"
        assert result["productType"] == "Health"
        assert result["status"] == "ACTIVE"
        assert result["sumInsured"] == 500000.0
    
    def test_get_policy_not_found(self):
        """Test getting a non-existent policy."""
        result = self.agent.get_policy("POL-0000")
        assert result is None
    
    def test_get_policy_different_policies(self):
        """Test getting different policies."""
        policy_5678 = self.agent.get_policy("POL-5678")
        policy_9999 = self.agent.get_policy("POL-9999")
        
        assert policy_5678["productType"] == "Auto"
        assert policy_9999["status"] == "EXPIRED"


class TestClaimsAgent:
    """Tests for the ClaimsAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ClaimsAgent(use_mock=True)
    
    def test_get_claim_found(self):
        """Test getting an existing claim."""
        result = self.agent.get_claim("CLM-8899")
        
        assert result is not None
        assert result["claimId"] == "CLM-8899"
        assert result["policyId"] == "POL-1234"
        assert result["status"] == "UNDER_REVIEW"
        assert result["claimType"] == "Hospitalization"
    
    def test_get_claim_not_found(self):
        """Test getting a non-existent claim."""
        result = self.agent.get_claim("CLM-0000")
        assert result is None
    
    def test_get_claim_approved(self):
        """Test getting an approved claim."""
        result = self.agent.get_claim("CLM-1001")
        
        assert result["status"] == "APPROVED"
        assert result["approvedAmount"] == 45000.0
    
    def test_get_claim_rejected(self):
        """Test getting a rejected claim."""
        result = self.agent.get_claim("CLM-2002")
        
        assert result["status"] == "REJECTED"
        assert result["reasonIfRejected"] is not None
    
    def test_get_claims_by_policy(self):
        """Test getting all claims for a policy."""
        results = self.agent.get_claims_by_policy("POL-1234")
        
        assert len(results) == 3  # CLM-8899, CLM-1001, CLM-3003
        claim_ids = [c["claimId"] for c in results]
        assert "CLM-8899" in claim_ids
        assert "CLM-1001" in claim_ids
        assert "CLM-3003" in claim_ids


class TestDocsAgent:
    """Tests for the DocsAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = DocsAgent(store_type="mock")
    
    def test_get_docs_for_claim_with_missing(self):
        """Test getting documents for a claim with missing docs."""
        result = self.agent.get_docs_for_claim("CLM-8899", "Hospitalization")
        
        assert result is not None
        assert "KYC" in result["requiredDocs"]
        assert "Hospital Final Bill" in result["requiredDocs"]
        assert "KYC" in result["uploadedDocs"]
        assert "Hospital Final Bill" in result["missingDocs"]
    
    def test_get_docs_for_claim_complete(self):
        """Test getting documents for a claim with all docs uploaded."""
        result = self.agent.get_docs_for_claim("CLM-1001", "Hospitalization")
        
        assert result is not None
        assert len(result["missingDocs"]) == 0
    
    def test_get_docs_for_policy(self):
        """Test getting documents for a policy."""
        result = self.agent.get_docs_for_policy("POL-1234")
        
        assert result is not None
        assert "KYC" in result["requiredDocs"]
        assert len(result["missingDocs"]) == 0
    
    def test_get_docs_for_policy_with_missing(self):
        """Test getting documents for a policy with missing docs."""
        result = self.agent.get_docs_for_policy("POL-5678")
        
        assert result is not None
        assert "Policy Application Form" in result["missingDocs"]
