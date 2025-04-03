import boto3
import csv

def get_identity_store_id():
    """Retrieve the IdentityStoreId from the active SSO instance."""
    client = boto3.client("sso-admin")
    instances = client.list_instances()
    return instances["Instances"][0]["IdentityStoreId"]

def list_manual_users(identity_store_id):
    """List all users that are manually created (not from SCIM) and include their active status."""
    client = boto3.client("identitystore")
    users = []
    next_token = None

    while True:
        if next_token:
            response = client.list_users(
                IdentityStoreId=identity_store_id,
                NextToken=next_token
            )
        else:
            response = client.list_users(
                IdentityStoreId=identity_store_id
            )

        for user in response.get("Users", []):
            external_ids = user.get("ExternalIds", [])
            created_manually = not external_ids  # If no external IDs, user is manual
            users.append({
                "UserName": user.get("UserName", ""),
                "DisplayName": user.get("DisplayName", ""),
                "Status": user.get("Status", ""),
                "Manual": created_manually
            })

        next_token = response.get("NextToken")
        if not next_token:
            break

    return [u for u in users if u["Manual"]]

def write_users_to_csv(users, filename="manual_users.csv"):
    """Write the list of manual users to a CSV file."""
    fieldnames = ["UserName", "DisplayName", "Status", "Manual"]
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

def main():
    identity_store_id = get_identity_store_id()
    manual_users = list_manual_users(identity_store_id)
    write_users_to_csv(manual_users)
    print(f"Exported {len(manual_users)} manually created users to manual_users.csv")

if __name__ == "__main__":
    main()
