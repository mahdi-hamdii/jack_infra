import boto3
import csv
import argparse
import os
import configparser


def list_profiles_mapping():
    """Map AWS profiles to their account IDs based on SSO login."""
    config_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(config_path)

    profiles_mapping = {}

    for section in config.sections():
        if section.lower().strip().startswith("profile "):
            profile_name = section.strip().split("profile ", 1)[-1].strip()

            try:
                # Try creating session and fetching account ID
                session = boto3.Session(profile_name=profile_name)
                sts_client = session.client("sts")
                account_id = sts_client.get_caller_identity()["Account"]
                profiles_mapping[account_id] = profile_name
            except Exception as e:
                print(f"[!] Error getting account for profile {profile_name}: {e}")

    return profiles_mapping


def remove_console_login(iam_client, username):
    try:
        iam_client.delete_login_profile(UserName=username)
        print(f"[+] Console login removed for {username}")
    except iam_client.exceptions.NoSuchEntityException:
        print(f"[!] No console login found for {username}")
    except Exception as e:
        print(f"[!] Error removing console login for {username}: {e}")


def deactivate_access_keys(iam_client, username):
    try:
        response = iam_client.list_access_keys(UserName=username)
        access_keys = response["AccessKeyMetadata"]
        for key in access_keys:
            access_key_id = key["AccessKeyId"]
            iam_client.update_access_key(
                UserName=username, AccessKeyId=access_key_id, Status="Inactive"
            )
            print(f"[+] Access key {access_key_id} deactivated for {username}")
    except Exception as e:
        print(f"[!] Error deactivating access keys for {username}: {e}")


def deactivate_ssh_keys(iam_client, username):
    try:
        response = iam_client.list_ssh_public_keys(UserName=username)
        ssh_keys = response["SSHPublicKeys"]
        for key in ssh_keys:
            ssh_key_id = key["SSHPublicKeyId"]
            iam_client.update_ssh_public_key(
                UserName=username, SSHPublicKeyId=ssh_key_id, Status="Inactive"
            )
            print(f"[+] SSH public key {ssh_key_id} deactivated for {username}")
    except Exception as e:
        print(f"[!] Error deactivating SSH keys for {username}: {e}")


def process_users(csv_file_path, profiles_mapping):
    """Deactivate users based on the CSV and correct account/profile matching."""
    with open(csv_file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            raw_account_id = row.get("AccountId", "").strip()
            username = row.get("UserName", "").strip()

            # Normalize account ID
            account_id = raw_account_id.zfill(12)

            # Basic validations
            if not account_id.isdigit() or len(account_id) != 12:
                print(
                    f"[!] Skipping {username}: Invalid AccountId '{raw_account_id}' after normalization -> '{account_id}'"
                )
                continue

            if not username:
                print(f"[!] Skipping entry with missing username.")
                continue

            print(f"\nProcessing user: {username} in account {account_id}")

            profile = profiles_mapping.get(account_id)

            if not profile:
                print(
                    f"[!] No matching AWS profile found for account {account_id}. Skipping {username}."
                )
                continue

            try:
                session = boto3.Session(profile_name=profile)
                iam_client = session.client("iam")

                remove_console_login(iam_client, username)
                deactivate_access_keys(iam_client, username)
                deactivate_ssh_keys(iam_client, username)

            except Exception as e:
                print(
                    f"[!] Error processing user {username} in account {account_id}: {e}"
                )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Deactivate AWS IAM users from a CSV file"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to CSV file containing users with AccountId and UserName",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("[*] Mapping profiles to accounts...")
    profiles_mapping = list_profiles_mapping()

    print("[*] Profiles loaded:")
    for acc_id, prof in profiles_mapping.items():
        print(f"  - Account {acc_id} -> Profile {prof}")

    process_users(args.file, profiles_mapping)


if __name__ == "__main__":
    main()
