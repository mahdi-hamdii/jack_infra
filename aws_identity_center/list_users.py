import boto3
import csv
import sys
from datetime import datetime


def get_identity_store_id():
    """Retrieve the IdentityStoreId from the active SSO instance."""
    client = boto3.client("sso-admin")
    instances = client.list_instances()
    return instances["Instances"][0]["IdentityStoreId"]


def list_users(identity_store_id, manual_only=True):
    """List all users, filtering for manually created users if manual_only is True."""
    client = boto3.client("identitystore")
    users = []
    next_token = None

    while True:
        if next_token:
            response = client.list_users(
                IdentityStoreId=identity_store_id, NextToken=next_token
            )
        else:
            response = client.list_users(IdentityStoreId=identity_store_id)

        for user in response.get("Users", []):
            external_ids = user.get("ExternalIds", [])
            created_manually = not external_ids  # If no external IDs, user is manual
            if not manual_only or created_manually:
                users.append(
                    {
                        "UserName": user.get("UserName", ""),
                        "DisplayName": user.get("DisplayName", ""),
                        "Status": user.get("Status", ""),
                        "Manual": created_manually,
                    }
                )

        next_token = response.get("NextToken")
        if not next_token:
            break

    return users


def write_users_to_csv(users, filename=None, manual_only=True):
    """Write the list of manual users to a CSV file."""
    if not filename:
        today = datetime.today().strftime("%Y-%m-%d")
        prefix = "manual_users" if manual_only else "all_users"
        filename = f"{prefix}_{today}.csv"

    fieldnames = ["UserName", "DisplayName", "Status", "Manual"]
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)


def main():
    manual_only = True

    # Check if manual=false is passed as argument
    if len(sys.argv) > 1 and sys.argv[1].lower() == "manual=false":
        manual_only = False

    identity_store_id = get_identity_store_id()
    # manual_users = list_manual_users(identity_store_id)
    users = list_users(identity_store_id, manual_only=manual_only)

    write_users_to_csv(users, manual_only=manual_only)
    print(f"Exported {len(users)} users to CSV with today's date")


if __name__ == "__main__":
    main()
