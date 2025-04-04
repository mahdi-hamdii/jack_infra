import boto3
import csv
from botocore.config import Config


def list_accounts():
    """List all active accounts in AWS Organizations."""
    org_client = boto3.client("organizations")
    accounts = []
    paginator = org_client.get_paginator("list_accounts")

    for page in paginator.paginate():
        accounts.extend(page["Accounts"])

    return [account["Id"] for account in accounts if account["Status"] == "ACTIVE"]


def main():
    accounts = list_accounts()
    print(accounts)


if __name__ == "__main__":
    main()
