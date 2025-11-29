"""
Settings module for the Agentic AI Insurance Assistant.

This module reads configuration from environment variables.
It supports three environments: local, staging, and prod.

For local development:
- Uses SQLite or in-memory mock data
- Uses a simple local folder or in-memory list for docs storage

For staging/prod:
- Placeholders are defined for real database URLs and credentials
"""

import os
from dataclasses import dataclass
from typing import Literal


# Define the environment type
EnvType = Literal["local", "staging", "prod"]


@dataclass
class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        env: The current environment (local, staging, or prod)
        policy_db_url: Connection string for the policy database
        claims_db_url: Connection string for the claims database
        docs_store_type: Type of document storage (s3, sharepoint, or mock)
        llm_api_key: API key for the LLM provider
        llm_bypass: If True, bypass LLM and return hard-coded responses (for testing)
    """
    env: EnvType
    policy_db_url: str
    claims_db_url: str
    docs_store_type: Literal["s3", "sharepoint", "mock"]
    llm_api_key: str
    llm_bypass: bool
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Create Settings instance from environment variables.
        
        Environment Variables:
            ENV: The environment (local, staging, prod). Default: local
            POLICY_DB_URL: Database URL for policy data. Default: sqlite:///policy.db
            CLAIMS_DB_URL: Database URL for claims data. Default: sqlite:///claims.db
            DOCS_STORE_TYPE: Document storage type (s3, sharepoint, mock). Default: mock
            LLM_API_KEY: API key for LLM provider. Default: empty string
            LLM_BYPASS: Set to "true" to bypass LLM calls. Default: false
        """
        env = os.getenv("ENV", "local")
        if env not in ("local", "staging", "prod"):
            env = "local"
        
        return cls(
            env=env,  # type: ignore
            policy_db_url=os.getenv("POLICY_DB_URL", "sqlite:///policy.db"),
            claims_db_url=os.getenv("CLAIMS_DB_URL", "sqlite:///claims.db"),
            docs_store_type=os.getenv("DOCS_STORE_TYPE", "mock"),  # type: ignore
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_bypass=os.getenv("LLM_BYPASS", "false").lower() == "true",
        )


# Create a global settings instance
# This will be loaded when the module is imported
settings = Settings.from_env()


def get_settings() -> Settings:
    """Get the current settings instance."""
    return settings
