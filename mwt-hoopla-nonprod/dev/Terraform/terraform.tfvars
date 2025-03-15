############################################################
# Global Variables
############################################################

businessunit = "hoopla"
environment  = "dev"
region       = "us-east-1"
department   = "infrastructure"
owner        = "jmezinko"
application  = "network"

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

  confluent_cloud_vpn = {
    rules = [
      {
        from_port   = 9092
        to_port     = 9092
        protocol    = "tcp"
        cidr_blocks = "100.64.0.0/16"
      },
      {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        cidr_blocks = "100.64.0.0/16"
      }
    ]
    tags = {
      application = "security"
    }
  }

  db_comm_postgresql_internal = {
    rules = [
      {
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        cidr_blocks = "10.11.0.0/16"
      }
    ]
    tags = {
      application = "security"
    }
  }

  dms_peer_internal = {
    rules = [
      {
        from_port   = 1521
        to_port     = 1521
        protocol    = "tcp"
        cidr_blocks = "10.11.0.0/16"
      }
    ]
    tags = {
      application = "security"
    }
  }

  db_comm_oracle_ecom = {
    rules = [
      {
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        cidr_blocks = "10.11.0.0/16"
      }
    ]
    tags = {
      application = "security"
    }
  }

  redis = {
    rules = [
      {
        from_port   = 6379
        to_port     = 6379
        protocol    = "tcp"
        cidr_blocks = "10.223.0.0/16"
      }
    ]
    tags = {
      application = "security"
    }
  }

  redis_connect_dev_test_staging = {
    rules = [
      {
        from_port   = 6379
        to_port     = 6379
        protocol    = "tcp"
        cidr_blocks = "10.0.130.0/23"
      },
      {
        from_port   = 6379
        to_port     = 6379
        protocol    = "tcp"
        cidr_blocks = "10.0.132.0/23"
      }
    ]
    tags = {
      application = "security"
    }
  }

  eks_connect = {
    rules = [
      {
        from_port   = 6379
        to_port     = 6379
        protocol    = "tcp"
        cidr_blocks = "10.0.130.0/23"
      },
      {
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        cidr_blocks = "10.0.130.0/23"
      },
      {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        cidr_blocks = "10.0.130.0/23"
      },
      {
        from_port   = 6379
        to_port     = 6379
        protocol    = "tcp"
        cidr_blocks = "10.0.132.0/23"
      },
      {
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        cidr_blocks = "10.0.132.0/23"
      },
      {
        from_port   = 443
        to_port     = 443
        protocol    = "tcp"
        cidr_blocks = "10.0.132.0/23"
      }
    ]
    tags = {
      application = "security"
    }
  }

  route53_rslvr_in = {
    rules = [
      {
        from_port   = 53
        to_port     = 53
        protocol    = "tcp"
        cidr_blocks = "10.223.2.0/24"
      },
      {
        from_port   = 53
        to_port     = 53
        protocol    = "udp"
        cidr_blocks = "10.223.2.0/24"
      }
    ]
    tags = {
      application = "security"
    }
  }
}

############################################################
# Route 53 subdomains
############################################################

route53_subdomain = [
  {
    domain                    = "dev.hoopladigital.cloud",
    subject_alternative_names = ["*.dev.hoopladigital.cloud"]
  },
  {
    domain                    = "test.hoopladigital.cloud",
    subject_alternative_names = ["*.test.hoopladigital.cloud"]
  },
  {
    domain                    = "staging.hoopladigital.cloud",
    subject_alternative_names = ["*.staging.hoopladigital.cloud"]
  },
  {
    domain                    = "dev.hoopladigital.com",
    subject_alternative_names = ["*.dev.hoopladigital.com"]
  },
  {
    domain                    = "test.hoopladigital.com",
    subject_alternative_names = ["*.test.hoopladigital.com"]
  },
  {
    domain                    = "staging.hoopladigital.com",
    subject_alternative_names = ["*.staging.hoopladigital.com"]
  }
]

route53_resolver_endpoint = {
  name                   = "InboundEndpoint"
  direction              = "INBOUND"
  security_group_keyname = "route53_rslvr_in"
  protocols              = ["Do53", "DoH"]
  # ip_addresses           = ["10.110.10.0/23", "10.110.12.0/23", "10.110.14.0/23"] #if not specified use the VPC private subnets
}
