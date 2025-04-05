import boto3
import csv
import os
import configparser
from botocore.config import Config
from datetime import datetime

def list_profiles():
    """List AWS profiles from ~/.aws/config more safely."""
    config_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(config_path)

    profiles = []

    for section in config.sections():
        if section.lower().strip().startswith("profile "):
            profile_name = section.strip().split("profile ", 1)[-1].strip()
            profiles.append(profile_name)

    return profiles


def list_iam_users(session):
    """List all IAM users using the provided boto3 session."""
    iam_client = session.client('iam')
    users = []
    paginator = iam_client.get_paginator('list_users')

    for page in paginator.paginate():
        users.extend(page['Users'])

    return users


def main():
    profiles = list_profiles()

    print("\n✅ Profiles to work on:")
    for profile in profiles:
        print(f"  - {profile}")

    all_users_data = []

    for profile in profiles:
        print(f"\n🔵 Fetching IAM users for profile: {profile}")

        try:
            # Create session for that profile
            session = boto3.Session(profile_name=profile)

            # Get the account ID (important for reporting)
            sts_client = session.client('sts')
            account_id = sts_client.get_caller_identity()['Account']

            # List IAM users
            iam_users = list_iam_users(session)

            if iam_users:
                for user in iam_users:
                    print(f"    ➡️  {user['UserName']}")
                    all_users_data.append({
                        "Profile": profile,
                        "AccountId": account_id,
                        "UserName": user['UserName'],
                        "CreateDate": user['CreateDate'].strftime("%Y-%m-%dT%H:%M:%S")
                    })
            else:
                print(f"    ⚠️  No IAM users found for profile {profile}")

        except Exception as e:
            print(f"❌ Failed to fetch users for profile {profile}: {e}")

    # Save to CSV
    if all_users_data:
        today = datetime.today().strftime("%Y-%m-%d")
        csv_filename = f"iam_users_all_profiles_{today}.csv"

        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = ["Profile", "AccountId", "UserName", "CreateDate"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users_data)

        print(f"\n✅ IAM users list exported to {csv_filename}")
    else:
        print("\n⚠️ No users found across any profiles!")


if __name__ == "__main__":
    main()
