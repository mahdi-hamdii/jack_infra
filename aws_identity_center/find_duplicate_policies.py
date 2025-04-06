import boto3
import csv
import json
import os
import hashlib
from datetime import datetime
from collections import defaultdict
from itertools import combinations


def list_permission_sets(instance_arn):
    """List all permission sets in the AWS IAM Identity Center."""
    client = boto3.client('sso-admin')
    permission_sets = []
    next_token = None

    while True:
        response = (
            client.list_permission_sets(InstanceArn=instance_arn, NextToken=next_token)
            if next_token
            else client.list_permission_sets(InstanceArn=instance_arn)
        )
        permission_sets.extend(response.get('PermissionSets', []))
        next_token = response.get('NextToken')

        if not next_token:
            break

    return permission_sets


def get_permission_set_name(instance_arn, permission_set_arn):
    """Get the name of a permission set."""
    client = boto3.client('sso-admin')
    response = client.describe_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn
    )
    return response['PermissionSet'].get('Name', 'Unknown')


def get_inline_policy(instance_arn, permission_set_arn):
    """Retrieve the inline policy document (text) for a permission set."""
    client = boto3.client('sso-admin')

    try:
        response = client.get_inline_policy_for_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        return response.get('InlinePolicy')
    except client.exceptions.ResourceNotFoundException:
        return None


def get_managed_policies(instance_arn, permission_set_arn):
    """Retrieve managed policies attached to a permission set."""
    client = boto3.client('sso-admin')
    managed_policies = []

    try:
        response = client.list_managed_policies_in_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        managed_policies = response.get('AttachedManagedPolicies', [])
    except Exception as e:
        print(f"Error retrieving managed policies: {e}")

    return [p['Arn'] for p in managed_policies]


def save_duplicates_to_csv(data, filename, headers):
    """Utility function to save duplicates into a CSV."""
    os.makedirs("outputs", exist_ok=True)
    filepath = os.path.join("outputs", filename)

    with open(filepath, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    print(f"Saved results to {filepath}")


def extract_statements(policy_text):
    """Parse and return the list of statements from a policy text."""
    try:
        policy_data = json.loads(policy_text)
        statements = policy_data.get('Statement', [])
        if isinstance(statements, dict):
            statements = [statements]
        return statements
    except json.JSONDecodeError:
        print("Failed to decode policy JSON")
        return []


def detect_full_matches(policy_data_map):
    """Detect full matches between permission sets based on full inline policy hash."""
    seen_hashes = defaultdict(list)
    full_matches = []
    full_match_pairs = set()

    for ps_name, pdata in policy_data_map.items():
        seen_hashes[pdata["policy_hash"]].append(ps_name)

    for policy_hash, ps_names in seen_hashes.items():
        if len(ps_names) > 1:
            full_matches.append({
                "MatchType": "fullMatch",
                "PolicyHash": policy_hash,
                "PermissionSets": ", ".join(ps_names),
                "PolicyContent": policy_data_map[ps_names[0]]["policy_text"]
            })
            for ps1, ps2 in combinations(ps_names, 2):
                full_match_pairs.add(tuple(sorted([ps1, ps2])))

    return full_matches, full_match_pairs


def detect_partial_matches(policy_data_map, full_match_pairs):
    """Detect partial matches between permission sets based on common statements."""
    partial_matches = []
    checked_pairs = set()
    ps_names_list = list(policy_data_map.keys())

    for ps1, ps2 in combinations(ps_names_list, 2):
        pair = tuple(sorted([ps1, ps2]))
        if pair in checked_pairs or pair in full_match_pairs:
            continue

        stmts1 = policy_data_map[ps1]["statements"]
        stmts2 = policy_data_map[ps2]["statements"]

        common_statements = [stmt for stmt in stmts1 if stmt in stmts2]

        if common_statements:
            partial_matches.append({
                "MatchType": "partialMatch",
                "PolicyHash": f"{ps1}_{ps2}_partial",
                "PermissionSets": f"{ps1}, {ps2}",
                "PolicyContent": json.dumps(common_statements, indent=2)
            })

        checked_pairs.add(pair)

    return partial_matches


def main():
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"

    permission_sets = list_permission_sets(instance_arn)

    policy_data_map = {}  # ps_name -> { 'policy_text': str, 'policy_hash': str, 'statements': list }
    managed_policy_mapping = defaultdict(list)

    for ps in permission_sets:
        ps_name = get_permission_set_name(instance_arn, ps)

        # Get inline policy
        policy_text = get_inline_policy(instance_arn, ps)
        if policy_text:
            policy_hash = hashlib.md5(policy_text.encode('utf-8')).hexdigest()
            statements = extract_statements(policy_text)
            policy_data_map[ps_name] = {
                "policy_text": policy_text,
                "policy_hash": policy_hash,
                "statements": statements
            }

        # Get managed policies
        managed_policies = get_managed_policies(instance_arn, ps)
        for managed_policy_arn in managed_policies:
            managed_policy_mapping[managed_policy_arn].append(ps_name)

    # Detect full matches first
    full_matches, full_match_pairs = detect_full_matches(policy_data_map)

    # Then detect partial matches
    partial_matches = detect_partial_matches(policy_data_map, full_match_pairs)

    # Prepare duplicate managed policies
    duplicate_managed_data = []
    for managed_policy_arn, ps_names in managed_policy_mapping.items():
        if len(ps_names) > 1:
            duplicate_managed_data.append({
                "ManagedPolicyArn": managed_policy_arn,
                "PermissionSets": ", ".join(ps_names)
            })

    # Save results
    today = datetime.today().strftime("%Y-%m-%d")

    if full_matches or partial_matches:
        save_duplicates_to_csv(
            full_matches + partial_matches,
            f"duplicate_inline_policies_{today}.csv",
            headers=["MatchType", "PolicyHash", "PermissionSets", "PolicyContent"]
        )
    else:
        print("No duplicate inline policies found.")

    if duplicate_managed_data:
        save_duplicates_to_csv(
            duplicate_managed_data,
            f"duplicate_managed_policies_{today}.csv",
            headers=["ManagedPolicyArn", "PermissionSets"]
        )
    else:
        print("No duplicate managed policies found.")


if __name__ == "__main__":
    main()
