# EventBridge Infrastructure

This repository contains the Infrastructure as Code (IaC) for the EventBridge that triggers key rotation state machine using Terraform. The infrastructure is organized to support multiple environments while maintaining a single source of truth for common configurations.

## Variables to adapt:

- Make sure that you update the **target_state_machine_name** with the name of the State Machine you want to run.
- Verify Previous runs of the state machine to check if it expects an input. if it does then update the value of this variable **target_state_machine_input** with the correct input
- Update the **schedule_expression** with the rate of the schedule you want. For now the rate is 90 days

## How to Deploy Infrastructure

1. Navigate to the common Terraform folder:

```bash
cd event-bridge-trigger/common
```

2. Export AWS credentials:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

3. Initialize Terraform with environment-specific backend (in this case its dev):

```bash
terraform init -backend-config="../dev/terraform.tfbackend"
```

4. Plan the changes (in this case its dev):

```bash
terraform plan -var-file="../dev/terraform.tfvars"
```

5. Apply the changes (in this case its dev):

```bash
terraform apply -var-file="../dev/terraform.tfvars"
```

6. To destroy the changes (in this case its dev):

```bash
terraform destroy -var-file="../../dev/terraform.tfvars"
```
