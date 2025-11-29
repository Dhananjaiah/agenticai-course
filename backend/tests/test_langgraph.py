"""
Tests for LangGraph-based orchestrator functionality.

These tests verify that the LangGraph StateGraph workflow:
- Correctly processes states through the graph nodes
- Maintains proper state transitions
- Provides proper graph structure
"""

import pytest
from backend.orchestrator import (
    Orchestrator,
    AgentState,
    MessageParser,
    BusinessRules,
    create_parse_node,
    create_policy_node,
    create_claims_node,
    create_docs_node,
    create_business_rules_node,
    OrchestratorInput,
)
from backend.agents import PolicyAgent, ClaimsAgent, DocsAgent


class TestLangGraphState:
    """Tests for LangGraph state management."""
    
    def test_agent_state_structure(self):
        """Test that AgentState has all required fields."""
        state: AgentState = {
            "user_id": "test-user",
            "message": "Test message",
            "policy_id": None,
            "claim_id": None,
            "policy": None,
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        assert state["user_id"] == "test-user"
        assert state["message"] == "Test message"
        assert state["policy_id"] is None
        assert state["flags"] == {}


class TestLangGraphNodes:
    """Tests for individual LangGraph nodes."""
    
    def test_parse_node(self):
        """Test the parse message node."""
        parse_node = create_parse_node(MessageParser)
        
        state: AgentState = {
            "user_id": "test-user",
            "message": "What is the status of POL-1234?",
            "policy_id": None,
            "claim_id": None,
            "policy": None,
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        result = parse_node(state)
        
        assert result["policy_id"] == "POL-1234"
        assert result["claim_id"] is None
    
    def test_parse_node_with_claim(self):
        """Test parsing a message with claim ID."""
        parse_node = create_parse_node(MessageParser)
        
        state: AgentState = {
            "user_id": "test-user",
            "message": "Check CLM-8899 status",
            "policy_id": None,
            "claim_id": None,
            "policy": None,
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        result = parse_node(state)
        
        assert result["policy_id"] is None
        assert result["claim_id"] == "CLM-8899"
    
    def test_policy_node(self):
        """Test the policy fetch node."""
        policy_agent = PolicyAgent(use_mock=True)
        policy_node = create_policy_node(policy_agent)
        
        state: AgentState = {
            "user_id": "test-user",
            "message": "Test",
            "policy_id": "POL-1234",
            "claim_id": None,
            "policy": None,
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        result = policy_node(state)
        
        assert result["policy"] is not None
        assert result["policy"]["policyId"] == "POL-1234"
    
    def test_claims_node(self):
        """Test the claims fetch node."""
        claims_agent = ClaimsAgent(use_mock=True)
        claims_node = create_claims_node(claims_agent)
        
        state: AgentState = {
            "user_id": "test-user",
            "message": "Test",
            "policy_id": None,
            "claim_id": "CLM-8899",
            "policy": None,
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        result = claims_node(state)
        
        assert result["claim"] is not None
        assert result["claim"]["claimId"] == "CLM-8899"
    
    def test_docs_node(self):
        """Test the documents fetch node."""
        docs_agent = DocsAgent(store_type="mock")
        docs_node = create_docs_node(docs_agent)
        
        state: AgentState = {
            "user_id": "test-user",
            "message": "Test",
            "policy_id": "POL-1234",
            "claim_id": "CLM-8899",
            "policy": None,
            "claim": {"claimId": "CLM-8899", "claimType": "Hospitalization"},
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        result = docs_node(state)
        
        assert result["documents"] is not None
        assert "requiredDocs" in result["documents"]
    
    def test_business_rules_node(self):
        """Test the business rules node."""
        rules_node = create_business_rules_node()
        
        state: AgentState = {
            "user_id": "test-user",
            "message": "Test",
            "policy_id": "POL-1234",
            "claim_id": None,
            "policy": {"policyId": "POL-1234", "status": "ACTIVE"},
            "claim": None,
            "documents": None,
            "flags": {},
            "answer": "",
            "error": None,
        }
        
        result = rules_node(state)
        
        assert result["flags"] is not None
        assert result["flags"]["policy_not_found"] is False


class TestLangGraphOrchestrator:
    """Tests for the LangGraph-based Orchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
    
    def test_orchestrator_has_graph(self):
        """Test that orchestrator has a compiled LangGraph graph."""
        assert self.orchestrator.graph is not None
    
    def test_orchestrator_process_with_policy(self):
        """Test processing a request with policy ID through the graph."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "What is the status of POL-1234?"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["policy"] is not None
        assert result["policy"]["policyId"] == "POL-1234"
        assert result["claim"] is None
    
    def test_orchestrator_process_with_claim(self):
        """Test processing a request with claim ID through the graph."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "Check status of CLM-8899"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["claim"] is not None
        assert result["claim"]["claimId"] == "CLM-8899"
        # Should also fetch policy from claim
        assert result["policy"] is not None
    
    def test_orchestrator_process_with_both(self):
        """Test processing a request with both IDs through the graph."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "Check POL-1234 and CLM-8899"
        }
        
        result = self.orchestrator.process(input_data)
        
        assert result["policy"] is not None
        assert result["claim"] is not None
        assert result["documents"] is not None
        assert result["flags"] is not None
    
    def test_orchestrator_returns_flags(self):
        """Test that orchestrator returns business rule flags."""
        input_data: OrchestratorInput = {
            "userId": "user-123",
            "message": "Check CLM-8899"
        }
        
        result = self.orchestrator.process(input_data)
        
        # CLM-8899 is under review and has missing docs
        assert result["flags"]["claim_under_review"] is True
        assert result["flags"]["pending_documents"] is True
    
    def test_graph_visualization(self):
        """Test that graph visualization can be generated."""
        mermaid = self.orchestrator.get_graph_visualization()
        # Mermaid diagram should be a non-empty string (or empty if not supported)
        assert isinstance(mermaid, str)


class TestLangGraphIntegration:
    """Integration tests for the complete LangGraph workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()
    
    def test_full_workflow_policy_only(self):
        """Test complete workflow with only a policy ID."""
        result = self.orchestrator.process({
            "userId": "user-1",
            "message": "Tell me about POL-5678"
        })
        
        assert result["policy"]["policyId"] == "POL-5678"
        assert result["policy"]["customerName"] == "Jane Doe"
        assert result["claim"] is None
        assert result["documents"] is not None  # Policy-level docs
    
    def test_full_workflow_claim_only(self):
        """Test complete workflow with only a claim ID."""
        result = self.orchestrator.process({
            "userId": "user-1",
            "message": "Status of CLM-1001"
        })
        
        assert result["claim"]["claimId"] == "CLM-1001"
        assert result["claim"]["status"] == "APPROVED"
        assert result["policy"]["policyId"] == "POL-1234"  # Fetched from claim
        assert result["flags"]["claim_approved"] is True
    
    def test_full_workflow_rejected_claim(self):
        """Test complete workflow with a rejected claim."""
        result = self.orchestrator.process({
            "userId": "user-1",
            "message": "Check CLM-2002"
        })
        
        assert result["claim"]["status"] == "REJECTED"
        assert result["flags"]["claim_rejected"] is True
        assert result["flags"]["rejection_reason"] is not None
    
    def test_full_workflow_not_found(self):
        """Test complete workflow when policy is not found."""
        result = self.orchestrator.process({
            "userId": "user-1",
            "message": "Check POL-9999"  # Exists but expired
        })
        
        assert result["policy"] is not None
        assert result["flags"]["policy_expired"] is True
