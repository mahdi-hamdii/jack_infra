############################################################
# Global
############################################################

variable "businessunit" {
  type        = string
  description = "Busniess Unit"
}

variable "environment" {
  type        = string
  description = "Environment"
}

variable "region" {
  type        = string
  description = "Region"
}

variable "department" {
  type        = string
  description = "Department"
}

variable "owner" {
  type        = string
  description = "Owner"
}

variable "application" {
  type        = string
  description = "Application"
}

############################################################
# VPC
############################################################

variable "vpc" {
  type        = any
  description = "VPC Configuration"
}

############################################################
# Transit Gateway
############################################################

variable "transit_gateway" {
  type        = any
  description = "Transit Gateway Configuration"
}

############################################################
# VPC Endpoints
############################################################

variable "vpc_endpoints" {
  type        = any
  description = "VPC Endpoints Configuration"
}

############################################################
# Security Groups
############################################################

variable "security_groups" {
  type        = any
  description = "Security Groups Configuration"
}

############################################################
# Route 53 subdomains
############################################################

variable "route53_subdomain" {
  type        = any
  description = "Route 53 subdomains Configuration"
}

variable "route53_resolver_endpoint" {
  type        = any
  description = "Route 53 resolver endpoint Configuration"
}

############################################################
# EC2 Instance
############################################################

variable "ec2_instance" {
  description = "EC2 instance configuration"
  type = object({
    instance_type               = string
    ami                         = string
    associate_public_ip_address = bool
    security_group_keyname      = string
    enable_volume_tags          = bool
    root_block_device = list(object({
      encrypted   = bool
      volume_type = string
      volume_size = number
    }))
    tags = map(string)
  })
}
