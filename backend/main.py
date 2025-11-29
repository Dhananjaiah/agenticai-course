"""
FastAPI Main Application - Agentic AI Insurance Assistant

This is the main entry point for the backend API.
It provides two endpoints:
- POST /chat - Process user messages and return AI-generated responses
- GET /health - Health check endpoint for readiness probes

The /chat endpoint connects to the LangGraph orchestrator,
which coordinates the various agents (Policy, Claims, Docs)
to gather information and generate helpful responses.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.config.settings import get_settings
from backend.orchestrator import Orchestrator, OrchestratorInput
from backend.llm_builder import LLMAnswerBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings early for lifespan
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info(f"Application started in {settings.env} environment")
    yield
    # Shutdown
    logger.info("Application shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Agentic AI Insurance Assistant",
    description="AI-powered chatbot for insurance policy and claims inquiries",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# In production, you should set ALLOWED_ORIGINS environment variable
# to a comma-separated list of allowed origins (e.g., "https://app.example.com,https://www.example.com")
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
if settings.env == "prod" and allowed_origins == ["*"]:
    logger.warning("CORS is configured to allow all origins in production. "
                   "Set ALLOWED_ORIGINS environment variable for security.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = Orchestrator()
llm_builder = LLMAnswerBuilder()

logger.info(f"Application starting in {settings.env} environment")


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    """
    Request model for the /chat endpoint.
    
    Attributes:
        userId: Unique identifier for the user making the request
        message: The user's question or message
    """
    userId: str
    message: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "userId": "user-123",
                    "message": "What is the status of my claim CLM-8899?"
                }
            ]
        }
    }


class PolicyResponse(BaseModel):
    """Policy data in the response."""
    policyId: Optional[str] = None
    customerName: Optional[str] = None
    productType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    status: Optional[str] = None
    sumInsured: Optional[float] = None


class ClaimResponse(BaseModel):
    """Claim data in the response."""
    claimId: Optional[str] = None
    policyId: Optional[str] = None
    status: Optional[str] = None
    claimType: Optional[str] = None
    requestedAmount: Optional[float] = None
    approvedAmount: Optional[float] = None
    lastUpdated: Optional[str] = None
    reasonIfRejected: Optional[str] = None


class DocumentsResponse(BaseModel):
    """Documents data in the response."""
    requiredDocs: Optional[list[str]] = None
    uploadedDocs: Optional[list[str]] = None
    missingDocs: Optional[list[str]] = None


class DataResponse(BaseModel):
    """Structured data in the chat response."""
    policy: Optional[PolicyResponse] = None
    claim: Optional[ClaimResponse] = None
    documents: Optional[DocumentsResponse] = None


class ChatResponse(BaseModel):
    """
    Response model for the /chat endpoint.
    
    Attributes:
        answer: The AI-generated friendly response text
        data: Structured data about the policy, claim, and documents
    """
    answer: str
    data: DataResponse
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "Your policy POL-1234 is active. Claim CLM-8899 is under review. We still need the Hospital Final Bill before we can finish the review.",
                    "data": {
                        "policy": {
                            "policyId": "POL-1234",
                            "customerName": "John Smith",
                            "productType": "Health",
                            "startDate": "2024-01-01",
                            "endDate": "2024-12-31",
                            "status": "ACTIVE",
                            "sumInsured": 500000.0
                        },
                        "claim": {
                            "claimId": "CLM-8899",
                            "policyId": "POL-1234",
                            "status": "UNDER_REVIEW",
                            "claimType": "Hospitalization",
                            "requestedAmount": 75000.0,
                            "approvedAmount": None,
                            "lastUpdated": "2024-03-15T10:30:00Z",
                            "reasonIfRejected": None
                        },
                        "documents": {
                            "requiredDocs": ["KYC", "Hospital Final Bill", "Discharge Summary", "Doctor Prescription"],
                            "uploadedDocs": ["KYC", "Discharge Summary"],
                            "missingDocs": ["Hospital Final Bill", "Doctor Prescription"]
                        }
                    }
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    status: str
    environment: str


# --- Endpoints ---

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a user message and return an AI-generated response.
    
    This endpoint:
    1. Receives the user's message
    2. Passes it to the LangGraph orchestrator
    3. The orchestrator calls the appropriate agents (Policy, Claims, Docs)
    4. Business rules are applied to the gathered data
    5. The LLM generates a friendly response
    6. Returns the response along with structured data
    
    Args:
        request: ChatRequest with userId and message
        
    Returns:
        ChatResponse with the answer and structured data
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    logger.info(f"Chat request from user {request.userId}")
    
    try:
        # Prepare input for orchestrator
        orchestrator_input: OrchestratorInput = {
            "userId": request.userId,
            "message": request.message
        }
        
        # Process through orchestrator
        result = orchestrator.process(orchestrator_input)
        
        # Generate answer using LLM
        answer = llm_builder.build_answer(result)
        result["answer"] = answer
        
        # Build response
        data_response = DataResponse(
            policy=PolicyResponse(**result["policy"]) if result["policy"] else None,
            claim=ClaimResponse(**result["claim"]) if result["claim"] else None,
            documents=DocumentsResponse(**result["documents"]) if result["documents"] else None
        )
        
        response = ChatResponse(
            answer=answer,
            data=data_response
        )
        
        logger.info(f"Chat response generated for user {request.userId}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again later."
        )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint for readiness probes.
    
    Returns:
        HealthResponse with status and environment info
    """
    return HealthResponse(
        status="healthy",
        environment=settings.env
    )



# --- Main Entry Point ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
