locals {
  domain_name   = trimsuffix(var.domain, ".")
  parts         = split(".", local.domain_name)
  parent_domain = join(".", slice(local.parts, 1, length(local.parts)))
  resolver_name = replace(local.domain_name, ".", "_")
}

resource "aws_route53_zone" "child_domain" {
  provider = aws.nonprod_account
  name     = local.domain_name
}

data "aws_route53_zone" "parent_domain" {
  provider = aws.prod_account
  name     = local.parent_domain
}


resource "aws_route53_record" "delegation" {
  provider = aws.prod_account
  zone_id  = data.aws_route53_zone.parent_domain.zone_id
  name     = local.domain_name
  type     = "NS"
  ttl      = 172800
  records  = aws_route53_zone.child_domain.name_servers
}

resource "aws_acm_certificate" "cert" {
  provider          = aws.nonprod_account
  domain_name       = local.domain_name
  validation_method = "DNS"
  subject_alternative_names = [
    "*.${local.domain_name}"
  ]
  tags = {
    Name = local.domain_name
  }
}

resource "aws_acm_certificate_validation" "cert" {
  provider = aws.nonprod_account
  timeouts {
    create = "5m"
  }
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [aws_route53_record.validation.fqdn]
}

resource "aws_route53_record" "validation" {
  provider        = aws.nonprod_account
  zone_id         = aws_route53_zone.child_domain.zone_id
  name            = tolist(aws_acm_certificate.cert.domain_validation_options)[0].resource_record_name
  type            = tolist(aws_acm_certificate.cert.domain_validation_options)[0].resource_record_type
  records         = [tolist(aws_acm_certificate.cert.domain_validation_options)[0].resource_record_value]
  allow_overwrite = true
  ttl             = "60"
}

resource "aws_route53_zone" "private" {
  provider = aws.nonprod_account
  name     = local.domain_name

  vpc {
    vpc_id = var.private_hosted_zone_vpc_id
  }
}
