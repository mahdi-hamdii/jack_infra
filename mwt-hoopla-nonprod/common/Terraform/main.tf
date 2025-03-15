############################################################
# VPC
############################################################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.18.1"

  name = "${var.businessunit}_${var.environment}"

  cidr = var.vpc.cidr
  azs  = var.vpc.azs

  public_subnet_names = keys(var.vpc.public_subnets)
  public_subnets      = values(var.vpc.public_subnets)

  private_subnet_names = keys(var.vpc.private_subnets)
  private_subnets      = values(var.vpc.private_subnets)

  enable_nat_gateway     = var.vpc.enable_nat_gateway
  single_nat_gateway     = var.vpc.single_nat_gateway
  one_nat_gateway_per_az = var.vpc.one_nat_gateway_per_az

  enable_dns_hostnames = var.vpc.enable_dns_hostnames
  enable_dns_support   = var.vpc.enable_dns_support
}

############################################################
# Transit Gateway
############################################################

resource "aws_ec2_transit_gateway_vpc_attachment" "ec2_transit_gateway_vpc_attachment" {
  subnet_ids         = module.vpc.private_subnets
  transit_gateway_id = var.transit_gateway.id
  vpc_id             = module.vpc.vpc_id
}

############################################################
# VPC Endpoints
############################################################

module "vpc_endpoints" {
  source  = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"
  version = "5.18.1"

  vpc_id = module.vpc.vpc_id

  create_security_group      = var.vpc_endpoints.create_security_group
  security_group_name_prefix = var.vpc_endpoints.security_group_name_prefix
  security_group_description = var.vpc_endpoints.security_group_description

  security_group_rules = {
    for key, value in var.vpc_endpoints.security_group_rules : key => {
      protocol    = lookup(value, "protocol", "tcp")
      from_port   = lookup(value, "from_port", 443)
      to_port     = lookup(value, "to_port", 443)
      type        = lookup(value, "type", "ingress")
      cidr_blocks = lookup(value, "cidr_blocks", [module.vpc.vpc_cidr_block])
      description = lookup(value, "description", "VPC Endpoint Security Group Rule")
    }
  }

  endpoints = {
    for key, value in var.vpc_endpoints.endpoints : key => {
      service         = value.service
      service_type    = lookup(value, "service_type", "Gateway")
      route_table_ids = lookup(value, "route_table_ids", module.vpc.private_route_table_ids)
    }
  }

}

############################################################
# Security Groups
############################################################

module "security_groups" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.0"

  for_each = var.security_groups

  name   = each.key
  vpc_id = module.vpc.vpc_id

  ingress_with_cidr_blocks = [
    for rule in each.value.rules : {
      from_port   = rule.from_port
      to_port     = rule.to_port
      protocol    = rule.protocol
      cidr_blocks = rule.cidr_blocks
    }
  ]

  tags = lookup(each.value, "tags", {})
}


############################################################
# Route 53
############################################################

module "route53_subdomain" {
  source = "../../../modules/route53_subdomain"

  for_each = { for subdomain in var.route53_subdomain : subdomain.domain => subdomain }

  providers = {
    aws.nonprod_account = aws.nonprod_account
    aws.prod_account    = aws.prod_account
  }

  domain                     = each.value.domain
  private_hosted_zone_vpc_id = module.vpc.vpc_id
}

resource "aws_route53_resolver_endpoint" "inbound" {
  name      = var.route53_resolver_endpoint.name
  direction = var.route53_resolver_endpoint.direction

  security_group_ids = [module.security_groups[var.route53_resolver_endpoint.security_group_keyname].security_group_id]

  protocols = var.route53_resolver_endpoint.protocols


  dynamic "ip_address" {
    for_each = toset(lookup(var.route53_resolver_endpoint, "ip_addresses", module.vpc.private_subnets))
    content {
      subnet_id = ip_address.value
    }
  }

}
