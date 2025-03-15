# Hoopla Infrastructure

This repository contains the Infrastructure as Code (IaC) for the Hoopla project using Terraform. The infrastructure is organized to support multiple environments while maintaining a single source of truth for common configurations.

## Project Structure

```
mwt-hoopla-nonprod/
├── common/                # Common infrastructure code shared across all environments
│   └── Terraform/         # Common Terraform configurations
│       ├── main.tf        # Main infrastructure definitions
│       ├── variables.tf   # Variable declarations
│       ├── outputs.tf     # Output definitions
│       └── ...
├── dev/                   # Development environment specific configurations
│   └── Terraform/
│       ├── terraform.tfvars    # Development environment variables
│       └── terraform.tfbackend # Backend configuration for dev
├── staging/              # Staging environment specific configurations
│   └── Terraform/
│       ├── terraform.tfvars    # Staging environment variables
│       └── terraform.tfbackend # Backend configuration for staging
└── prod/                # Production environment specific configurations
    └── Terraform/
        ├── terraform.tfvars    # Production environment variables
        └── terraform.tfbackend # Backend configuration for prod
```

## Architecture Overview

### Common Code (`common/` directory)
- Contains all the shared infrastructure code that is environment-agnostic
- Includes the core Terraform configurations, modules, and resources
- Should only be modified when:
  - Adding new infrastructure components
  - Modifying existing infrastructure behavior
  - Fixing bugs
  - Adding new features

### Environment-Specific Code (`dev/`, `staging/`, `prod/` directories)
- Contains environment-specific configurations
- Only two files should be modified per environment:
  1. `terraform.tfvars`: Contains environment-specific values
     ```hcl
     # Example terraform.tfvars
     environment     = "dev"
     instance_type  = "t3.micro"
     vpc_cidr       = "10.0.0.0/16"
     ```
  2. `terraform.tfbackend`: Specifies the backend configuration
     ```hcl
     # Example terraform.tfbackend
     bucket         = "my-terraform-state-dev"
     key            = "terraform.tfstate"
     region         = "us-east-1"
     ```

## Best Practices

1. **Code Reusability**
   - Common infrastructure code is maintained in the `common/` directory
   - Environment-specific values are defined in `terraform.tfvars`
   - Never hardcode environment-specific values in common code

2. **Change Management**
   - Only modify files in the `common/` directory when changing functionality
   - Environment-specific changes should only involve modifying `terraform.tfvars` and `terraform.tfbackend`
   - All changes should go through code review

3. **State Management**
   - Each environment has its own state file
   - State files are stored in S3 
   - Backend configurations are environment-specific

## How to Deploy Infrastructure

1. Navigate to the common Terraform folder:
```bash
cd mwt-hoopla-nonprod/common/Terraform
```

2. Export AWS credentials:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

3. Initialize Terraform with environment-specific backend (in this case its dev):
```bash
terraform init -backend-config="../../dev/Terraform/terraform.tfbackend"
```

4. Plan the changes (in this case its dev):
```bash
terraform plan -var-file="../../dev/Terraform/terraform.tfvars"
```

5. Apply the changes (in this case its dev):
```bash
terraform apply -var-file="../../dev/Terraform/terraform.tfvars"
```

## Important Notes

- Always use the appropriate environment's `terraform.tfvars` and `terraform.tfbackend` files
- Never commit sensitive information (like AWS credentials) to version control
- Use workspace-specific variables for environment-specific configurations
- Regular backups of state files are recommended
- Follow the principle of least privilege when setting up AWS credentials



