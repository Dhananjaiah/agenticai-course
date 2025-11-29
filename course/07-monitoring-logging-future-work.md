# Monitoring, Logging, and Future Work

## Lecture Outline

1. Logging best practices
2. Monitoring basics
3. Error tracking
4. Future improvements
5. Course recap

---

## Introduction

Congratulations! You've built and deployed an Agentic AI Insurance Assistant. But the work doesn't stop at deployment.

In this final module, you'll learn about:
- Keeping track of what's happening in your system
- Catching problems before users complain
- Ideas for making the system even better

Let's wrap things up!

---

## Logging Best Practices

Good logging helps you understand what's happening and debug problems.

### What to Log

| What | Why | Example |
|------|-----|---------|
| Request received | Know what users are asking | "Chat request from user user-123" |
| Agent calls | Track which agents are used | "PolicyAgent: Looking up POL-1234" |
| Results | Know what was found | "Found policy, status: ACTIVE" |
| Errors | Debug problems | "Error fetching claim: DB timeout" |
| Response sent | Confirm completion | "Response sent to user-123" |

### What NOT to Log

- ❌ Full customer data (privacy!)
- ❌ API keys or passwords
- ❌ Detailed personal information
- ❌ Credit card numbers

### Log Levels

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed debugging info")    # Development only
logger.info("Normal operation")            # Standard operations
logger.warning("Something unusual")        # Potential problems
logger.error("Something went wrong")       # Actual errors
logger.critical("System is down")          # Major failures
```

In production, set `LOG_LEVEL=WARNING` to reduce noise.

### Structured Logging

Instead of plain text, use structured logs:

```python
# Plain text (harder to search)
logger.info(f"User {user_id} asked about claim {claim_id}")

# Structured (easier to search and analyze)
logger.info("claim_query", extra={
    "user_id": user_id,
    "claim_id": claim_id,
    "response_time_ms": 150
})
```

Tools like Elasticsearch, Datadog, and Splunk can parse structured logs.

---

## Monitoring Basics

Monitoring tells you if your system is healthy and performing well.

### Key Metrics to Track

| Metric | What It Tells You | Alert If |
|--------|------------------|----------|
| Request rate | How busy the system is | Sudden drop (outage?) |
| Error rate | How many requests fail | > 1% errors |
| Response time | How fast responses are | p95 > 500ms |
| CPU usage | System load | > 80% sustained |
| Memory usage | Memory consumption | > 85% |
| Pod count | How many replicas | < minimum |

### Prometheus + Grafana

A common setup:
1. **Prometheus** scrapes metrics from your app
2. **Grafana** displays them in dashboards

To expose metrics from FastAPI:

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

### Example Dashboard Panels

- Request rate over time
- Error rate by endpoint
- Response time percentiles (p50, p95, p99)
- Active pods count
- CPU and memory usage

---

## Error Tracking

When errors happen, you need to know about them.

### Options

| Tool | Good For |
|------|----------|
| **Sentry** | Python error tracking, stack traces |
| **Datadog** | Full observability (logs, metrics, traces) |
| **PagerDuty** | Alerting and on-call management |
| **Slack** | Team notifications |

### Basic Error Tracking with Sentry

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    environment=settings.env,
)
```

Now unhandled exceptions are automatically reported to Sentry with full context.

### Alerting

Set up alerts for critical issues:

```yaml
# Example Prometheus alert
groups:
  - name: insurance-assistant
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on insurance-assistant"
```

---

## Future Improvements

Here are ideas to make the system even better:

### 1. Authentication & Authorization

