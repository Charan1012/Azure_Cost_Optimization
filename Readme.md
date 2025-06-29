# Azure Cosmos DB Cost Optimization Solution

![Architecture Diagram](images/Architecture_Diagram.png)

## 📌 Overview

Production-grade solution to reduce Azure Cosmos DB costs by **automatically archiving** infrequently accessed data to Blob Storage Cool Tier, cutting storage costs by **~95%**. Implements tiered storage with seamless data retrieval.

## 🛠️ Key Components

| Component       | Technology               | Purpose                          |
|-----------------|--------------------------|----------------------------------|
| **Hot Tier**    | Azure Cosmos DB          | Low-latency access to recent data|
| **Cold Tier**   | Blob Storage Cool Tier   | Cost-effective archival          |
| **Orchestration** | Azure Functions        | Serverless data pipeline         |
| **Infrastructure** | Terraform             | IaC for repeatable deployments   |
| **API Layer**   | Python HTTP Function     | Unified data access              |

## 🚀 Getting Started

### Prerequisites

- Azure CLI (`az login`)
- Terraform v1.5+
- Python 3.9+

### Deployment

```bash
# 1. Provision infrastructure
cd infrastructure/
terraform init
terraform apply -auto-approve

# 2. Deploy functions
az functionapp deployment source config-zip \
    -g $(terraform output -raw resource_group_name) \
    -n $(terraform output -raw function_app_name) \
    --src ../functions.zip

# 3. Seed test data
FUNCTION_URL=$(terraform output -raw seed_function_url)
curl -X POST $FUNCTION_URL
