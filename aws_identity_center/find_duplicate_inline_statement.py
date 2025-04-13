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
    if action1 == "*" or action2 == "*":
        return True

    if action1 == action2:
        return True

    if ":" not in action1 or ":" not in action2:
        print(f"[!] Warning: unexpected action format -> '{action1}' or '{action2}'")
        return False

    service1, act1 = action1.split(":", 1)
    service2, act2 = action2.split(":", 1)

    if service1 != service2:
        return False

    if act1 == "*":
        return True  # Example: s3:* covers s3:GetObject

    if act2 == "*":
        return False  # Example: s3:GetObject does not cover s3:*

    return False


def actions_cover_each_other(actions1, actions2):
    if not isinstance(actions1, list):
        actions1 = [actions1]
    if not isinstance(actions2, list):
        actions2 = [actions2]

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


def extract_action_or_notaction(statement):
    """Return tuple (key_type, actions), where key_type is 'Action' or 'NotAction'."""
    if "Action" in statement:
        return "Action", statement.get("Action")
    elif "NotAction" in statement:
        return "NotAction", statement.get("NotAction")
    else:
        return None, None


def statements_match(s1, s2):
    try:
        if s1.get("Effect") != s2.get("Effect"):
            return False

        key1, actions1 = extract_action_or_notaction(s1)
        key2, actions2 = extract_action_or_notaction(s2)

        if key1 is None or key2 is None:
            print(f"[!] Warning: One of the statements is missing both Action and NotAction. Skipping.")
            return False

        if key1 != key2:
            return False  # Cannot match Action with NotAction

        if not actions_cover_each_other(actions1, actions2):
            return False

        if not resource_covers(s1.get("Resource"), s2.get("Resource")):
            return False

        return True

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
            elif statements_match(s1, s2):
                match_type = "WildcardMatch"
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
