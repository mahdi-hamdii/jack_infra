# AWS Credentials Configuration Guide

This guide explains how to set up AWS credentials for different environments (dev, staging, prod) on your local machine.

## Prerequisites

- AWS CLI installed
- AWS access keys for each environment
- VS Code or preferred text editor

## Configuration Steps

### 1. Navigate to AWS Credentials Directory

```bash
cd ~/.aws
```

### 2. Edit Credentials File

Open the credentials file in your preferred editor:

```bash
code .
```

Navigate to the `credentials` file and add your AWS credentials using the following structure:

```ini
[dev]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN # add this in case you have session token

[staging]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN # add this in case you have session token

[prod]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN # add this in case you have session token
```

### 3. Configure AWS Regions

Edit the `config` file to set default regions for each profile:

```ini
[profile dev]
region = us-east-1

[profile staging]
region = us-east-1

[profile prod]
region = us-east-1
```

## Using AWS Profiles with Terraform

To use a specific AWS profile with Terraform, set the `AWS_PROFILE` environment variable:

```bash
# For staging environment
export AWS_PROFILE=staging

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply changes
terraform apply
```

## Security Best Practices

1. Never commit AWS credentials to version control
2. Use IAM roles when possible instead of access keys
3. Rotate access keys regularly
4. Use the principle of least privilege when creating IAM users and policies

## Troubleshooting

If you encounter authentication issues:
1. Verify the credentials are correctly formatted
2. Check if the AWS profile is properly set
3. Ensure the access keys have the necessary permissions
4. Verify the region matches your AWS resources

## Additional Resources

- [AWS CLI Configuration Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
