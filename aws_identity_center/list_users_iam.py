import boto3
import csv
from botocore.config import Config

def list_accounts():
    """List all active accounts in AWS Organizations."""
    org_client = boto3.client('organizations')
    accounts = []
    paginator = org_client.get_paginator('list_accounts')

    for page in paginator.paginate():
        accounts.extend(page['Accounts'])

    return [account['Id'] for account in accounts if account['Status'] == 'ACTIVE']


def get_sso_role_name():
    """Dynamically retrieve the SSO role name from the current caller identity."""
    sts_client = boto3.client('sts')
    identity = sts_client.get_caller_identity()
    arn = identity['Arn']

    if ":assumed-role/" in arn:
        role_part = arn.split(":assumed-role/")[1]
        role_name = role_part.split("/")[0]
        print(f"Detected current SSO role name: {role_name}")
        return role_name
    else:
        raise Exception("Could not detect SSO assumed role automatically.")


def assume_role_in_account(account_id, role_name):
    """Assume the correct role into the target account."""
    sts_client = boto3.client('sts')
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName="ListIAMUsersSession"
    )

    credentials = response['Credentials']

    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    return session.client("iam")


def list_iam_users(iam_client):
    """List all IAM users using the provided IAM client."""
    users = []
    paginator = iam_client.get_paginator('list_users')

    for page in paginator.paginate():
        users.extend(page['Users'])

    return users


def main():
    accounts = list_accounts()
    role_name = get_sso_role_name()
    all_users_data = []

    for account_id in accounts:
        print(f"\n--- Fetching IAM users from Account {account_id} ---")
        try:
            iam_client = assume_role_in_account(account_id, role_name)
            users = list_iam_users(iam_client)

            for user in users:
                print(f"User: {user['UserName']}")
                all_users_data.append({
                    "AccountId": account_id,
                    "UserName": user['UserName'],
                    "CreateDate": user['CreateDate'].strftime("%Y-%m-%dT%H:%M:%S")
                })

        except Exception as e:
            print(f"Failed to fetch users in account {account_id}: {e}")

    # Save everything into CSV
    if all_users_data:
        with open("iam_users_all_accounts.csv", "w", newline="") as csvfile:
            fieldnames = ["AccountId", "UserName", "CreateDate"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users_data)

        print("\n✅ IAM users list exported to iam_users_all_accounts.csv")


if __name__ == "__main__":
    main()
