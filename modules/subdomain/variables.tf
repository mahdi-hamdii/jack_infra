variable "domain_name" {
  type        = string
  description = "The domain name to create the subdomain for"
}

variable "private_hosted_zone_vpc_id" {
  type        = string
  description = "The VPC ID for the private hosted zone"
}
