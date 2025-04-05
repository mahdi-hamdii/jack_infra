import boto3
import csv
import os
import configparser
from botocore.config import Config

def list_sso_profiles():
    """List all AWS profiles that are defined in ~/.aws/config (assume all are SSO if starting with [profile XYZ])."""
    import os
    import configparser

    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~/.aws/config"))

    profiles = []
    for section in config.sections():
        if section.startswith("profile "):
            profile_name = section.split("profile ")[1]
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
    profiles = list_sso_profiles()

    # ✅ First, print all profiles found
    print("\n✅ SSO Profiles found:")
    for profile in profiles:
        print(f"  - {profile}")

    all_users_data = []

    # ✅ Now, go one by one and fetch users
    for profile in profiles:
        print(f"\n🔵 Fetching IAM users for profile: {profile}")

        try:
            session = boto3.Session(profile_name=profile)
            iam_users = list_iam_users(session)

            # Get account ID for reference
            sts_client = session.client('sts')
            account_id = sts_client.get_caller_identity()['Account']

            if iam_users:
                for user in iam_users:
                    print(f"    User: {user['UserName']}")
                    all_users_data.append({
                        "Profile": profile,
                        "AccountId": account_id,
                        "UserName": user['UserName'],
                        "CreateDate": user['CreateDate'].strftime("%Y-%m-%dT%H:%M:%S")
                    })
            else:
                print(f"    ⚠️ No IAM users found for profile {profile}")

        except Exception as e:
            print(f"❌ Failed to fetch users for profile {profile}: {e}")

    # Save to CSV
    if all_users_data:
        from datetime import datetime
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