Currently, anyone can call the API. Add:
- User authentication (JWT tokens)
- Authorization (user can only see their own policies)
- Rate limiting per user

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/chat")
async def chat(request: ChatRequest, token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    # ... rest of the code
```

### 2. Real Database Integration

Replace mock data with real databases:
- PostgreSQL for policies and claims
- Redis for caching
- S3 or SharePoint for documents

### 3. Real LLM Integration

Connect to a real LLM:

```python
import openai

def call_llm(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content
```

### 4. More Intents

Expand what the assistant can handle:
- Premium payment status
- Policy renewal reminders
- Coverage questions
- Filing new claims
- Updating contact information

### 5. Conversation History

Remember previous messages in a conversation:

```python
class ChatRequest(BaseModel):
    userId: str
    message: str
    conversationId: Optional[str] = None  # Track conversation
```

Store conversation history in Redis or a database.

### 6. Multi-Language Support

Support customers in different languages:
- Detect language from message
- Translate internal data to user's language
- Use multilingual LLM

### 7. Analytics

Track:
- Most common questions
- Average response time
- User satisfaction
- Common failure points

---

## How This Maps to a Real Insurance Company

Let me explain how our project would fit into a real insurance company:

```
Our Project                    Real World
─────────────────────         ────────────────────────────────────

FastAPI Backend          →    Part of the customer portal backend
                              (alongside other APIs)

PolicyAgent              →    Integration with Policy Admin System
                              (Guidewire, Duck Creek, custom)

ClaimsAgent              →    Integration with Claims System
                              (ClaimCenter, FNOL systems)

DocsAgent                →    Integration with ECM/DMS
                              (SharePoint, Alfresco, S3)

LLM Builder              →    Azure OpenAI / AWS Bedrock
                              (enterprise LLM with compliance)

Kubernetes               →    Enterprise Kubernetes (EKS, AKS, GKE)
                              or on-premises (OpenShift)

Monitoring               →    Enterprise observability
                              (Dynatrace, Datadog, Splunk)
```

The patterns you've learned apply directly to enterprise insurance systems.

---

## Course Recap

You've come a long way! Here's what you've learned:

### Module 0: Overview
- What the project does
- Who it's for
- The three environments

### Module 1: Architecture
- The flow from user to response
- Why we have multiple agents
- How data flows through the system

### Module 2: Backend API
- FastAPI for the /chat endpoint
- Pydantic for validation
- Environment configuration

### Module 3: Agents
- PolicyAgent for policy data
- ClaimsAgent for claim data
- DocsAgent for document status

### Module 4: Local Environment
- Running with uvicorn
- Running with Docker
- Testing the endpoints

### Module 5: Staging
- Kubernetes basics
- Deploying to staging
- Internal testing

### Module 6: Production
- Production deployment
- Secrets management
- Debugging production issues

### Module 7: Operations (this module)
- Logging best practices
- Monitoring basics
- Future improvements

---

## What You Can Do Now

After this course, you can:

✅ Build AI-powered backend APIs with FastAPI

✅ Design multi-agent systems for complex workflows

✅ Write clean, testable code with proper separation of concerns

✅ Deploy applications to Kubernetes

✅ Manage configuration across environments

✅ Debug and operate production systems

✅ Plan future improvements and scaling

---

## Mini Quiz (Final!)

1. **What log level should you use in production to reduce noise?**
   - a) DEBUG
   - b) INFO
   - c) WARNING

2. **What tool combination is common for metrics and dashboards?**
   - a) Prometheus + Grafana
   - b) Word + Excel
   - c) Notepad + Calculator

3. **What should you add to restrict API access to authenticated users?**
   - a) More replicas
   - b) Authentication (JWT tokens, OAuth)
   - c) Faster CPU

4. **What's a good next step to handle more user intents?**
   - a) Delete existing code
   - b) Add more agents or extend orchestrator logic
   - c) Use a bigger database

5. **What's the main takeaway from this course?**
   - a) AI is complicated
   - b) You can build real-world AI systems with clear architecture
   - c) Kubernetes is scary

---

## Answers

1. **c** - WARNING
2. **a** - Prometheus + Grafana
3. **b** - Authentication (JWT tokens, OAuth)
4. **b** - Add more agents or extend orchestrator logic
5. **b** - You can build real-world AI systems with clear architecture

---

## Thank You!

You've completed the **Agentic AI Insurance Assistant** course!

You now have:
- A complete, working project
- Understanding of the architecture
- Skills to deploy and operate AI systems
- Ideas for future improvements

Take this knowledge and build something amazing. Whether it's for insurance, healthcare, finance, or any other domain, the patterns you've learned here apply.

**Good luck, and happy building!** 🎉🚀

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

*Course created for DevOps, MLOps, and Backend engineers who want to build practical AI systems.*
