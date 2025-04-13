import boto3
import json
import csv
import os
from datetime import datetime


def list_permission_sets(sso_client, instance_arn):
    """List all permission sets across all pages."""
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


def action_includes(action1, action2):
    if action1 == action2:
        return True

    if ":" not in action1 or ":" not in action2:
        print(f"[!] Invalid action format detected: {action1} or {action2}")
        return False

    service1, act1 = action1.split(":", 1)
    service2, act2 = action2.split(":", 1)

    if service1 != service2:
        return False

    if act1 == "*":
        return True  # s3:* covers any s3:Action

    if act2 == "*":
        return False  # s3:Action does not cover s3:* (inverse not true)

    return False


def actions_cover_each_other(actions1, actions2):
    if not isinstance(actions1, list):
        actions1 = [actions1]
    if not isinstance(actions2, list):
        actions2 = [actions2]

    # All actions in 2 must be covered by actions1
    for a2 in actions2:
        if not any(action_includes(a1, a2) for a1 in actions1):
            return False
    return True


def resource_covers(resource1, resource2):
    if resource1 == "*":
        return True

    if isinstance(resource1, str) and isinstance(resource2, str):
        return resource1 == resource2

    if isinstance(resource1, list) and isinstance(resource2, str):
        return resource2 in resource1

    if isinstance(resource1, str) and isinstance(resource2, list):
        return all(resource1 == r2 for r2 in resource2)

    if isinstance(resource1, list) and isinstance(resource2, list):
        return all(r2 in resource1 for r2 in resource2)

    return False


def statements_match(s1, s2):
    """Compare two statements for duplication."""
    try:
        if s1.get("Effect") != s2.get("Effect"):
            return False

        # Handle NotAction detection
        if "NotAction" in s1 or "NotAction" in s2:
            return "NeedsManualCheck"

        if actions_cover_each_other(s1.get("Action"), s2.get("Action")) and \
           resource_covers(s1.get("Resource"), s2.get("Resource")):
            return True

        return False

    except Exception as e:
        print("\n⚠️ Error while matching two statements!")
        print(f"Statement 1: {json.dumps(s1, indent=2)}")
        print(f"Statement 2: {json.dumps(s2, indent=2)}")
        raise e


def find_duplicate_statements(inline_policy_json):
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
                continue

            key = tuple(sorted([json.dumps(s1, sort_keys=True), json.dumps(s2, sort_keys=True)]))
            if key in checked_pairs:
                continue

            checked_pairs.add(key)

            if s1 == s2:
                match_type = "ExactMatch"
            else:
                match_result = statements_match(s1, s2)
                if match_result == True:
                    match_type = "WildcardMatch"
                elif match_result == "NeedsManualCheck":
                    match_type = "NotActionCheckRequired"
                else:
                    continue

            duplicates.append((match_type, s1, s2))

    return duplicates


def main():
    today = datetime.today().strftime("%Y-%m-%d")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"duplicate_inline_statements_{today}.csv")

    sso_client = boto3.client("sso-admin")
    instance_arn = sso_client.list_instances()["Instances"][0]["InstanceArn"]

    permission_sets = list_permission_sets(sso_client, instance_arn)
    print(f"[+] Using Instance ARN: {instance_arn}")
    print(f"[+] Found {len(permission_sets)} permission sets.")

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


if __name__ == "__main__":
    main()
