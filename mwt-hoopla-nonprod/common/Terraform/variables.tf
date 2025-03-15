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
