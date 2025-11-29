# Staging Environment and Internal Testing

## Lecture Outline

1. Why we need a staging environment
2. Kubernetes basics for staging
3. Deploying to staging
4. Testing with internal users
5. Health checks and monitoring basics

---

## Introduction

You've got the app running locally. Great! But before we push to production, we need a **staging environment**.

Staging is where we:
- Test with real-ish data
- Catch bugs before users see them
- Validate that deployments work
- Let internal testers try the system

Let's set it up!

---

## Why Staging Matters

Think of staging as a dress rehearsal before the big show.

| Local | Staging | Production |
|-------|---------|------------|
| Your laptop | Kubernetes cluster | Kubernetes cluster |
| Mock data | Test data | Real data |
| Just you | Internal testers | Real users |
| Catch obvious bugs | Catch integration bugs | Catch nothing (hopefully!) |

Staging catches issues like:
- Database connection problems
- Missing environment variables
- Container configuration errors
- Performance issues under load

---

## Kubernetes Basics

Kubernetes (K8s) is where we run staging and production. Here's what you need to know:

### Key Concepts

| Concept | What It Is | Our Usage |
|---------|------------|-----------|
| **Pod** | One or more containers running together | Our FastAPI app |
| **Deployment** | Manages pods, ensures correct count running | Runs 2 replicas |
| **Service** | Network access to pods | Internal load balancer |
| **ConfigMap** | Non-secret configuration | ENV, DB URLs |
| **Secret** | Sensitive configuration | API keys, passwords |
| **Namespace** | Logical grouping | `staging`, `production` |

### Our Staging Files

```
infra/staging/
├── configmap.yaml    # Non-secret config
├── secret.yaml       # Sensitive config (placeholder)
├── deployment.yaml   # Pod and replica configuration
└── service.yaml      # Network access
```

---

## Understanding the Manifests

Let's look at each file.

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: insurance-assistant-config
  namespace: staging
data:
  ENV: "staging"
  POLICY_DB_URL: "postgresql://policy-db-staging.internal:5432/policy"
  CLAIMS_DB_URL: "postgresql://claims-db-staging.internal:5432/claims"
  DOCS_STORE_TYPE: "mock"
  LLM_BYPASS: "true"
```

This contains configuration that's not secret. Anyone can see it.

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: insurance-assistant-secrets
  namespace: staging
type: Opaque
stringData:
  LLM_API_KEY: "sk-staging-api-key-change-me"
```

⚠️ **Important:** In the real world, don't commit actual secrets to git! Use:
- HashiCorp Vault
- AWS Secrets Manager
- External Secrets Operator

Our secret.yaml has placeholders you'll replace.

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insurance-assistant
  namespace: staging
spec:
  replicas: 2  # Run 2 copies for availability
  
  template:
    spec:
      containers:
        - name: app
          image: your-registry.io/insurance-assistant:staging
          
          envFrom:
            - configMapRef:
                name: insurance-assistant-config
          
          env:
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: insurance-assistant-secrets
                  key: LLM_API_KEY
          
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
          
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
```

Key points:
- 2 replicas for high availability
- Environment variables from ConfigMap and Secret
- Health probes so Kubernetes knows the app is healthy

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: insurance-assistant
  namespace: staging
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8000
```

This creates an internal DNS name: `insurance-assistant.staging.svc.cluster.local`

---

## Deploying to Staging

Here's how to deploy. You'll need access to a Kubernetes cluster.

### Step 1: Create the Namespace

```bash
kubectl create namespace staging
```

### Step 2: Build and Push the Image

```bash
# Build the Docker image
docker build -t your-registry.io/insurance-assistant:staging -f infra/local/Dockerfile .

# Push to your container registry
docker push your-registry.io/insurance-assistant:staging
```

### Step 3: Update the Image Name

Edit `infra/staging/deployment.yaml` and replace:
```yaml
image: your-registry.io/insurance-assistant:staging
```

With your actual registry URL.

### Step 4: Update Secrets

Edit `infra/staging/secret.yaml` with real values (or use a secret manager).

### Step 5: Apply the Manifests

