"""
Tests for the message parser functionality.

These tests verify that the MessageParser correctly extracts
policy IDs and claim IDs from user messages.
"""

import pytest
from backend.orchestrator import MessageParser


class TestMessageParser:
    """Tests for the MessageParser class."""
    
    def test_extract_policy_id_basic(self):
        """Test basic policy ID extraction."""
        message = "What is the status of policy POL-1234?"
        result = MessageParser.extract_policy_id(message)
        assert result == "POL-1234"
    
    def test_extract_policy_id_lowercase(self):
        """Test policy ID extraction with lowercase input."""
        message = "Check pol-5678 please"
        result = MessageParser.extract_policy_id(message)
        assert result == "POL-5678"
    
    def test_extract_policy_id_in_sentence(self):
        """Test policy ID extraction from a longer sentence."""
        message = "I want to know about my policy POL-9999 and when it expires"
        result = MessageParser.extract_policy_id(message)
        assert result == "POL-9999"
    
    def test_extract_policy_id_not_found(self):
        """Test when no policy ID is present."""
        message = "What is my claim status?"
        result = MessageParser.extract_policy_id(message)
        assert result is None
    
    def test_extract_claim_id_basic(self):
        """Test basic claim ID extraction."""
        message = "What is the status of claim CLM-8899?"
        result = MessageParser.extract_claim_id(message)
        assert result == "CLM-8899"
    
    def test_extract_claim_id_lowercase(self):
        """Test claim ID extraction with lowercase input."""
        message = "Check clm-1001 status"
        result = MessageParser.extract_claim_id(message)
        assert result == "CLM-1001"
    
    def test_extract_claim_id_not_found(self):
        """Test when no claim ID is present."""
        message = "What is my policy status?"
        result = MessageParser.extract_claim_id(message)
        assert result is None
    
    def test_parse_both_ids(self):
        """Test extraction of both policy and claim IDs."""
        message = "Check claim CLM-8899 on policy POL-1234"
        policy_id, claim_id = MessageParser.parse(message)
        assert policy_id == "POL-1234"
        assert claim_id == "CLM-8899"
    
    def test_parse_only_policy(self):
        """Test parsing with only policy ID."""
        message = "Status of POL-1234"
        policy_id, claim_id = MessageParser.parse(message)
        assert policy_id == "POL-1234"
        assert claim_id is None
    
    def test_parse_only_claim(self):
        """Test parsing with only claim ID."""
        message = "Status of CLM-8899"
        policy_id, claim_id = MessageParser.parse(message)
        assert policy_id is None
        assert claim_id == "CLM-8899"
    
    def test_parse_no_ids(self):
        """Test parsing with no IDs."""
        message = "Hello, I need help"
        policy_id, claim_id = MessageParser.parse(message)
        assert policy_id is None
        assert claim_id is None
