import boto3
import csv
import os
import configparser
import time
from botocore.config import Config
from datetime import datetime, timedelta, timezone


def list_profiles():
    """List AWS profiles from ~/.aws/config."""
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
    iam_client = session.client("iam")
    users = []
    paginator = iam_client.get_paginator("list_users")

    for page in paginator.paginate():
        users.extend(page["Users"])

    return users


def get_user_access_keys_last_used(iam_client, user_name):
    """Retrieve the most recent Access Key LastUsedDate for a user."""
    access_keys = iam_client.list_access_keys(UserName=user_name).get(
        "AccessKeyMetadata", []
    )
    last_used_dates = []

    for key in access_keys:
        access_key_id = key["AccessKeyId"]
        try:
            response = iam_client.get_access_key_last_used(AccessKeyId=access_key_id)
            last_used_date = response["AccessKeyLastUsed"].get("LastUsedDate")
            if last_used_date:
                last_used_dates.append(last_used_date)
        except Exception as e:
            print(f"Warning: Could not get last used date for key {access_key_id}: {e}")

    if last_used_dates:
        return max(last_used_dates)
    else:
        return None


def get_codecommit_last_used(iam_client, user_arn):
    """Retrieve the LastAccessed date for AWS CodeCommit service for a user."""
    try:
        # Start the report generation
        job_response = iam_client.generate_service_last_accessed_details(Arn=user_arn)
        job_id = job_response["JobId"]

        # Poll until job is ready
        while True:
            status_response = iam_client.get_service_last_accessed_details(JobId=job_id)
            if status_response["JobStatus"] in ["COMPLETED", "FAILED"]:
                break
            time.sleep(1)

        if status_response["JobStatus"] == "FAILED":
            print(f"Warning: Service access report generation failed for {user_arn}")
            return None

        # Parse the services used
        for service in status_response.get("ServicesLastAccessed", []):
            if service["ServiceName"] == "AWS CodeCommit":
                last_authenticated = service.get("LastAuthenticated")
                return last_authenticated

    except Exception as e:
        print(f"Warning: Error getting CodeCommit usage for {user_arn}: {e}")

    return None


def is_user_active(console_last_login, access_key_last_used, codecommit_last_used):
    """Determine if user is active within the last 30 days."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    if console_last_login and console_last_login > cutoff_date:
        return "Yes"
    if access_key_last_used and access_key_last_used > cutoff_date:
        return "Yes"
    if codecommit_last_used and codecommit_last_used > cutoff_date:
        return "Yes"
    return "No"


def list_identity_store_usernames():
    """Fetch all SSO usernames from Identity Store (only the part before @), stored in lowercase."""
    client = boto3.client("sso-admin")
    instances = client.list_instances()
    identity_store_id = instances["Instances"][0]["IdentityStoreId"]

    identitystore_client = boto3.client("identitystore")
    usernames = set()
    next_token = None

    while True:
        if next_token:
            response = identitystore_client.list_users(
                IdentityStoreId=identity_store_id, NextToken=next_token
            )
        else:
            response = identitystore_client.list_users(
                IdentityStoreId=identity_store_id
            )

        for user in response.get("Users", []):
            user_name = user.get("UserName", "")
            if "@" in user_name:
                usernames.add(user_name.split("@")[0].lower())

        next_token = response.get("NextToken")
        if not next_token:
            break

    return usernames


def main():
    profiles = list_profiles()

    print("\nProfiles to work on:")
    for profile in profiles:
        print(f"  - {profile}")

    print("\nFetching SSO usernames to determine migration...")
    sso_usernames = list_identity_store_usernames()
    print(f"Collected {len(sso_usernames)} SSO usernames.\n")

    all_users_data = []

    for profile in profiles:
        print(f"\nFetching IAM users for profile: {profile}")

        try:
            # Create session for that profile
            session = boto3.Session(profile_name=profile)

            # Get the account ID
            sts_client = session.client("sts")
            account_id = sts_client.get_caller_identity()["Account"]

            # List IAM users
            iam_users = list_iam_users(session)
            iam_client = session.client("iam")

            if iam_users:
                for user in iam_users:
                    user_name = user["UserName"]
                    user_arn = user["Arn"]
                    print(f"    Found user: {user_name}")

                    console_last_login = user.get("PasswordLastUsed")
                    access_key_last_used = get_user_access_keys_last_used(
                        iam_client, user_name
                    )
                    codecommit_last_used = get_codecommit_last_used(
                        iam_client, user_arn
                    )

                    is_migrated = "Yes" if user_name.lower() in sso_usernames else "No"

                    user_record = {
                        "Profile": profile,
                        "AccountId": account_id,
                        "UserName": user_name,
                        "CreateDate": user["CreateDate"].strftime("%Y-%m-%dT%H:%M:%S"),
                        "ConsoleLastLogin": (
                            console_last_login.strftime("%Y-%m-%dT%H:%M:%S")
                            if console_last_login
                            else "Never"
                        ),
                        "AccessKeyLastUsed": (
                            access_key_last_used.strftime("%Y-%m-%dT%H:%M:%S")
                            if access_key_last_used
                            else "Never"
                        ),
                        "CodeCommitLastUsed": (
                            codecommit_last_used.strftime("%Y-%m-%dT%H:%M:%S")
                            if codecommit_last_used
                            else "Never"
                        ),
                        "IsActive": is_user_active(
                            console_last_login,
                            access_key_last_used,
                            codecommit_last_used,
                        ),
                        "IsMigrated": is_migrated,
                    }

                    all_users_data.append(user_record)
            else:
                print(f"    No IAM users found for profile {profile}")

        except Exception as e:
            print(f"Error fetching users for profile {profile}: {e}")

    # Save to CSV
    if all_users_data:
        today = datetime.today().strftime("%Y-%m-%d")
        csv_filename = f"iam_users_all_profiles_{today}.csv"

        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = [
                "Profile",
                "AccountId",
                "UserName",
                "CreateDate",
                "ConsoleLastLogin",
                "AccessKeyLastUsed",
                "CodeCommitLastUsed",
                "IsActive",
                "IsMigrated",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users_data)

        print(f"\nIAM users list exported to {csv_filename}")
    else:
        print("\nNo users found across any profiles.")


if __name__ == "__main__":
    main()
