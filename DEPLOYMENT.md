# IBM Cloud Code Engine — Deployment Guide

## AI Startup Blueprint Generator

This guide deploys the app to **IBM Cloud Code Engine** — a fully managed serverless platform.

---

## Prerequisites

- IBM Cloud account ([cloud.ibm.com](https://cloud.ibm.com))
- IBM Cloud CLI installed: `curl -fsSL https://clis.cloud.ibm.com/install/linux | sh`
- Docker Desktop (for local build) OR IBM Cloud Container Registry
- `ibmcloud` CLI Code Engine plugin

---

## Step 1: Install CLI Plugins

```bash
ibmcloud plugin install code-engine
ibmcloud plugin install container-registry
ibmcloud login --apikey YOUR_IBM_CLOUD_API_KEY
```

---

## Step 2: Create a Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p knowledge_base exports logs

# Expose port
EXPOSE 5000

CMD ["python", "run.py"]
```

---

## Step 3: Build & Push to IBM Container Registry

```bash
# Login to IBM Container Registry
ibmcloud cr login
ibmcloud cr namespace-add blueprint-ai

# Build and tag
docker build -t us.icr.io/blueprint-ai/startup-blueprint:latest .

# Push
docker push us.icr.io/blueprint-ai/startup-blueprint:latest
```

---

## Step 4: Create Code Engine Project

```bash
# Create project
ibmcloud ce project create --name startup-blueprint-app

# Target the project
ibmcloud ce project select --name startup-blueprint-app
```

---

## Step 5: Create Secrets for Environment Variables

```bash
ibmcloud ce secret create --name blueprint-secrets \
  --from-literal IBM_WATSONX_API_KEY="your-api-key" \
  --from-literal IBM_WATSONX_PROJECT_ID="your-project-id" \
  --from-literal IBM_WATSONX_URL="https://us-south.ml.cloud.ibm.com" \
  --from-literal IBM_COS_API_KEY="your-cos-key" \
  --from-literal IBM_COS_INSTANCE_CRN="crn:v1:..." \
  --from-literal IBM_COS_ENDPOINT="https://s3.us-south.cloud-object-storage.appdomain.cloud" \
  --from-literal SECRET_KEY="your-flask-secret-key" \
  --from-literal GRANITE_MODEL_ID="ibm/granite-3-3-8b-instruct"
```

---

## Step 6: Deploy Application

```bash
ibmcloud ce application create \
  --name startup-blueprint \
  --image us.icr.io/blueprint-ai/startup-blueprint:latest \
  --registry-secret ce-auto-icr-private-us-south \
  --env-from-secret blueprint-secrets \
  --port 5000 \
  --cpu 2 \
  --memory 4G \
  --min-scale 0 \
  --max-scale 5 \
  --concurrency 100
```

---

## Step 7: Get Application URL

```bash
ibmcloud ce application get --name startup-blueprint
# Look for "URL:" in the output
```

---

## Step 8: Configure Custom Domain (Optional)

```bash
# Map a custom domain
ibmcloud ce application update \
  --name startup-blueprint \
  --hostname blueprintai.yourdomain.com
```

---

## Auto-Scaling Configuration

Code Engine automatically scales based on incoming requests:

| Metric | Setting |
|--------|---------|
| Min instances | 0 (scale to zero when idle) |
| Max instances | 5 |
| Concurrency | 100 req/instance |
| CPU | 2 vCPU |
| Memory | 4 GB |

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `IBM_WATSONX_API_KEY` | Yes | watsonx.ai API key |
| `IBM_WATSONX_PROJECT_ID` | Yes | watsonx.ai project ID |
| `IBM_WATSONX_URL` | Yes | watsonx.ai endpoint URL |
| `IBM_COS_API_KEY` | Yes | COS API key |
| `IBM_COS_INSTANCE_CRN` | Yes | COS instance CRN |
| `IBM_COS_ENDPOINT` | Yes | COS S3 endpoint |
| `GRANITE_MODEL_ID` | No | Default: `ibm/granite-3-3-8b-instruct` |
| `SECRET_KEY` | Yes | Flask session secret key |
| `FLASK_DEBUG` | No | Set `false` in production |

---

## IBM COS Bucket Setup

Before deployment, create these buckets in your COS instance:

```bash
# Using ibmcloud CLI with COS plugin
ibmcloud cos bucket-create --bucket startup-knowledge-base --region us-south
ibmcloud cos bucket-create --bucket startup-reports --region us-south
ibmcloud cos bucket-create --bucket startup-resources --region us-south
```

Upload initial knowledge base documents:
```bash
ibmcloud cos object-put \
  --bucket startup-knowledge-base \
  --key startup_india_guide.txt \
  --body ./knowledge_base/startup_india_guide.txt
```

---

## CI/CD with IBM Cloud Toolchain (Optional)

```yaml
# .tekton/pipeline.yaml (simplified)
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: deploy-blueprint-ai
spec:
  tasks:
    - name: build-image
      taskRef:
        name: icr-build
    - name: deploy
      taskRef:
        name: code-engine-deploy
      params:
        - name: app-name
          value: startup-blueprint
```

---

## Health Check

After deployment, verify:

```bash
curl https://YOUR-APP-URL.us-south.codeengine.appdomain.cloud/api/health
```

Expected response:
```json
{
  "status": "ok",
  "granite": true,
  "rag": true,
  "cos": true
}
```

---

## Cost Estimation (IBM Cloud Code Engine)

| Resource | Cost |
|----------|------|
| Compute (2 vCPU × 4GB) | ~$0.00034/vCPU-sec |
| Scale to zero when idle | Free |
| 1M requests/month | ~$0.53 |
| IBM COS storage (10 GB) | ~$0.23/month |
| watsonx.ai (Granite) | Token-based pricing |

> Scale-to-zero means you pay only when the app is processing requests.

---

*IBM Cloud Code Engine — Serverless, scalable, pay-per-use*
