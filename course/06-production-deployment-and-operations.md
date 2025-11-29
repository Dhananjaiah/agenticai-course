# Production Deployment and Operations

## Lecture Outline

1. Production vs staging: what's different
2. Secrets management for production
3. Deploying to production
4. Operational considerations
5. Debugging production issues

---

## Introduction

Production is where real users interact with your system. Everything we've learned comes together here.

In this module, you'll learn:
- How to deploy safely to production
- How to manage secrets properly
- How to operate and debug the system

Let's make it production-ready!

---

## Production vs Staging: What's Different?

| Aspect | Staging | Production |
|--------|---------|------------|
| Data | Test data | Real customer data |
| Users | Internal testers | Real customers |
| Replicas | 2 | 3+ (with autoscaling) |
| Secrets | Test credentials | Real credentials |
| Monitoring | Basic | Comprehensive |
| Availability | Can have downtime | Must be highly available |
| Security | Important | Critical |

The code is the same. The configuration and operational rigor are different.

---

## Production Manifests

Our production files are in `infra/production/`:

```
infra/production/
├── configmap.yaml    # Production configuration
├── secret.yaml       # Secret references (placeholder)
├── deployment.yaml   # Production deployment + PDB
└── service.yaml      # Service + Ingress + HPA
```

Let's look at what's different.

### ConfigMap Changes

```yaml
data:
  ENV: "prod"
  DOCS_STORE_TYPE: "s3"        # Real document storage
  LLM_BYPASS: "false"          # Use real LLM
  LOG_LEVEL: "WARNING"         # Less verbose logging
```

### Deployment Changes

```yaml
spec:
  replicas: 3                   # More replicas
  
  template:
    spec:
      containers:
        - resources:
            requests:
              cpu: "250m"       # More resources
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
          
          securityContext:
            runAsNonRoot: true  # Stricter security
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
```

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: insurance-assistant-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: insurance-assistant
```

This ensures at least 2 pods are always running, even during updates.

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          averageUtilization: 70
```

Automatically scales pods based on CPU usage.

---

## Secrets Management

**Never commit real secrets to git!**

For production, use a proper secrets manager:

### Option 1: External Secrets Operator + Vault

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: insurance-assistant-secrets
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: insurance-assistant-secrets
  data:
    - secretKey: LLM_API_KEY
      remoteRef:
        key: secret/data/production/insurance-assistant
        property: llm_api_key
```

### Option 2: AWS Secrets Manager

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  data:
    - secretKey: LLM_API_KEY
      remoteRef:
        key: production/insurance-assistant
        property: llm_api_key
```

### Option 3: Sealed Secrets

```bash
# Encrypt the secret
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml

# The sealed secret can be committed to git
# It can only be decrypted by the cluster
```

**Key principle:** The actual secret values should never be in your git repository.

---

## Deploying to Production

### Pre-Deployment Checklist

Before deploying:
- [ ] All tests pass
- [ ] Staging testing complete
- [ ] Secrets configured in secret manager
- [ ] Team notified of deployment
- [ ] Rollback plan ready

### Deployment Steps

```bash
# 1. Create namespace (if not exists)
kubectl create namespace production

# 2. Apply configurations
kubectl apply -f infra/production/configmap.yaml
kubectl apply -f infra/production/deployment.yaml
kubectl apply -f infra/production/service.yaml

# 3. Verify deployment
kubectl rollout status deployment/insurance-assistant -n production

# 4. Check pods
kubectl get pods -n production
```

### Verify It's Working

```bash
# Port forward for quick test
kubectl port-forward service/insurance-assistant 8080:80 -n production

# Test health
curl http://localhost:8080/health

# Test chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "test", "message": "Status of POL-1234"}'
```

---

## Rollback Strategy

If something goes wrong, roll back quickly:

