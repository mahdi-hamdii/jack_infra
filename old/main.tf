
module "base" {
  source = "../.././modules/ops/nonprod_base"
  providers = {
    aws.nonprod_account = aws
    aws.prod_account    = aws.mwt-hoopla-prod
  }

  businessunit       = "hoopla"
  environment        = "nonprod"
  region             = "us-east-1"
  vpc_cidr           = "10.110.0.0/16"
  transit_gateway_id = "tgw-0e5565cde933cdfb9"

  azs = [
    "us-east-1a",
    "us-east-1b",
    "us-east-1c",
  ]

  # ========================================================================
  # NOTE: Subnet Ordering
  # ========================================================================
  # No natter what order the subnets are in, Terraform puts them in alphabetic
  # order and distributes them across the azs specified above. It's best to
  # keep these in alphabetic order so you know which azs the subnets are
  # being deployed to.
  # ========================================================================

  public_subnets = {
    public_1a = "10.110.110.0/23",
    public_1b = "10.110.112.0/23",
    public_1c = "10.110.114.0/23",
    # public_auth_la = "10.110.131.0/24" # <-- will go in another module
  }

  private_subnets = {
    private_1a = "10.110.10.0/23"
    private_1b = "10.110.12.0/23"
    private_1c = "10.110.14.0/23"
    # private_auth_la = "10.110.31.0/24" # <-- will go in another module
    # private_eks_1b = "10.110.50.0/23" # <-- will go in another module
    # private_eks_1c = "10.110.52.0/23" # <-- will go in another module
  }

  # security groups missing part
  # TODO - VERIFY THE MISSING CONFIGURATION HERE


}

