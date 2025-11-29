# Course Overview: Agentic AI for Insurance

## Lecture Outline

1. What this course is about
2. Who should take this course
3. Tools and technologies we'll use
4. How the environments fit together
5. What you'll build

---

## A Quick Story

Imagine you're a customer. You've had a hospital visit, and you want to know: "What's the status of my claim?"

You open a chatbot on your insurance company's website. You type your question. Within seconds, you get a friendly response like:

> "Your claim CLM-8899 is under review. We still need your hospital's final bill before we can finish processing it."

Behind that simple answer, a lot is happening:

- The system looked up your policy information
- It checked your claim status
- It verified which documents you've uploaded
- It identified what's missing
- An AI summarized all of this into a simple, human-friendly response

This course will teach you how to build exactly that system.

---

## What You'll Learn

In this course, you'll build a **real-world Agentic AI Insurance Assistant**. This isn't just theory—you'll write actual code that you could adapt for a real insurance company.

Here's what we'll cover:

1. **Backend API with FastAPI** - The API that your chatbot talks to
2. **LangGraph Orchestrator** - The "boss agent" that coordinates everything
3. **Helper Agents** - Specialized agents for policies, claims, and documents
4. **Business Rules** - Logic that checks conditions and flags issues
5. **LLM Integration** - Using AI to generate friendly responses
6. **Infrastructure** - Docker for local, Kubernetes for staging and production

---

## Who Is This For?

This course is designed for:

- **DevOps Engineers** who want to understand how AI applications work
- **MLOps Engineers** who want to deploy LLM-powered systems
- **Backend Engineers** who want to learn about agentic AI
- **Anyone** who wants a practical guide to building AI assistants

You should have:

- Basic Python knowledge
- Familiarity with REST APIs
- Some experience with Docker (helpful but not required)
- Curiosity about AI and LLMs

---

## Tools We'll Use

| Tool | Purpose |
|------|---------|
| **Python 3.11+** | Our programming language |
| **FastAPI** | Building the REST API |
| **LangGraph** | Orchestrating our agents |
| **Pydantic** | Data validation |
| **pytest** | Testing |
| **Docker** | Local development |
| **Kubernetes** | Staging and production deployment |
| **SQLite** | Mock databases for local dev |

Don't worry if you haven't used all of these before. We'll explain everything as we go.

---

## The Three Environments

We'll work with three environments:

### 1. Local Environment
- Runs on your laptop
- Uses mock data (no real databases)
- Uses Docker Compose
- Great for development and learning

### 2. Staging Environment
- Runs on Kubernetes
- Uses test databases
- For internal testing before production
- Catches bugs before real users see them

### 3. Production Environment
- The real thing
- Real databases, real users
- Proper security and monitoring
- Where the magic happens

Each environment uses the **same code** but different **configuration**. This is a key DevOps principle: build once, deploy anywhere.

---

## What You'll Build

By the end of this course, you'll have:

✅ A complete FastAPI backend with a `/chat` endpoint

✅ A LangGraph orchestrator that coordinates multiple agents

✅ Three helper agents (Policy, Claims, Documents)

✅ Business rules that check conditions and flag issues

✅ An LLM integration that generates friendly responses

✅ Docker configuration for local development

✅ Kubernetes manifests for staging and production

✅ Tests that verify everything works

---

## Course Structure

Here's how the course is organized:

| Module | Topic |
|--------|-------|
| 01 | Architecture and Flow |
| 02 | Backend API and LangGraph Setup |
| 03 | Policy, Claims, and Docs Agents |
| 04 | Local Environment and Testing |
| 05 | Staging Environment |
| 06 | Production Deployment |
| 07 | Monitoring, Logging, and Future Work |

Each module builds on the previous one. By the end, you'll have a complete, working system.

---

## Mini Quiz

Test your understanding before we dive in:

1. **What problem does our Insurance Assistant solve?**
   - a) Selling insurance policies
   - b) Answering customer questions about policies and claims
   - c) Processing payments

2. **What is the role of the LangGraph orchestrator?**
   - a) Store data in the database
   - b) Coordinate multiple agents to gather information
   - c) Send emails to customers

3. **Why do we have three environments (local, staging, prod)?**
   - a) To make things complicated
   - b) To test changes safely before they reach real users
   - c) Because Kubernetes requires it

4. **What does the LLM do in our system?**
   - a) Look up policy data
   - b) Generate friendly, human-readable responses
   - c) Store documents

5. **Is this course theory-only or hands-on?**
   - a) Theory-only
   - b) Hands-on with real code

---

## Answers

1. **b** - Answering customer questions about policies and claims
2. **b** - Coordinate multiple agents to gather information
3. **b** - To test changes safely before they reach real users
4. **b** - Generate friendly, human-readable responses
5. **b** - Hands-on with real code

---

## Ready?

In the next module, we'll dive into the architecture. You'll see exactly how data flows from the user's question to the final answer.

Let's get started! 🚀
