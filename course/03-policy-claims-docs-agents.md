# Policy, Claims, and Docs Agents

## Lecture Outline

1. What agents are and why we have three
2. PolicyAgent: responsibilities and data shape
3. ClaimsAgent: responsibilities and data shape
4. DocsAgent: responsibilities and data shape
5. How this mirrors real insurance systems
6. A realistic example

---

## What Are Agents?

In our system, an "agent" is a specialized component that knows how to do one thing really well.

- **PolicyAgent** → Knows about insurance policies
- **ClaimsAgent** → Knows about insurance claims
- **DocsAgent** → Knows about uploaded documents

Each agent:
- Has a single responsibility
- Returns structured data in a consistent format
- Can be tested independently
- Mirrors a real-world system in an insurance company

---

## Why Three Agents?

In a real insurance company, policies, claims, and documents are often in **different systems**:

- **Policy Core System** - Where policies are created and managed
- **Claims Management System** - Where claims are processed
- **Document Management System** - S3, SharePoint, or similar

Our three agents mirror this real-world separation. If you work at an insurance company, you'll probably have similar systems.

---

## PolicyAgent

### What It Does

The PolicyAgent fetches policy information. When you ask "What's the status of POL-1234?", this agent gets the answer.

### Data Shape

Here's what the PolicyAgent returns:

```json
{
  "policyId": "POL-1234",
  "customerName": "John Smith",
  "productType": "Health",
  "startDate": "2024-01-01",
  "endDate": "2024-12-31",
  "status": "ACTIVE",
  "sumInsured": 500000.0
}
```

Let me explain each field:

| Field | Description | Example |
|-------|-------------|---------|
| `policyId` | Unique identifier | "POL-1234" |
| `customerName` | Who owns the policy | "John Smith" |
| `productType` | Type of insurance | "Health", "Auto", "Life" |
| `startDate` | When coverage started | "2024-01-01" |
| `endDate` | When coverage ends | "2024-12-31" |
| `status` | Current status | "ACTIVE", "EXPIRED", "CANCELLED" |
| `sumInsured` | Coverage amount | 500000.0 |

### How It Works

```python
class PolicyAgent:
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
    
    def get_policy(self, policy_id: str):
        if self.use_mock:
            # Return from mock data
            return MOCK_POLICIES.get(policy_id)
        else:
            # In production: query real database
            pass
```

For local development, we use mock data. In production, this would connect to a real database.

---

## ClaimsAgent

### What It Does

The ClaimsAgent fetches claim information. When someone asks about CLM-8899, this agent knows the answer.

### Data Shape

Here's what the ClaimsAgent returns:

```json
{
  "claimId": "CLM-8899",
  "policyId": "POL-1234",
  "status": "UNDER_REVIEW",
  "claimType": "Hospitalization",
  "requestedAmount": 75000.0,
  "approvedAmount": null,
  "lastUpdated": "2024-03-15T10:30:00Z",
  "reasonIfRejected": null
}
```

Let me explain each field:

| Field | Description | Example |
|-------|-------------|---------|
| `claimId` | Unique identifier | "CLM-8899" |
| `policyId` | Which policy this claim belongs to | "POL-1234" |
| `status` | Current status | "OPEN", "UNDER_REVIEW", "APPROVED", "REJECTED" |
| `claimType` | What kind of claim | "Hospitalization", "Accident", "Outpatient" |
| `requestedAmount` | What the customer asked for | 75000.0 |
| `approvedAmount` | What was approved (if decided) | 45000.0 or null |
| `lastUpdated` | When it was last updated | ISO timestamp |
| `reasonIfRejected` | Why it was rejected (if applicable) | "Policy doesn't cover..." or null |

### Claim Statuses

Here's what each status means:

- **OPEN** - Claim just filed, not yet reviewed
- **UNDER_REVIEW** - Currently being processed
- **APPROVED** - Claim accepted, amount approved
- **REJECTED** - Claim denied with a reason

---

## DocsAgent

### What It Does

The DocsAgent checks document status. Insurance claims require documents (ID proof, hospital bills, etc.). This agent knows what's needed and what's been uploaded.

### Data Shape

Here's what the DocsAgent returns:

```json
{
  "requiredDocs": ["KYC", "Hospital Final Bill", "Discharge Summary", "Doctor Prescription"],
  "uploadedDocs": ["KYC", "Discharge Summary"],
  "missingDocs": ["Hospital Final Bill", "Doctor Prescription"]
}
```

