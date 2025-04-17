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


def is_s3_client_valid(session, profile):
    try:
        s3_client = session.client("s3")

        # Test list buckets
        s3_client.list_buckets()

        # Verify identity
        sts_client = session.client("sts")
        identity = sts_client.get_caller_identity()
        print(f"[+] Authenticated as: {identity['Arn']}")

        return s3_client

    except botocore.exceptions.NoCredentialsError:
        print(f"[!] No credentials found for profile: {profile}")
    except botocore.exceptions.PartialCredentialsError:
        print(f"[!] Incomplete credentials for profile: {profile}")
    except botocore.exceptions.ClientError as e:
        print(f"[!] ClientError for profile {profile}: {e}")
    except Exception as e:
        print(f"[!] Unexpected error for profile {profile}: {e}")
    
    return None


def check_s3_public_access(profile):
    print(f"[*] Creating session for profile: {profile}")
    session = boto3.Session(profile_name=profile)
    s3_client = is_s3_client_valid(session, profile)

    if not s3_client:
        print(f"[!] Skipping profile {profile} due to client issues.")
        return []

    results = []

    try:
        buckets = s3_client.list_buckets()["Buckets"]
        for bucket in buckets:
            bucket_name = bucket["Name"]
            bucket_arn = f"arn:aws:s3:::{bucket_name}"

            if hasattr(s3_client, "get_public_access_block"):
                try:
                    pab = s3_client.get_public_access_block(Bucket=bucket_name)
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
                    print(f"[!] Unexpected error on bucket {bucket_name}: {e}")
            else:
                print(f"[!] Method 'get_public_access_block' is not available for this s3 client.")
                results.append({
                    "Account": profile,
                    "BucketArn": bucket_arn,
                    "Reason": "Client lacks get_public_access_block"
                })

    except Exception as e:
        print(f"[!] Error while listing buckets for profile {profile}: {e}")

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
