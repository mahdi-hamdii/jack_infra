import boto3
import json
import os
import csv
from datetime import datetime


def list_permission_sets(sso_client, instance_arn):
    permission_sets = []
    next_token = None

    while True:
        if next_token:
            response = sso_client.list_permission_sets(
                InstanceArn=instance_arn,
                NextToken=next_token
            )
        else:
            response = sso_client.list_permission_sets(
                InstanceArn=instance_arn
            )

        permission_sets.extend(response.get("PermissionSets", []))
        next_token = response.get("NextToken")
        if not next_token:
            break

    return permission_sets


def get_permission_set_name(sso_client, instance_arn, permission_set_arn):
    response = sso_client.describe_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn,
    )
    return response["PermissionSet"]["Name"]


def get_inline_policy(sso_client, instance_arn, permission_set_arn):
    response = sso_client.get_inline_policy_for_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn,
    )
    return response.get("InlinePolicy")


def main():
    today = datetime.today().strftime("%Y-%m-%d")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"inline_policy_statements_count_{today}.csv")

    sso_client = boto3.client("sso-admin")
    instance_arn = sso_client.list_instances()["Instances"][0]["InstanceArn"]

    permission_sets = list_permission_sets(sso_client, instance_arn)
    print(f"[+] Using Instance ARN: {instance_arn}")
    print(f"[+] Found {len(permission_sets)} permission sets.\n")

    total_statements = 0
    detailed_counts = []

    for permission_set_arn in permission_sets:
        permission_set_name = get_permission_set_name(sso_client, instance_arn, permission_set_arn)
        inline_policy = get_inline_policy(sso_client, instance_arn, permission_set_arn)

        statement_count = 0

        if inline_policy:
            policy = json.loads(inline_policy)
            statements = policy.get("Statement", [])

            if isinstance(statements, dict):
                statements = [statements]  # single statement case

            statement_count = len(statements)
            total_statements += statement_count

        print(f"Permission Set: {permission_set_name} -> {statement_count} statements")

        detailed_counts.append({
            "PermissionSetName": permission_set_name,
            "StatementCount": statement_count
        })

    print(f"\n✅ Total statements across all permission sets: {total_statements}")

    # Save to CSV
    with open(output_filename, "w", newline="") as csvfile:
        fieldnames = ["PermissionSetName", "StatementCount"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_counts)

    print(f"[+] Detailed counts saved to {output_filename}")


if __name__ == "__main__":
    main()
