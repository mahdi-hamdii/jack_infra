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


def create_iam_client():
    """Create a boto3 IAM client using the active SSO session."""
    session = boto3.Session()
    config = Config(retries={"max_attempts": 10, "mode": "standard"})

    return session.client(
        "iam",
        config=config,
        region_name="us-east-1",
        endpoint_url="https://iam.amazonaws.com",
    )


def list_iam_users(iam_client):
    """List all IAM users using the provided IAM client."""
    users = []
    paginator = iam_client.get_paginator("list_users")

    for page in paginator.paginate():
        users.extend(page["Users"])

    return users


def main():
    accounts = list_accounts()
    print(f"accounts in place: {accounts}")

    all_users_data = []

    for account_id in accounts:
        print(f"\n--- Fetching IAM users from Account {account_id} ---")
        try:
            # You already have SSO session; no need to assume role
            iam_client = create_iam_client()

            users = list_iam_users(iam_client)

            for user in users:
                print(f"User: {user['UserName']}")
                all_users_data.append(
                    {
                        "AccountId": account_id,
                        "UserName": user["UserName"],
                        "CreateDate": user["CreateDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                )

        except Exception as e:
            print(f"Failed to fetch users in account {account_id}: {e}")

    # Save everything into CSV
    if all_users_data:
        with open("iam_users_all_accounts.csv", "w", newline="") as csvfile:
            fieldnames = ["AccountId", "UserName", "CreateDate"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users_data)

        print("\n IAM users list exported to iam_users_all_accounts.csv")


if __name__ == "__main__":
    main()
