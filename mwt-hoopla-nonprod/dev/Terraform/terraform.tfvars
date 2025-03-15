############################################################
# Global Variables
############################################################

businessunit = "hoopla"
environment  = "dev"
region       = "us-east-1"

############################################################
# VPC
############################################################

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

  enable_dns_hostnames = true
  enable_dns_support   = true
}

############################################################
# Transit Gateway
############################################################

transit_gateway = {
  id = "tgw-0e5565cde933cdfb9"
}

############################################################
# VPC Endpoints
############################################################

vpc_endpoints = {

  create_security_group      = true
  security_group_name_prefix = "vpc_endpoints_"
  security_group_description = "VPC endpoint security group"

  security_group_rules = {
    ingress_https = {
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      type        = "ingress"
      description = "HTTPS from VPC"
      #   cidr_blocks = ["10.110.0.0/16"] If ommited use the VPC CIDR
    }
  }

  endpoints = {
    s3 = {
      service      = "s3"
      service_type = "Gateway"
      #   route_table_ids = ["rtb-XXXXXX"] If ommited use the VPC Route Table ids
    }
  }

}

############################################################
# Security Groups
############################################################


security_groups = {
  datacenter_rdp = {
    rules = [
      {
        from_port   = 3389
        to_port     = 3389
        protocol    = "tcp"
        cidr_blocks = "10.223.0.0/16"
      }
    ]
    tags = {
      application = "security"
    }
  }

  # TODO - add more security groups

}
