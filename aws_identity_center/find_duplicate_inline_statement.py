import boto3
import json
import csv
from datetime import datetime
from collections import defaultdict

def list_permission_sets(sso_client, instance_arn):
    """List all permission sets."""
    response = sso_client.list_permission_sets(InstanceArn=instance_arn)
    return response.get("PermissionSets", [])

def get_permission_set_name(sso_client, instance_arn, permission_set_arn):
    """Get the name of a permission set."""
    response = sso_client.describe_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn
    )
    return response["PermissionSet"]["Name"]

def get_inline_policy(sso_client, instance_arn, permission_set_arn):
    """Retrieve the inline policy for a permission set."""
    response = sso_client.get_inline_policy_for_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn
    )
    return response.get("InlinePolicy")

def normalize_statement(stmt):
    """Simplify statement to focus only on Effect, Action, Resource, Condition."""
    normalized = {
        "Effect": stmt.get("Effect"),
        "Action": stmt.get("Action"),
        "Resource": stmt.get("Resource"),
        "Condition": stmt.get("Condition", {}),
    }
    return normalized

def actions_match(action1, action2):
    """Check if two actions match (exactly or wildcard)."""
    if action1 == action2:
        return "ExactMatch"
    if isinstance(action1, str) and isinstance(action2, str):
        service1, action1_part = action1.split(":", 1)
        service2, action2_part = action2.split(":", 1)
        if service1 == service2 and ("*" in [action1_part, action2_part]):
            return "WildcardMatch"
    return None

def resources_match(res1, res2):
    """Check if two resources match (exactly or wildcard-aware)."""
    if res1 == res2:
        return True
    if res1 == "*" or res2 == "*":
        return True
    return False

def find_duplicate_statements(policy_json):
    """Find duplicate statements inside a single inline policy."""
    if not policy_json:
        return []

    policy = json.loads(policy_json)
    statements = policy.get("Statement", [])
    normalized_statements = [normalize_statement(stmt) for stmt in statements]

    duplicates = []

    for i in range(len(normalized_statements)):
        for j in range(i + 1, len(normalized_statements)):
            s1 = normalized_statements[i]
            s2 = normalized_statements[j]

            match_type = actions_match(s1["Action"], s2["Action"])
            if not match_type:
                continue
            if s1["Effect"] != s2["Effect"]:
                continue
            if not resources_match(s1["Resource"], s2["Resource"]):
                continue
            if s1.get("Condition", {}) != s2.get("Condition", {}):
                continue

            duplicates.append((s1, s2, match_type))

    return duplicates

def main():
    sso_client = boto3.client("sso-admin")
    instances = sso_client.list_instances()
    if not instances["Instances"]:
        print("No SSO instances found.")
        return
    instance_arn = instances["Instances"][0]["InstanceArn"]

    permission_sets = list_permission_sets(sso_client, instance_arn)

    today = datetime.today().strftime("%Y-%m-%d")
    output_file = f"duplicate_inline_statements_{today}.csv"

    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["PermissionSetName", "MatchType", "DuplicateStatement1", "DuplicateStatement2"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for ps_arn in permission_sets:
            ps_name = get_permission_set_name(sso_client, instance_arn, ps_arn)
            inline_policy = get_inline_policy(sso_client, instance_arn, ps_arn)
            duplicates = find_duplicate_statements(inline_policy)

            for dup1, dup2, match_type in duplicates:
                writer.writerow({
                    "PermissionSetName": ps_name,
                    "MatchType": match_type,
                    "DuplicateStatement1": json.dumps(dup1),
                    "DuplicateStatement2": json.dumps(dup2),
                })

    print(f"✅ Duplicates report saved to {output_file}")

if __name__ == "__main__":
    main()