| Field | Description |
|-------|-------------|
| `requiredDocs` | All documents needed for this claim type |
| `uploadedDocs` | What the customer has already uploaded |
| `missingDocs` | What's still needed (calculated automatically) |

### Required Documents by Claim Type

Different claim types need different documents:

| Claim Type | Required Documents |
|------------|-------------------|
| Hospitalization | KYC, Hospital Final Bill, Discharge Summary, Doctor Prescription |
| Accident | KYC, Police Report, Hospital Records, Photos of Damage |
| Outpatient | KYC, Doctor Prescription, Medical Bills |
| Theft | KYC, Police Report, Proof of Ownership, Photos |

---

## How This Mirrors Real Insurance Systems

Let me show you how our agents map to real systems:

```
Our System                    Real Insurance Company
─────────────────────         ──────────────────────────────
PolicyAgent           ←→      Policy Administration System
                              (e.g., Guidewire PolicyCenter)

ClaimsAgent           ←→      Claims Management System
                              (e.g., Guidewire ClaimCenter)

DocsAgent             ←→      Document Management System
                              (e.g., AWS S3, SharePoint, 
                               OpenText, Alfresco)
```

In a real implementation, each agent would:
- Connect to the appropriate system
- Handle authentication
- Transform data into our standard format
- Handle errors gracefully

---

## A Realistic Example

Let's walk through a complete example.

### Scenario
Customer John Smith has policy POL-1234 (Health insurance). He was hospitalized and filed claim CLM-8899 for $75,000. He uploaded some documents but forgot the hospital bill.

### What the User Asks
> "What's the status of my claim CLM-8899?"

### What Each Agent Returns

**ClaimsAgent returns:**
```json
{
  "claimId": "CLM-8899",
  "policyId": "POL-1234",
  "status": "UNDER_REVIEW",
  "claimType": "Hospitalization",
  "requestedAmount": 75000.0,
  "approvedAmount": null,
  "lastUpdated": "2024-03-15T10:30:00Z",
  "reasonIfRejected": null
}
```

**PolicyAgent returns:**
```json
{
  "policyId": "POL-1234",
  "customerName": "John Smith",
  "productType": "Health",
  "startDate": "2024-01-01",
  "endDate": "2024-12-31",
  "status": "ACTIVE",
  "sumInsured": 500000.0
}
```

**DocsAgent returns:**
```json
{
  "requiredDocs": ["KYC", "Hospital Final Bill", "Discharge Summary", "Doctor Prescription"],
  "uploadedDocs": ["KYC", "Discharge Summary"],
  "missingDocs": ["Hospital Final Bill", "Doctor Prescription"]
}
```

### Final Response
> "Your policy POL-1234 is active. Claim CLM-8899 is currently under review. We still need the Hospital Final Bill and Doctor Prescription before we can complete the review."

---

## Mock Data for Development

For local development, we use mock data stored in Python dictionaries:

```python
MOCK_POLICIES = {
    "POL-1234": PolicyData(
        policyId="POL-1234",
        customerName="John Smith",
        productType="Health",
        startDate="2024-01-01",
        endDate="2024-12-31",
        status="ACTIVE",
        sumInsured=500000.0
    ),
    # ... more mock policies
}
```

This lets you develop and test without needing real databases.

---

## Mini Quiz

1. **What is the main responsibility of the PolicyAgent?**
   - a) Process claims
   - b) Fetch policy information
   - c) Check uploaded documents

2. **What status does a claim have when it's been accepted?**
   - a) OPEN
   - b) UNDER_REVIEW
   - c) APPROVED

3. **What does the `missingDocs` field contain?**
   - a) All required documents
   - b) Documents that have been uploaded
   - c) Documents still needed

4. **Why do we have three separate agents instead of one?**
   - a) To make the code longer
   - b) To mirror real-world systems and enable independent testing
   - c) Python requires it

5. **If a claim has `approvedAmount: null`, what does that mean?**
   - a) The claim was rejected
   - b) The claim hasn't been decided yet
   - c) The customer didn't request any amount

---

## Answers

1. **b** - Fetch policy information
2. **c** - APPROVED
3. **c** - Documents still needed
4. **b** - To mirror real-world systems and enable independent testing
5. **b** - The claim hasn't been decided yet

---

## What's Next?

In the next module, we'll set up the local environment and run everything together. You'll see the complete system in action!

Let's keep building! 🔧
