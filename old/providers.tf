terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.83.0"
    }
  }

  backend "s3" {
    bucket = "mwt.hoopla.nonprod.tf.backend"
    key    = "base/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      environment  = "nonprod"
      businessunit = "hoopla"
      department   = "infrastructure"
      owner        = "jmezinko"
      application  = "network"
    }
  }
}

provider "aws" {
  alias  = "art-hoopla-prod"
  region = "us-east-1"
  assume_role {
    role_arn = "arn:aws:iam:: 058253789961: role/route53_addins_record_for_delegation"
  }
}
