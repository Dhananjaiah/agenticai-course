# Agentic AI Insurance Assistant

An AI-powered chatbot backend for insurance policy and claims inquiries. Built with FastAPI, LangGraph, and designed for production deployment on Kubernetes.

## What This Project Does

When a customer asks a question like "What is the status of my claim CLM-8899?", this system:

1. **Parses the message** to extract policy/claim IDs
2. **Calls specialized agents** to fetch relevant data:
   - PolicyAgent → Gets policy information
   - ClaimsAgent → Gets claim status
   - DocsAgent → Checks document requirements
3. **Applies business rules** to identify issues (missing docs, expired policies, etc.)
4. **Generates a friendly response** using an LLM

**Example Response:**
> "Your policy POL-1234 is active. Claim CLM-8899 is under review. We still need the hospital's final bill before we can finish processing it."

## Project Structure

```
.
├── backend/                    # FastAPI backend application
│   ├── main.py                # Main FastAPI app with endpoints
│   ├── orchestrator.py        # LangGraph orchestrator (boss agent)
│   ├── llm_builder.py         # LLM response generation
│   ├── config/                # Configuration and settings
│   │   └── settings.py        # Environment-based configuration
│   ├── agents/                # Specialized data-fetching agents
│   │   ├── policy_agent.py    # Policy data agent
│   │   ├── claims_agent.py    # Claims data agent
│   │   └── docs_agent.py      # Document status agent
│   └── tests/                 # Automated tests
│       ├── test_parser.py     # Message parsing tests
│       ├── test_agents.py     # Agent tests
│       ├── test_orchestrator.py # Orchestrator tests
│       └── test_api.py        # API endpoint tests
│
├── infra/                      # Infrastructure configurations
│   ├── local/                 # Local development setup
│   │   ├── docker-compose.yml # Docker Compose for local dev
│   │   ├── Dockerfile         # Container image definition
│   │   └── start.sh           # Local startup script
│   ├── staging/               # Kubernetes staging manifests
│   │   ├── configmap.yaml     # Staging configuration
│   │   ├── secret.yaml        # Staging secrets (placeholder)
│   │   ├── deployment.yaml    # Staging deployment
│   │   └── service.yaml       # Staging service
│   └── production/            # Kubernetes production manifests
│       ├── configmap.yaml     # Production configuration
│       ├── secret.yaml        # Production secrets (placeholder)
│       ├── deployment.yaml    # Production deployment + PDB
│       └── service.yaml       # Production service + HPA
│
├── course/                     # Udemy-style course content
│   ├── 00-overview.md
│   ├── 01-architecture-and-flow.md
│   ├── 02-backend-api-and-langgraph-setup.md
│   ├── 03-policy-claims-docs-agents.md
│   ├── 04-local-environment-and-testing.md
│   ├── 05-staging-environment-and-internal-testing.md
│   ├── 06-production-deployment-and-operations.md
│   └── 07-monitoring-logging-future-work.md
│
├── pyproject.toml              # Python project configuration
└── README.md                   # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized development)
- kubectl (for Kubernetes deployment)

### Run Locally with Python

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Set environment variables
export ENV=local
export LLM_BYPASS=true

# 4. Run the server
uvicorn backend.main:app --reload

# 5. Test it
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "Status of CLM-8899"}'
```

### Run Locally with Docker

```bash
cd infra/local
docker-compose up --build
```

### Run Tests

```bash
pytest backend/tests/ -v
```

## API Endpoints

### POST /chat

Process a user message and return an AI-generated response.

**Request:**
```json
{
  "userId": "user-123",
  "message": "What is the status of my claim CLM-8899?"
}
```

**Response:**
```json
{
  "answer": "Your policy POL-1234 is active. Claim CLM-8899 is under review. We still need the Hospital Final Bill and Doctor Prescription.",
  "data": {
    "policy": {
      "policyId": "POL-1234",
      "customerName": "John Smith",
      "productType": "Health",
      "status": "ACTIVE",
      "sumInsured": 500000.0
    },
    "claim": {
      "claimId": "CLM-8899",
      "status": "UNDER_REVIEW",
      "claimType": "Hospitalization",
      "requestedAmount": 75000.0
    },
    "documents": {
      "requiredDocs": ["KYC", "Hospital Final Bill", "Discharge Summary", "Doctor Prescription"],
      "uploadedDocs": ["KYC", "Discharge Summary"],
      "missingDocs": ["Hospital Final Bill", "Doctor Prescription"]
    }
  }
}
```

### GET /health

Health check endpoint for Kubernetes readiness probes.

**Response:**
```json
{
  "status": "healthy",
  "environment": "local"
}
```

## Deploy to Staging

```bash
# 1. Create namespace
kubectl create namespace staging

# 2. Apply manifests
kubectl apply -f infra/staging/

# 3. Verify
kubectl get pods -n staging
```

## Deploy to Production

```bash
# 1. Create namespace
kubectl create namespace production

# 2. Set up secrets (use a real secret manager!)
# Edit infra/production/secret.yaml with your secret manager references

# 3. Apply manifests
kubectl apply -f infra/production/

# 4. Verify
kubectl get pods -n production
kubectl get hpa -n production
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment (local, staging, prod) | local |
| `POLICY_DB_URL` | Policy database connection string | sqlite:///policy.db |
| `CLAIMS_DB_URL` | Claims database connection string | sqlite:///claims.db |
| `DOCS_STORE_TYPE` | Document storage (mock, s3, sharepoint) | mock |
| `LLM_API_KEY` | API key for LLM provider | (empty) |
| `LLM_BYPASS` | Bypass LLM for testing (true/false) | false |

## How This Maps to a Real Insurance Company

| Our Component | Real-World Equivalent |
|---------------|----------------------|
| PolicyAgent | Policy Administration System (Guidewire, Duck Creek) |
| ClaimsAgent | Claims Management System (ClaimCenter, FNOL) |
| DocsAgent | Document Management System (S3, SharePoint, Alfresco) |
| LLM Builder | Enterprise LLM (Azure OpenAI, AWS Bedrock) |
| Kubernetes | Enterprise K8s (EKS, AKS, GKE, OpenShift) |

In a real implementation, each agent would connect to actual enterprise systems via APIs or database connections. The mock data we use for development would be replaced with real integrations.

## Course Content

This project includes a complete Udemy-style course in the `/course` directory:

1. **00-overview.md** - Course introduction and what you'll build
2. **01-architecture-and-flow.md** - System architecture and data flow
3. **02-backend-api-and-langgraph-setup.md** - FastAPI and orchestrator setup
4. **03-policy-claims-docs-agents.md** - Deep dive into the three agents
5. **04-local-environment-and-testing.md** - Local development and testing
6. **05-staging-environment-and-internal-testing.md** - Kubernetes staging deployment
7. **06-production-deployment-and-operations.md** - Production deployment and ops
8. **07-monitoring-logging-future-work.md** - Monitoring and future improvements

Each module includes:
- Clear explanations in simple English
- Code walkthroughs
- Mini quizzes
- Hands-on exercises

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

---

Built for DevOps, MLOps, and Backend engineers who want to learn practical AI system development.
