# Backend API and LangGraph Setup

## Lecture Outline

1. FastAPI basics for our /chat endpoint
2. Request and response models
3. How we wire the orchestrator into the API
4. Environment configuration
5. Key files walkthrough

---

## Introduction

In this module, you'll learn how we build the backend API. We'll look at:

- How FastAPI handles incoming requests
- How we validate data with Pydantic
- How we connect the API to our LangGraph orchestrator
- How we manage configuration for different environments

Let's dive in!

---

## FastAPI: The Basics

FastAPI is a modern Python web framework. It's fast, easy to use, and has automatic documentation.

Here's the simplest possible FastAPI app:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello, World!"}
```

That's it! FastAPI handles:
- Routing (mapping URLs to functions)
- JSON serialization
- Input validation
- Auto-generated docs at `/docs`

---

## Our /chat Endpoint

Our main endpoint is `POST /chat`. Let's look at what it does.

### Request Model

First, we define what data we expect:

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    userId: str    # Who is asking
    message: str   # What they're asking
```

When someone sends a request, FastAPI automatically validates it. If `userId` or `message` is missing, they get an error.

### Response Model

We also define what we return:

```python
class ChatResponse(BaseModel):
    answer: str           # The friendly response
    data: DataResponse    # Structured data (policy, claim, docs)
```

### The Endpoint

Here's the actual endpoint code:

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Prepare input for orchestrator
    orchestrator_input = {
        "userId": request.userId,
        "message": request.message
    }
    
    # 2. Process through orchestrator
    result = orchestrator.process(orchestrator_input)
    
    # 3. Generate answer using LLM
    answer = llm_builder.build_answer(result)
    
    # 4. Build and return response
    return ChatResponse(
        answer=answer,
        data=DataResponse(
            policy=result["policy"],
            claim=result["claim"],
            documents=result["documents"]
        )
    )
```

That's the heart of our API. Let me explain each part.

---

## Connecting to the Orchestrator

The orchestrator is initialized when the app starts:

```python
from backend.orchestrator import Orchestrator
from backend.llm_builder import LLMAnswerBuilder

# Create instances at startup
orchestrator = Orchestrator()
llm_builder = LLMAnswerBuilder()
```

When a request comes in:

1. We pass the message to `orchestrator.process()`
2. The orchestrator calls the agents and applies business rules
3. We get back structured data
4. We pass that to `llm_builder.build_answer()`
5. We return everything to the user

---

## The Health Endpoint

Every production API needs a health check. Kubernetes uses this to know if your app is ready.

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.env
    }
```

Simple, but essential. If this returns 200, the app is running.

---

## Environment Configuration

One of the key principles is: **same code, different config**.

We use environment variables to control behavior:

```python
# backend/config/settings.py

import os
from dataclasses import dataclass

@dataclass
class Settings:
    env: str                # local, staging, or prod
    policy_db_url: str      # Database connection
    claims_db_url: str      # Database connection
    docs_store_type: str    # s3, sharepoint, or mock
    llm_api_key: str        # API key for LLM
    llm_bypass: bool        # Skip LLM in tests
    
    @classmethod
    def from_env(cls):
        return cls(
            env=os.getenv("ENV", "local"),
            policy_db_url=os.getenv("POLICY_DB_URL", "sqlite:///policy.db"),
            claims_db_url=os.getenv("CLAIMS_DB_URL", "sqlite:///claims.db"),
            docs_store_type=os.getenv("DOCS_STORE_TYPE", "mock"),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_bypass=os.getenv("LLM_BYPASS", "false").lower() == "true",
        )

settings = Settings.from_env()
```

**Why do we do this?**

- In **local**: We use mock data and bypass the LLM
- In **staging**: We use test databases
- In **prod**: We use real databases and the real LLM

The code is the same. Only the environment variables change.

---

## Key Files Walkthrough

Let's look at the important files in `/backend`:

### `main.py`
This is the entry point. It creates the FastAPI app and defines the endpoints.

```
backend/
├── main.py              # FastAPI app, endpoints
├── orchestrator.py      # LangGraph orchestrator
├── llm_builder.py       # LLM answer generation
├── config/
│   └── settings.py      # Environment configuration
├── agents/
│   ├── policy_agent.py  # Policy data fetching
│   ├── claims_agent.py  # Claims data fetching
│   └── docs_agent.py    # Document status checking
└── tests/
    └── ...              # Test files
```

### `orchestrator.py`
The "boss agent" that coordinates everything. We'll cover this in detail in the next module.

### `llm_builder.py`
Takes structured data and asks the LLM to create a friendly response.

### `config/settings.py`
Reads environment variables and provides them to the rest of the app.

### `agents/`
The three helper agents. Each one knows how to fetch specific data.

---

## Running the API Locally

To run the API on your machine:

```bash
# Set environment variables
export ENV=local
export LLM_BYPASS=true

# Install dependencies
pip install -r backend/requirements.txt

# Run the server
uvicorn backend.main:app --reload
```

Now visit:
- http://localhost:8000/docs - Interactive API docs
- http://localhost:8000/health - Health check

Try sending a request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "Status of CLM-8899"}'
```

You should get a response with policy, claim, and document information!

---

## Error Handling

We wrap our endpoint in try/except to handle errors gracefully:

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # ... process request ...
        return response
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again."
        )
```

This ensures users get a clean error message, not a Python stack trace.

---

## Logging

We use Python's built-in logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# In the endpoint:
logger.info(f"Chat request from user {request.userId}")
```

Logs are essential for debugging in production.

---

## Mini Quiz

1. **What does FastAPI automatically do for us?**
   - a) Write tests
   - b) Validate input, serialize JSON, generate docs
   - c) Deploy to Kubernetes

2. **Why do we use Pydantic models for requests?**
   - a) They look nice
   - b) Automatic validation of incoming data
   - c) They're required by Python

3. **What's the purpose of the health endpoint?**
   - a) Let users check their health
   - b) Let Kubernetes know the app is running
   - c) Generate reports

4. **Why do we use environment variables for configuration?**
   - a) Same code can run in different environments
   - b) It's faster
   - c) Python requires it

5. **What happens if someone sends a request missing the `message` field?**
   - a) The app crashes
   - b) FastAPI returns a 422 validation error
   - c) The message is set to empty string

---

## Answers

1. **b** - Validate input, serialize JSON, generate docs
2. **b** - Automatic validation of incoming data
3. **b** - Let Kubernetes know the app is running
4. **a** - Same code can run in different environments
5. **b** - FastAPI returns a 422 validation error

---

## What's Next?

In the next module, we'll look at the three agents in detail: PolicyAgent, ClaimsAgent, and DocsAgent. You'll see exactly what data each one returns and how they work.

Let's keep going! 🚀
