# Local Environment and Testing

## Lecture Outline

1. Setting up your local environment
2. Running with uvicorn directly
3. Running with Docker Compose
4. Understanding mock data
5. Testing the /chat endpoint
6. Hands-on lab

---

## Introduction

In this module, you'll set up the project on your local machine and test it. By the end, you'll have the Insurance Assistant running and responding to your questions.

Let's get started!

---

## Prerequisites

Before we begin, make sure you have:

- **Python 3.11+** installed
- **Docker** (optional, for Docker Compose)
- **curl** or **Postman** for testing APIs
- A terminal/command line

---

## Option 1: Running with Python Directly

The simplest way to run locally is with Python and uvicorn.

### Step 1: Clone and Navigate

```bash
# Navigate to the project
cd agenticai-course
```

### Step 2: Create a Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Mac/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Step 4: Set Environment Variables

```bash
export ENV=local
export POLICY_DB_URL=sqlite:///policy.db
export CLAIMS_DB_URL=sqlite:///claims.db
export DOCS_STORE_TYPE=mock
export LLM_API_KEY=""
export LLM_BYPASS=true
```

### Step 5: Run the Server

```bash
uvicorn backend.main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application started in local environment
```

🎉 The server is running!

---

## Option 2: Running with Docker Compose

If you prefer Docker, we have that ready too.

### Step 1: Navigate to infra/local

```bash
cd infra/local
```

### Step 2: Build and Run

```bash
docker-compose up --build
```

This will:
1. Build the Docker image
2. Start the container
3. Map port 8000 to your machine

### Step 3: Check It's Running

```bash
curl http://localhost:8000/health
```

You should see:
```json
{"status":"healthy","environment":"local"}
```

---

## Understanding Mock Data

In local mode, we don't connect to real databases. Instead, we use mock data defined in Python.

### Mock Policies

We have three test policies:

| Policy ID | Customer | Type | Status |
|-----------|----------|------|--------|
| POL-1234 | John Smith | Health | ACTIVE |
| POL-5678 | Jane Doe | Auto | ACTIVE |
| POL-9999 | Bob Wilson | Life | EXPIRED |

### Mock Claims

We have four test claims:

| Claim ID | Policy | Status | Type |
|----------|--------|--------|------|
| CLM-8899 | POL-1234 | UNDER_REVIEW | Hospitalization |
| CLM-1001 | POL-1234 | APPROVED | Hospitalization |
| CLM-2002 | POL-5678 | REJECTED | Accident |
| CLM-3003 | POL-1234 | OPEN | Outpatient |

### Mock Documents

For claim CLM-8899:
- Required: KYC, Hospital Final Bill, Discharge Summary, Doctor Prescription
- Uploaded: KYC, Discharge Summary
- Missing: Hospital Final Bill, Doctor Prescription

---

## Testing the /chat Endpoint

Now let's test with real requests!

### Test 1: Ask About a Policy

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "What is the status of POL-1234?"}'
```

**Expected Response:**
```json
{
  "answer": "Your policy POL-1234 is active.",
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
    "claim": null,
    "documents": {
      "requiredDocs": ["KYC", "Policy Application Form", "ID Proof"],
      "uploadedDocs": ["KYC", "Policy Application Form", "ID Proof"],
      "missingDocs": []
    }
  }
}
```

### Test 2: Ask About a Claim

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "Status of CLM-8899"}'
```

**Expected Response:**
```json
{
  "answer": "Your policy POL-1234 is active. Claim CLM-8899 is currently under review. We still need the following documents: Hospital Final Bill, Doctor Prescription.",
  "data": {
    "policy": { ... },
    "claim": {
      "claimId": "CLM-8899",
      "policyId": "POL-1234",
      "status": "UNDER_REVIEW",
      ...
    },
    "documents": {
      "missingDocs": ["Hospital Final Bill", "Doctor Prescription"]
    }
  }
}
```

### Test 3: Ask About a Non-Existent Policy

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "Check POL-0000"}'
```

**Expected Response:**
```json
{
  "answer": "I couldn't find the policy you're looking for. Please check the policy number and try again.",
  "data": {
    "policy": null,
    "claim": null,
    "documents": null
  }
}
```

### Test 4: Ask About an Approved Claim

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "What about CLM-1001?"}'
```

**Expected Response:**
The answer should mention that the claim was approved for $45,000.

---

## Using the Interactive Docs

FastAPI provides interactive documentation. Open your browser to:

**http://localhost:8000/docs**

You'll see:
- All available endpoints
- Request/response schemas
- A "Try it out" button

This is great for exploring the API without writing curl commands.

---

## Running Tests

We have automated tests. Run them with:

```bash
# From the project root
pytest backend/tests/ -v
```

You should see all tests passing:

```
backend/tests/test_parser.py::TestMessageParser::test_extract_policy_id_basic PASSED
backend/tests/test_parser.py::TestMessageParser::test_extract_claim_id_basic PASSED
backend/tests/test_agents.py::TestPolicyAgent::test_get_policy_found PASSED
...
```

### What the Tests Cover

| Test File | What It Tests |
|-----------|--------------|
| `test_parser.py` | Message parsing, ID extraction |
| `test_agents.py` | Agent data fetching |
| `test_orchestrator.py` | Business rules, data merging |
| `test_api.py` | FastAPI endpoints |

---

## Hands-On Lab

Now it's your turn! Complete these exercises:

### Exercise 1: Test All Mock Policies

Query each of the three policies:
- POL-1234
- POL-5678
- POL-9999

Note the differences in their responses.

### Exercise 2: Test All Mock Claims

Query each of the four claims:
- CLM-8899 (under review, missing docs)
- CLM-1001 (approved)
- CLM-2002 (rejected)
- CLM-3003 (open)

Notice how the responses differ based on status.

### Exercise 3: Test with Both IDs

Send a message with both policy and claim:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "user-123", "message": "Check claim CLM-8899 on policy POL-1234"}'
```

What data do you get back?

### Exercise 4: Try the Health Endpoint

```bash
curl http://localhost:8000/health
```

What information does it return?

---

## Troubleshooting

### "Module not found" Error

Make sure you:
1. Activated your virtual environment
2. Installed requirements with `pip install -r backend/requirements.txt`
3. Are running from the project root directory

### Port Already in Use

If port 8000 is busy:

```bash
uvicorn backend.main:app --reload --port 8001
```

### Docker Build Fails

Make sure Docker Desktop is running, then try:

```bash
docker-compose down
docker-compose up --build
```

---

## Mini Quiz

1. **What command starts the server for local development?**
   - a) python main.py
   - b) uvicorn backend.main:app --reload
   - c) npm start

2. **What does `LLM_BYPASS=true` do?**
   - a) Calls the real LLM
   - b) Returns mock responses without calling the LLM
   - c) Disables the chat endpoint

3. **How many test policies do we have in the mock data?**
   - a) 1
   - b) 3
   - c) 10

4. **Where can you find the interactive API documentation?**
   - a) http://localhost:8000/
   - b) http://localhost:8000/docs
   - c) http://localhost:8000/api

5. **What command runs the automated tests?**
   - a) npm test
   - b) pytest backend/tests/ -v
   - c) python test.py

---

## Answers

1. **b** - uvicorn backend.main:app --reload
2. **b** - Returns mock responses without calling the LLM
3. **b** - 3 (POL-1234, POL-5678, POL-9999)
4. **b** - http://localhost:8000/docs
5. **b** - pytest backend/tests/ -v

---

## What's Next?

In the next module, we'll deploy to a staging environment using Kubernetes. You'll learn how to take this local setup and run it in a cluster.

Great job getting this far! 🎉
