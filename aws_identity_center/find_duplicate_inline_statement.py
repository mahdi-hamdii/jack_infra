import boto3
import json
import csv
import os
from datetime import datetime


def list_permission_sets(sso_client, instance_arn):
    """List all permission sets."""
    response = sso_client.list_permission_sets(InstanceArn=instance_arn)
    return response["PermissionSets"]


def get_permission_set_name(sso_client, instance_arn, permission_set_arn):
    """Get the name of a permission set."""
    response = sso_client.describe_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn,
    )
    return response["PermissionSet"]["Name"]


def get_inline_policy(sso_client, instance_arn, permission_set_arn):
    """Fetch the inline policy of a permission set."""
    response = sso_client.get_inline_policy_for_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn,
    )
    return response.get("InlinePolicy")


def actions_match(action1, action2):
    """Check if two actions match (exact or wildcard). Print invalid actions if detected."""
    if action1 == action2:
        return True

    actions1 = action1 if isinstance(action1, list) else [action1]
    actions2 = action2 if isinstance(action2, list) else [action2]

    for a1 in actions1:
        if ":" not in a1:
            print(f"[!] Warning: action missing service prefix (':') -> '{a1}'")
            continue
        service1, action_part1 = a1.split(":", 1)

        for a2 in actions2:
            if ":" not in a2:
                print(f"[!] Warning: action missing service prefix (':') -> '{a2}'")
                continue
            service2, action_part2 = a2.split(":", 1)

            if service1 == service2:
                return True
            if a1 == a2:
                return True

    return False


def resource_covers(resource1, resource2):
    """Check if resource1 covers resource2."""
    if resource1 == "*" or resource1 == resource2:
        return True
    if isinstance(resource1, list) and resource2 in resource1:
        return True
    return False


def statements_match(s1, s2):
    """Check if two statements match."""
    try:
        if s1["Effect"] != s2["Effect"]:
            return False

        if not actions_match(s1["Action"], s2["Action"]):
            return False

        if not resource_covers(s1["Resource"], s2["Resource"]):
            return False

        return True

    except Exception as e:
        print("\n⚠️ Error while matching two statements!")
        print(f"Statement 1: {json.dumps(s1, indent=2)}")
        print(f"Statement 2: {json.dumps(s2, indent=2)}")
        raise e


def find_duplicate_statements(inline_policy_json):
    """Find duplicate or covered statements inside an inline policy."""
    duplicates = []
    if not inline_policy_json:
        return duplicates

    policy = json.loads(inline_policy_json)
    statements = policy.get("Statement", [])

    if not isinstance(statements, list):
        statements = [statements]

    checked_pairs = set()

    for i, s1 in enumerate(statements):
        for j, s2 in enumerate(statements):
            if i >= j:
                continue  # Don't compare same or already compared

            key = tuple(sorted([json.dumps(s1, sort_keys=True), json.dumps(s2, sort_keys=True)]))
            if key in checked_pairs:
                continue

            checked_pairs.add(key)

            if s1 == s2:
                match_type = "ExactMatch"
            elif statements_match(s1, s2):
                match_type = "WildcardMatch"
            else:
                continue

            duplicates.append((match_type, s1, s2))

    return duplicates


def main():
    today = datetime.today().strftime("%Y-%m-%d")
    output_filename = f"duplicate_inline_statements_{today}.csv"

    sso_client = boto3.client("sso-admin")
    instance_arn = sso_client.list_instances()["Instances"][0]["InstanceArn"]

    permission_sets = list_permission_sets(sso_client, instance_arn)
    print(f"[+] Using Instance ARN: {instance_arn}")
    print(f"[+] Found {len(permission_sets)} permission sets.")
    for ps in permission_sets:
        print(f"    - {ps}")
    with open(output_filename, "w", newline="") as csvfile:
        fieldnames = ["PermissionSetName", "MatchType", "DuplicateStatement1", "DuplicateStatement2"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for permission_set_arn in permission_sets:
            permission_set_name = get_permission_set_name(sso_client, instance_arn, permission_set_arn)
            inline_policy = get_inline_policy(sso_client, instance_arn, permission_set_arn)

            if not inline_policy:
                continue

            duplicates = find_duplicate_statements(inline_policy)

            for match_type, dup1, dup2 in duplicates:
                writer.writerow({
                    "PermissionSetName": permission_set_name,
                    "MatchType": match_type,
                    "DuplicateStatement1": json.dumps(dup1),
                    "DuplicateStatement2": json.dumps(dup2),
                })

    print(f"[+] Duplicates saved to {output_filename}")