```bash
# See rollout history
kubectl rollout history deployment/insurance-assistant -n production

# Roll back to previous version
kubectl rollout undo deployment/insurance-assistant -n production

# Roll back to specific revision
kubectl rollout undo deployment/insurance-assistant --to-revision=2 -n production
```

---

## Operational Tasks

### Viewing Logs

```bash
# All pods
kubectl logs -l app=insurance-assistant -n production

# Follow logs
kubectl logs -f -l app=insurance-assistant -n production

# Logs from last hour
kubectl logs --since=1h -l app=insurance-assistant -n production
```

### Checking Resource Usage

```bash
# Pod resource usage
kubectl top pods -n production

# Node resource usage
kubectl top nodes
```

### Scaling

```bash
# Manual scale
kubectl scale deployment insurance-assistant --replicas=5 -n production

# Or let the HPA handle it automatically
```

### Restarting Pods

```bash
# Rolling restart (no downtime)
kubectl rollout restart deployment/insurance-assistant -n production
```

---

## Debugging Production Issues

When something goes wrong, here's how to investigate.

### Step 1: Check Pod Status

```bash
kubectl get pods -n production

# Look for:
# - Pods not Running
# - High restart counts
# - Pending pods
```

### Step 2: Describe Problem Pods

```bash
kubectl describe pod <pod-name> -n production

# Look for:
# - Events at the bottom
# - Container status
# - Resource issues
```

### Step 3: Check Logs

```bash
kubectl logs <pod-name> -n production

# For previous crashed container
kubectl logs <pod-name> --previous -n production
```

### Step 4: Check Application Health

```bash
# Exec into a pod
kubectl exec -it <pod-name> -n production -- /bin/sh

# Inside the pod, check health
curl localhost:8000/health
```

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| OOMKilled | Pod restarts, OOMKilled in status | Increase memory limit |
| CrashLoopBackOff | Pod keeps restarting | Check logs for startup error |
| ImagePullBackOff | Pod stuck in pending | Check image name and registry access |
| Unhealthy | Readiness probe failing | Check app startup and health endpoint |
| DB connection error | Errors in logs | Check DB URL and credentials |

---

## Example: Debugging a Failed Chat Request

Support reports: "A customer can't get their claim status."

### Investigation Steps

1. **Get the user's request ID** (if you have one in logs)

2. **Search the logs:**
```bash
kubectl logs -l app=insurance-assistant -n production | grep "user-id-here"
```

3. **Look for errors:**
```bash
kubectl logs -l app=insurance-assistant -n production | grep -i error
```

4. **Check if it's a specific claim:**
```bash
# Maybe the claim doesn't exist in the database
# Or there's a database connectivity issue
```

5. **Test the same request:**
```bash
curl -X POST https://insurance-assistant.yourdomain.com/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "debug", "message": "Status of <claim-id>"}'
```

6. **Report findings to the team**

---

## Mini Quiz

1. **What should you NEVER do with production secrets?**
   - a) Store them in a secret manager
   - b) Commit them to git
   - c) Rotate them regularly

2. **What does a Pod Disruption Budget do?**
   - a) Limits how much money you spend
   - b) Ensures minimum pods are always running
   - c) Prevents any changes to pods

3. **How do you roll back a failed deployment?**
   - a) Delete all pods manually
   - b) kubectl rollout undo deployment/<name>
   - c) Restart Kubernetes

4. **What's the first thing to check when a pod is crashing?**
   - a) The weather
   - b) The pod logs
   - c) The database size

5. **What does the Horizontal Pod Autoscaler do?**
   - a) Automatically scales pods based on metrics
   - b) Makes pods wider
   - c) Increases CPU speed

---

## Answers

1. **b** - Commit them to git
2. **b** - Ensures minimum pods are always running
3. **b** - kubectl rollout undo deployment/<name>
4. **b** - The pod logs
5. **a** - Automatically scales pods based on metrics

---

## What's Next?

In the final module, we'll cover monitoring, logging, and ideas for future improvements. You're almost done with the course!

Let's finish strong! 💪
