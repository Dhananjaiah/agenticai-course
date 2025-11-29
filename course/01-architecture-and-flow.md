# Architecture and Flow

## Lecture Outline

1. High-level architecture overview
2. The flow diagram
3. Step-by-step walkthrough
4. How components communicate
5. Why we chose this design

---

## The Big Picture

Let's start with what happens when a user asks a question.

The user types into a chatbot:
> "What is the status of my claim CLM-8899?"

And they get back:
> "Your claim CLM-8899 is under review. We still need the hospital's final bill."

Between that question and answer, here's what happens:

```
User → Chatbot → Backend API → Orchestrator → Agents → Data Sources → LLM → Response
```

Let's break down each piece.

---

## Architecture Diagram

Here's the complete flow:

```
┌─────────────┐
│   Chatbot   │  User types their question here
└──────┬──────┘
       │ POST /chat
       ▼
┌─────────────┐
│  FastAPI    │  Our backend receives the request
│   /chat     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator               │
│                     (The "Boss Agent")                  │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Policy    │  │   Claims    │  │    Docs     │     │
│  │   Agent     │  │   Agent     │  │   Agent     │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Policy   │    │ Claims   │    │  Docs    │
    │   DB     │    │   DB     │    │  Store   │
    └──────────┘    └──────────┘    └──────────┘

                    Results merged
                         │
                         ▼
              ┌─────────────────────┐
              │   Business Rules    │
              │   (Check & Flag)    │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │    LLM Builder      │
              │ (Generate Response) │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   Final Response    │
              │  (Back to Chatbot)  │
              └─────────────────────┘
```

---

## Step-by-Step Walkthrough

Let's follow a real request through the system.

### Step 1: User Sends a Message

The user types in the chatbot:
> "What is the status of my claim CLM-8899?"

The chatbot sends this to our API:

```json
{
  "userId": "user-123",
  "message": "What is the status of my claim CLM-8899?"
}
```

### Step 2: FastAPI Receives the Request

Our `/chat` endpoint receives the JSON. It logs the request and passes it to the orchestrator.

### Step 3: Message Parsing

The orchestrator first **parses the message**. It looks for:
- Policy IDs (like `POL-1234`)
- Claim IDs (like `CLM-8899`)

In our example, it finds: `CLM-8899`

### Step 4: Calling the Agents

Based on what it found, the orchestrator decides which agents to call:

- **Claim found?** → Call ClaimsAgent
- **Policy found?** → Call PolicyAgent
- **Need docs?** → Call DocsAgent

For `CLM-8899`, it:
1. Calls **ClaimsAgent** to get claim details
2. From the claim, gets the policy ID (`POL-1234`)
3. Calls **PolicyAgent** to get policy details
4. Calls **DocsAgent** to check document status

### Step 5: Gathering Data

Each agent returns structured data:

**ClaimsAgent returns:**
```json
{
  "claimId": "CLM-8899",
  "policyId": "POL-1234",
  "status": "UNDER_REVIEW",
  "claimType": "Hospitalization",
  "requestedAmount": 75000
}
```

**PolicyAgent returns:**
```json
{
  "policyId": "POL-1234",
  "customerName": "John Smith",
  "status": "ACTIVE"
}
```

**DocsAgent returns:**
```json
{
  "requiredDocs": ["KYC", "Hospital Final Bill", "Discharge Summary"],
  "uploadedDocs": ["KYC", "Discharge Summary"],
  "missingDocs": ["Hospital Final Bill"]
}
```

### Step 6: Business Rules

The business rules layer checks conditions:

- Is the policy active? ✅ Yes
- Is the claim under review? ✅ Yes
- Are there missing documents? ✅ Yes - Hospital Final Bill

It sets flags:
```json
{
  "claim_under_review": true,
  "pending_documents": true,
  "missing_docs_list": ["Hospital Final Bill"]
}
```

### Step 7: LLM Generates Response

All this data goes to the LLM. The LLM is given:
- Policy info
- Claim info
- Document status
- Flags

It generates a friendly response:
> "Your claim CLM-8899 is under review. We still need the hospital's final bill before we can finish processing it."

### Step 8: Response Sent Back

The API returns:

```json
{
  "answer": "Your claim CLM-8899 is under review. We still need the hospital's final bill before we can finish processing it.",
  "data": {
    "policy": { ... },
    "claim": { ... },
    "documents": { ... }
  }
}
```

The chatbot displays the answer to the user.

---

## Why This Design?

You might wonder: "Why not just have one big function that does everything?"

Great question! Here's why we split things up:

### 1. **Separation of Concerns**
Each agent has one job. PolicyAgent knows about policies. ClaimsAgent knows about claims. This makes the code easier to understand and maintain.

### 2. **Testability**
We can test each agent independently. If the PolicyAgent has a bug, we can find and fix it without touching other code.

### 3. **Flexibility**
What if the claims database moves to a new server? We only update ClaimsAgent. Nothing else changes.

### 4. **Real-World Mapping**
In real insurance companies, policies, claims, and documents are often in different systems. Our architecture mirrors this reality.

### 5. **Scalability**
If claims queries are slow, we can scale just the ClaimsAgent. We don't need to scale everything.

---

## Data Flow Summary

| Step | Component | What Happens |
|------|-----------|--------------|
| 1 | Chatbot | User sends message |
| 2 | FastAPI | Receives and validates request |
| 3 | Orchestrator | Parses message, extracts IDs |
| 4 | Agents | Fetch data from respective sources |
| 5 | Business Rules | Check conditions, set flags |
| 6 | LLM Builder | Generate friendly response |
| 7 | FastAPI | Return response to chatbot |
| 8 | Chatbot | Display to user |

---

## Mini Quiz

1. **What is the first thing the orchestrator does with the user's message?**
   - a) Send it to the LLM
   - b) Parse it to extract policy/claim IDs
   - c) Store it in the database

2. **If a user asks about claim CLM-8899, which agents might be called?**
   - a) Only ClaimsAgent
   - b) ClaimsAgent, then PolicyAgent (from claim's policyId), then DocsAgent
   - c) Only DocsAgent

3. **What does the Business Rules layer do?**
   - a) Generate the final response
   - b) Check conditions and set flags
   - c) Store data in the database

4. **Why do we separate the code into multiple agents?**
   - a) To make it more complicated
   - b) For testability, flexibility, and real-world mapping
   - c) Because Python requires it

5. **What format does each agent return data in?**
   - a) Plain text
   - b) Structured JSON
   - c) XML

---

## Answers

1. **b** - Parse it to extract policy/claim IDs
2. **b** - ClaimsAgent, then PolicyAgent (from claim's policyId), then DocsAgent
3. **b** - Check conditions and set flags
4. **b** - For testability, flexibility, and real-world mapping
5. **b** - Structured JSON

---

## What's Next?

In the next module, we'll look at the actual code for the FastAPI app and how we wire up the LangGraph orchestrator. You'll see how all these pieces connect in Python.

See you there! 🎯
