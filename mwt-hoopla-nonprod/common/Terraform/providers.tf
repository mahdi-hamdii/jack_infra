terraform {

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.83.0"
    }
  }

  # This part is initialized on the terraform.tfbackend (specific to each environment)
  # do not delete it, it is filled in the terraform init command
  backend "s3" {
    bucket = ""
    key    = ""
    region = ""
  }
}

# First AWS Provider (nonprod account)
provider "aws" {
  region = var.region
  # Auth will be handled by environment variables:
  # AWS_ACCESS_KEY_ID
  # AWS_SECRET_ACCESS_KEY

  default_tags {
    tags = {
      environment  = var.environment
      businessunit = var.businessunit
      department   = var.department
      owner        = var.owner
      application  = var.application
    }
  }
}

# Second AWS Provider (production account)
provider "aws" {
  alias  = "mwt-hoopla-prod"
  region = "us-east-1"
  # Auth will be handled by environment variables:
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY will be used to assume the role

  assume_role {
    role_arn = "arn:aws:iam::058253789961:role/route53_add_ns_record_for_delegation"
  }
}
