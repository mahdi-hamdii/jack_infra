import boto3
import csv
import json
from datetime import datetime
from collections import defaultdict

def list_permission_sets(sso_client, instance_arn):
    response = sso_client.list_permission_sets(InstanceArn=instance_arn)
    return response["PermissionSets"]

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

def normalize_statement(stmt):
    """Create a normalized dict for easier comparison."""
    return {
        "Effect": stmt.get("Effect", ""),
        "Action": stmt.get("Action", ""),
        "Resource": stmt.get("Resource", "*"),
        "Condition": stmt.get("Condition", {}),
    }

def actions_match(action1, action2):
    """Determine if two actions match exactly or via wildcard."""
    if action1 == action2:
        return True
    if "*" in action1:
        service1, _ = action1.split(":", 1)
        service2, action2_part = action2.split(":", 1)
        return service1 == service2
    if "*" in action2:
        service2, _ = action2.split(":", 1)
        service1, action1_part = action1.split(":", 1)
        return service1 == service2
    return False

def resource_covers(resource1, resource2):
    """True if resource1 covers resource2 (wildcard)."""
    if resource1 == resource2:
        return True
    if resource1 == "*":
        return True
    if resource1.endswith("*") and resource2.startswith(resource1[:-1]):
        return True
    return False

def statements_match(stmt1, stmt2):
    """Enhanced matching logic."""
    s1 = normalize_statement(stmt1)
    s2 = normalize_statement(stmt2)

    if s1["Effect"] != s2["Effect"]:
        return False

    if actions_match(s1["Action"], s2["Action"]) and resource_covers(s1["Resource"], s2["Resource"]):
        return True

    return False

def find_duplicate_statements(policy_json):
    """Find duplicate statements inside a policy document."""
    if not policy_json:
        return []

    policy = json.loads(policy_json)
    statements = policy.get("Statement", [])

    duplicates = []

    for i in range(len(statements)):
        for j in range(i + 1, len(statements)):
            s1 = normalize_statement(statements[i])
            s2 = normalize_statement(statements[j])

            # Priority 1: Exact match
            if (
                s1["Effect"] == s2["Effect"]
                and s1["Action"] == s2["Action"]
                and s1["Resource"] == s2["Resource"]
                and s1["Condition"] == s2["Condition"]
            ):
                duplicates.append(("ExactMatch", statements[i], statements[j]))
            # Priority 2: Wildcard match
            elif statements_match(statements[i], statements[j]):
                duplicates.append(("WildcardMatch", statements[i], statements[j]))

    return duplicates
def main():
    today = datetime.today().strftime("%Y-%m-%d")
    output_file = f"duplicate_inline_statements_{today}.csv"

    sso_admin = boto3.client("sso-admin")
    instances = sso_admin.list_instances()
    instance_arn = instances["Instances"][0]["InstanceArn"]

    permission_sets = list_permission_sets(sso_admin, instance_arn)

    results = []

    for ps_arn in permission_sets:
        name = get_permission_set_name(sso_admin, instance_arn, ps_arn)
        policy = get_inline_policy(sso_admin, instance_arn, ps_arn)

        if not policy:
            continue

        duplicates = find_duplicate_statements(policy)

        for match_type, dup1, dup2 in duplicates:
            results.append({
                "PermissionSetName": name,
                "MatchType": match_type,
                "DuplicateStatement1": json.dumps(normalize_statement(dup1)),
                "DuplicateStatement2": json.dumps(normalize_statement(dup2)),
            })

    if results:
        with open(output_file, "w", newline="") as csvfile:
            fieldnames = ["PermissionSetName", "MatchType", "DuplicateStatement1", "DuplicateStatement2"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"[+] Duplicates saved to {output_file}")
    else:
        print("[+] No duplicates found.")

if __name__ == "__main__":
    main()
