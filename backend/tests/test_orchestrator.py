"""
Tests for the orchestrator functionality.

These tests verify that the Orchestrator correctly:
- Parses messages
- Calls the appropriate agents
- Applies business rules
- Returns merged results
"""

import pytest
from backend.orchestrator import Orchestrator, BusinessRules, OrchestratorInput


class TestBusinessRules:
    """Tests for the BusinessRules class."""
    
    def test_policy_not_found_flag(self):
        """Test that policy_not_found flag is set correctly."""
        flags = BusinessRules.apply(
            policy=None,
            claim=None,
            documents=None,
            policy_id="POL-1234",
            claim_id=None
        )
        
        assert flags["policy_not_found"] is True
    
    def test_claim_not_found_flag(self):
        """Test that claim_not_found flag is set correctly."""
        flags = BusinessRules.apply(
            policy=None,
            claim=None,
            documents=None,
            policy_id=None,
            claim_id="CLM-8899"
        )
        
        assert flags["claim_not_found"] is True
    
    def test_policy_claim_mismatch_flag(self):
        """Test that policy_claim_mismatch flag is set correctly."""
        policy = {"policyId": "POL-1234"}
        claim = {"policyId": "POL-5678", "status": "OPEN"}
        
        flags = BusinessRules.apply(
            policy=policy,
            claim=claim,
            documents=None,
            policy_id="POL-1234",
            claim_id="CLM-8899"
        )
        
        assert flags["policy_claim_mismatch"] is True
    
    def test_claim_approved_flag(self):
        """Test that claim_approved flag and amount are set correctly."""
        claim = {"status": "APPROVED", "approvedAmount": 45000.0, "policyId": "POL-1234"}
        
        flags = BusinessRules.apply(
            policy=None,
            claim=claim,
            documents=None,
            policy_id=None,
            claim_id="CLM-1001"
        )
        
        assert flags["claim_approved"] is True
        assert flags["approved_amount"] == 45000.0
    
    def test_claim_rejected_flag(self):
        """Test that claim_rejected flag and reason are set correctly."""
        claim = {
            "status": "REJECTED",
            "reasonIfRejected": "Policy does not cover this",
            "policyId": "POL-1234"
        }
        
        flags = BusinessRules.apply(
            policy=None,
            claim=claim,
            documents=None,
            policy_id=None,
            claim_id="CLM-2002"
        )
        
        assert flags["claim_rejected"] is True
        assert flags["rejection_reason"] == "Policy does not cover this"
    
    def test_pending_documents_flag(self):
        """Test that pending_documents flag is set correctly."""
        documents = {
            "requiredDocs": ["KYC", "Hospital Final Bill"],
            "uploadedDocs": ["KYC"],
            "missingDocs": ["Hospital Final Bill"]
        }
        
        flags = BusinessRules.apply(
            policy=None,
            claim=None,
            documents=documents,
            policy_id=None,
            claim_id=None
        )
        
        assert flags["pending_documents"] is True
        assert "Hospital Final Bill" in flags["missing_docs_list"]
    
    def test_policy_expired_flag(self):
        """Test that policy_expired flag is set correctly."""
        policy = {"policyId": "POL-9999", "status": "EXPIRED"}
        
        flags = BusinessRules.apply(
            policy=policy,
            claim=None,
            documents=None,
            policy_id="POL-9999",
            claim_id=None
        )
        
        assert flags["policy_expired"] is True


class TestOrchestrator:
    """Tests for the Orchestrator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
    
    def test_process_with_policy_id(self):
        """Test processing a request with only policy ID."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "What is the status of POL-1234?"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["policy"] is not None
        assert result["policy"]["policyId"] == "POL-1234"
        assert result["claim"] is None
    
    def test_process_with_claim_id(self):
        """Test processing a request with only claim ID."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "What is the status of CLM-8899?"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["claim"] is not None
        assert result["claim"]["claimId"] == "CLM-8899"
        # Should also fetch policy from claim
        assert result["policy"] is not None
        assert result["policy"]["policyId"] == "POL-1234"
    
    def test_process_with_both_ids(self):
        """Test processing a request with both policy and claim IDs."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "Check claim CLM-8899 on policy POL-1234"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["policy"] is not None
        assert result["claim"] is not None
        assert result["documents"] is not None
    
    def test_process_not_found(self):
        """Test processing a request for non-existent policy."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "Check POL-0000"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["policy"] is None
        assert result["flags"]["policy_not_found"] is True
    
    def test_process_no_ids(self):
        """Test processing a request with no IDs."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "Hello, I need help"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["policy"] is None
        assert result["claim"] is None
        assert result["documents"] is None
