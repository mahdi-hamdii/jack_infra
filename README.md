# Hoopla Infrastructure

This repository contains the Infrastructure as Code (IaC) for the Hoopla project using Terraform. The infrastructure is organized to support multiple environments while maintaining a single source of truth for common configurations.

## Project Structure

```
infrastructure/               # Root organization infrastructure directory
├── modules/                  # Central repository for all organization's Terraform modules
│   └── route53_subdomain  # Cutom module
│
└── mwt-hoopla-nonprod/      # Hoopla project infrastructure (this repository)
    ├── common/              # Common infrastructure code shared across all environments
    │   └── Terraform/       # Common Terraform configurations
    │       ├── main.tf      # Main infrastructure definitions
    │       ├── variables.tf # Variable declarations
    │       ├── outputs.tf   # Output definitions
    │       └── ...
    ├── dev/                 # Development environment specific configurations
    │   └── Terraform/
    │       ├── terraform.tfvars    # Development environment variables
    │       └── terraform.tfbackend # Backend configuration for dev
    └── staging/            # Staging environment specific configurations
        └── Terraform/
            ├── terraform.tfvars    # Staging environment variables
            └── terraform.tfbackend # Backend configuration for staging

```

## Custom Modules

The `modules` repository is our organization's central collection of **custom-built Terraform modules**. This is a separate repository at the same level as project-specific repositories like mwt-hoopla-nonprod. These modules are designed to be used across all infrastructure projects in our organization.

### Purpose of Custom Modules
- Provide standardized infrastructure patterns across all organization projects
- Implement company-wide security and compliance requirements
- Create a single source of truth for common infrastructure components
- Enable consistent infrastructure deployment across different teams and projects
- Reduce duplication of effort across teams
- Ensure best practices are followed across the organization

### Using Custom Modules
- Modules are maintained in their own repository (`modules`) separate from project repositories
- Projects reference these modules using Git source or registry references
- Each module follows strict versioning to ensure stability across projects
- Changes to modules go through thorough review process as they affect multiple projects
- Teams can request new features or modifications through the central module repository
- Documentation and usage examples are maintained centrally

Example of module usage in a project:
```hcl
module "vpc" {
  source = "local_path_to_the_module"
  
  # Module configuration...
}
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
     businessunit = "hoopla"
     environment  = "dev"
     region       = "us-east-1"
     department   = "infrastructure"
     owner        = "jmezinko"
     application  = "network"

     vpc = {
       cidr = "10.110.0.0/16"
       azs  = ["us-east-1a", "us-east-1b", "us-east-1c"]
       public_subnets = {
         public_1a = "10.110.110.0/23"
         public_1b = "10.110.112.0/23"
         public_1c = "10.110.114.0/23"
       }
       private_subnets = {
         private_1a = "10.110.10.0/23"
         private_1b = "10.110.12.0/23"
         private_1c = "10.110.14.0/23"
       }
       enable_nat_gateway     = true
       single_nat_gateway     = true
       one_nat_gateway_per_az = true
       enable_dns_hostnames   = true
       enable_dns_support     = true
     }
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
6. To destroy the changes (in this case its dev):
```bash
terraform destroy -var-file="../../dev/Terraform/terraform.tfvars"
```

## Important Notes

- Always use the appropriate environment's `terraform.tfvars` and `terraform.tfbackend` files
- Never commit sensitive information (like AWS credentials) to version control
- Use workspace-specific variables for environment-specific configurations
- Regular backups of state files are recommended
- Follow the principle of least privilege when setting up AWS credentials

## Create new environment (staging for example)

To create a new environment, follow these steps:

1. Copy the existing environment folder (in this case, copy `dev` to create `staging`):
```bash
cd mwt-hoopla-nonprod
cp -r dev staging
```

2. Update the `terraform.tfvars` file in the new environment:
```bash
vim staging/Terraform/terraform.tfvars
```

Change the environment-specific values, for example:
```hcl
# Before (in dev/Terraform/terraform.tfvars)
businessunit = "hoopla"
environment  = "dev"
region       = "us-east-1"
department   = "infrastructure"
owner        = "jmezinko"
application  = "network"

vpc = {
  cidr = "10.110.0.0/16"
  azs  = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets = {
    public_1a = "10.110.110.0/23"
    public_1b = "10.110.112.0/23"
    public_1c = "10.110.114.0/23"
  }
  private_subnets = {
    private_1a = "10.110.10.0/23"
    private_1b = "10.110.12.0/23"
    private_1c = "10.110.14.0/23"
  }
  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true
}

# After (in staging/Terraform/terraform.tfvars)
businessunit = "hoopla"
environment  = "staging"
region       = "us-east-1"
department   = "infrastructure"
owner        = "jmezinko"
application  = "network"

vpc = {
  cidr = "10.120.0.0/16"
  azs  = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets = {
    public_1a = "10.120.110.0/23"
    public_1b = "10.120.112.0/23"
    public_1c = "10.120.114.0/23"
  }
  private_subnets = {
    private_1a = "10.120.10.0/23"
    private_1b = "10.120.12.0/23"
    private_1c = "10.120.14.0/23"
  }
  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true
}
```

3. Update the `terraform.tfbackend` file:
```bash
vim staging/Terraform/terraform.tfbackend
```

Change the backend configuration:
```hcl
# Before (in dev/Terraform/terraform.tfbackend)
bucket = "my-terraform-state-dev"
key    = "terraform.tfstate"
region = "us-east-1"

# After (in staging/Terraform/terraform.tfbackend)
bucket = "my-terraform-state-staging"  # Different bucket for staging state
key    = "terraform.tfstate"
region = "us-east-1"
```

4. Create the new state bucket in AWS (if it doesn't exist):
```bash
aws s3 mb s3://my-terraform-state-staging --region us-east-1
```

5. Deploy the new environment:
```bash
# Navigate to common Terraform directory
cd mwt-hoopla-nonprod/common/Terraform

# Initialize with staging backend
terraform init -backend-config="../../staging/Terraform/terraform.tfbackend"

# Plan with staging variables
terraform plan -var-file="../../staging/Terraform/terraform.tfvars"

# Apply the changes
terraform apply -var-file="../../staging/Terraform/terraform.tfvars"
```

Important Notes for New Environments:
- Ensure unique values for environment-specific resources (VPC CIDRs, bucket names, etc.)
- Verify AWS credentials have necessary permissions in the new environment
- Consider different resource sizes/counts based on environment needs
- Update any environment-specific tags or naming conventions
- Document the new environment in your team's documentation

