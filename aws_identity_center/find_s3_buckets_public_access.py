import boto3
import botocore
import csv
import os
from datetime import datetime
import configparser


def list_profiles():
    config_path = os.path.expanduser("~/.aws/config")
    config = configparser.ConfigParser()
    config.read(config_path)

    profiles = []
    for section in config.sections():
        if section.startswith("profile "):
            profiles.append(section.split("profile ", 1)[1])
        elif section == "default":
            profiles.append("default")
    return profiles


def check_s3_public_access(profile):
    session = boto3.Session(profile_name=profile)
    s3_client = session.client("s3")
    results = []

    try:
        buckets = s3_client.list_buckets()["Buckets"]
        for bucket in buckets:
            bucket_name = bucket["Name"]
            bucket_arn = f"arn:aws:s3:::{bucket_name}"

            try:
                pab = s3_client.get_bucket_public_access_block(Bucket=bucket_name)
                pab_config = pab.get("PublicAccessBlockConfiguration", {})

                if not all(pab_config.values()):
                    results.append({
                        "Account": profile,
                        "BucketArn": bucket_arn,
                        "Reason": "Block public access not fully enabled"
                    })
            except botocore.exceptions.ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "NoSuchPublicAccessBlockConfiguration":
                    results.append({
                        "Account": profile,
                        "BucketArn": bucket_arn,
                        "Reason": "No block public access config"
                    })
                else:
                    print(f"[!] Error checking bucket {bucket_name}: {e}")

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
        for row in results:
            writer.writerow(row)
    print(f"\n[+] Results written to {filename}")


def main():
    print("[*] Checking all profiles for S3 public access issues...")
    profiles = list_profiles()
    all_results = []

    for profile in profiles:
        print(f"\n--> Checking profile: {profile}")
        results = check_s3_public_access(profile)
        all_results.extend(results)

    if all_results:
        save_to_csv(all_results)
    else:
        print("[+] No public access issues found.")


if __name__ == "__main__":
    main()