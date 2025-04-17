import boto3
import os
import csv
import configparser
from datetime import datetime


def list_profiles():
    config_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(config_path)

    profiles = []
    for section in config.sections():
        if section.lower().strip().startswith("profile "):
            profile_name = section.strip().split("profile ", 1)[-1].strip()
            profiles.append(profile_name)
    return profiles


def get_account_id(session):
    try:
        sts = session.client("sts")
        return sts.get_caller_identity()["Account"]
    except Exception:
        return "Unknown"


def check_s3_public_access(profile):
    session = boto3.Session(profile_name=profile)
    s3_client = session.client("s3")
    account_id = get_account_id(session)

    results = []
    try:
        buckets = s3_client.list_buckets()["Buckets"]
        for bucket in buckets:
            bucket_name = bucket["Name"]
            bucket_arn = f"arn:aws:s3:::{bucket_name}"
            try:
                policy_status = s3_client.get_bucket_policy_status(Bucket=bucket_name)
                if policy_status["PolicyStatus"].get("IsPublic"):
                    results.append({
                        "Account": profile,
                        "BucketArn": bucket_arn,
                        "Reason": "Bucket policy allows public access"
                    })
                    continue
            except s3_client.exceptions.ClientError:
                pass

            try:
                access_block = s3_client.get_bucket_public_access_block(Bucket=bucket_name)
                if not all(access_block["PublicAccessBlockConfiguration"].values()):
                    results.append({
                        "Account": profile,
                        "BucketArn": bucket_arn,
                        "Reason": "Block public access not fully enabled"
                    })
            except s3_client.exceptions.NoSuchPublicAccessBlockConfiguration:
                results.append({
                    "Account": profile,
                    "BucketArn": bucket_arn,
                    "Reason": "No block public access config"
                })

    except Exception as e:
        print(f"[!] Error for profile {profile}: {e}")
    return results


def save_to_csv(results):
    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/public_s3_buckets_{datetime.today().strftime('%Y-%m-%d')}.csv"
    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["Account", "BucketArn", "Reason"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[+] Results saved to: {filename}")


def main():
    profiles = list_profiles()
    print("[*] Checking all profiles for S3 public access issues...\n")

    all_results = []
    for profile in profiles:
        print(f"  → Checking profile: {profile}")
        issues = check_s3_public_access(profile)
        all_results.extend(issues)

    if all_results:
        save_to_csv(all_results)
    else:
        print("All buckets have block public access enabled across all profiles.")


if __name__ == "__main__":
    main()