```bash
kubectl apply -f infra/staging/configmap.yaml
kubectl apply -f infra/staging/secret.yaml
kubectl apply -f infra/staging/deployment.yaml
kubectl apply -f infra/staging/service.yaml
```

### Step 6: Verify

```bash
# Check pods are running
kubectl get pods -n staging

# Check the deployment
kubectl get deployment -n staging

# Check the service
kubectl get service -n staging
```

You should see:
```
NAME                    READY   STATUS    RESTARTS   AGE
insurance-assistant-xxx 1/1     Running   0          1m
insurance-assistant-yyy 1/1     Running   0          1m
```

---

## Testing in Staging

### Port Forward for Testing

To test from your laptop:

```bash
kubectl port-forward service/insurance-assistant 8080:80 -n staging
```

Now you can hit http://localhost:8080/chat

### Test the Health Endpoint

```bash
curl http://localhost:8080/health
```

Should return:
```json
{"status":"healthy","environment":"staging"}
```

### Test the Chat Endpoint

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "tester-1", "message": "Status of POL-1234"}'
```

---

## Internal Testing Checklist

Before promoting to production, internal testers should verify:

### Functional Tests
- [ ] Health endpoint returns 200
- [ ] Chat endpoint accepts requests
- [ ] Policy lookup works
- [ ] Claim lookup works
- [ ] Document status works
- [ ] Error messages are user-friendly

### Integration Tests
- [ ] Database connections work (when using real DBs)
- [ ] LLM responses work (when LLM_BYPASS=false)
- [ ] Document storage works (when using real S3/SharePoint)

### Performance Tests
- [ ] Response time is acceptable (<500ms)
- [ ] System handles concurrent requests
- [ ] Memory usage is stable

### Security Tests
- [ ] No sensitive data in logs
- [ ] API requires proper headers
- [ ] Invalid inputs are rejected

---

## Viewing Logs

To debug issues, check the logs:

```bash
# All pods
kubectl logs -l app=insurance-assistant -n staging

# Specific pod
kubectl logs insurance-assistant-xxx -n staging

# Follow logs in real-time
kubectl logs -f insurance-assistant-xxx -n staging
```

---

## Scaling

Need more capacity? Scale up:

```bash
kubectl scale deployment insurance-assistant --replicas=4 -n staging
```

Need less? Scale down:

```bash
kubectl scale deployment insurance-assistant --replicas=2 -n staging
```

---

## Updating the Application

To deploy a new version:

### Step 1: Build New Image

```bash
docker build -t your-registry.io/insurance-assistant:staging-v2 .
docker push your-registry.io/insurance-assistant:staging-v2
```

### Step 2: Update Deployment

```bash
kubectl set image deployment/insurance-assistant \
  app=your-registry.io/insurance-assistant:staging-v2 \
  -n staging
```

### Step 3: Watch Rollout

```bash
kubectl rollout status deployment/insurance-assistant -n staging
```

Kubernetes will:
1. Start new pods with new image
2. Wait for them to be healthy
3. Terminate old pods
4. Zero downtime!

---

## Mini Quiz

1. **Why do we need a staging environment?**
   - a) To impress the boss
   - b) To catch bugs before they reach production
   - c) Kubernetes requires it

2. **What does the ConfigMap contain?**
   - a) Secret credentials
   - b) Non-sensitive configuration values
   - c) Application code

3. **What do liveness and readiness probes do?**
   - a) Check if users are happy
   - b) Let Kubernetes know if the app is healthy
   - c) Send alerts to the team

4. **How do you view logs from a staging pod?**
   - a) kubectl logs <pod-name> -n staging
   - b) docker logs
   - c) cat /var/log/app.log

5. **What happens when you update a deployment in Kubernetes?**
   - a) The entire system goes down
   - b) Rolling update with zero downtime
   - c) You have to manually restart each pod

---

## Answers

1. **b** - To catch bugs before they reach production
2. **b** - Non-sensitive configuration values
3. **b** - Let Kubernetes know if the app is healthy
4. **a** - kubectl logs <pod-name> -n staging
5. **b** - Rolling update with zero downtime

---

## What's Next?

In the next module, we'll deploy to production. You'll learn about:
- Production-grade secrets management
- Horizontal Pod Autoscaling
- Production monitoring

Almost there! 🚀
