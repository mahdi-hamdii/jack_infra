# Hoopla infra

## How to create the infrastructure

```bash
# Go to the common Terraform folder
cd mwt-hoopla-nonprod/common/Terraform

# Export the required environment variables
export AWS_ACCESS_KEY_ID="anaccesskey"
export AWS_SECRET_ACCESS_KEY="asecretkey"
export AWS_REGION="us-east-1"

# Terraform init
terraform init -backend-config="../../dev/Terraform/terraform.tfbackend"

# Terraform Plan
terraform plan -var-file="../../dev/Terraform/terraform.tfvars"

# Terraform Apply
terraform apply -var-file="../../dev/Terraform/terraform.tfvars"
```
