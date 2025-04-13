import boto3
import csv
import json
import os
import argparse
from datetime import datetime


def fetch_iam_managed_policies_from_groups(iam_client, group_names):
    """Fetch all managed policy ARNs attached to the specified IAM groups."""
    policies = set()

    for group_name in group_names:
        try:
            response = iam_client.list_attached_group_policies(GroupName=group_name)
            for policy in response.get("AttachedPolicies", []):
                policies.add(policy["PolicyArn"])
        except Exception as e:
            print(f"[!] Error fetching managed policies for group {group_name}: {e}")

    return policies


def fetch_iam_inline_policies_from_groups(iam_client, group_names):
    """Fetch all inline policy documents attached to the specified IAM groups."""
    policies = []

    for group_name in group_names:
        try:
            response = iam_client.list_group_policies(GroupName=group_name)
            for policy_name in response.get("PolicyNames", []):
                inline_policy = iam_client.get_group_policy(
                    GroupName=group_name, PolicyName=policy_name
                )
                policies.append(inline_policy["PolicyDocument"])
        except Exception as e:
            print(f"[!] Error fetching inline policies for group {group_name}: {e}")

    return policies


def fetch_permission_set_managed_policies(sso_admin_client, instance_arn, permission_set_arn):
    """Fetch managed policies attached to a permission set."""
    policies = set()

    try:
        response = sso_admin_client.list_managed_policies_in_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn,
        )
        for policy in response.get("AttachedManagedPolicies", []):
            policies.add(policy["PolicyArn"])
    except Exception as e:
        print(f"[!] Error fetching managed policies for permission set: {e}")

    return policies


def fetch_permission_set_inline_policy(sso_admin_client, instance_arn, permission_set_arn):
    """Fetch the inline policy document attached to a permission set."""
    try:
        response = sso_admin_client.get_inline_policy_for_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn,
        )
        policy = response.get("InlinePolicy")
        if policy:
            return json.loads(policy)
    except Exception as e:
        print(f"[!] Error fetching inline policy for permission set: {e}")

    return None


def load_permission_set_arn(sso_admin_client, instance_arn, permission_set_name):
    """Find the permission set ARN given its name."""
    paginator = sso_admin_client.get_paginator('list_permission_sets')
    for page in paginator.paginate(InstanceArn=instance_arn):
        for permission_set_arn in page.get('PermissionSets', []):
            desc = sso_admin_client.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn,
            )
            if desc["PermissionSet"]["Name"] == permission_set_name:
                return permission_set_arn

    raise Exception(f"[!] Permission set '{permission_set_name}' not found.")


def save_results_to_csv(missing_managed, missing_inline, permission_set_name):
    """Save missing policies to a CSV file inside outputs/ folder."""
    today = datetime.today().strftime("%Y-%m-%d")
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"missing_policies_{permission_set_name}_{today}.csv")

    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["Type", "PolicyNameOrArn"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for arn in missing_managed:
            writer.writerow({"Type": "ManagedPolicy", "PolicyNameOrArn": arn})
        for policy in missing_inline:
            writer.writerow({"Type": "InlinePolicy", "PolicyNameOrArn": json.dumps(policy)})

    print(f"\n[+] Results saved to: {filename}")


def compare_policies(group_managed, group_inline, ps_managed, ps_inline):
    """Compare policies between groups and permission set."""
    missing_managed = group_managed - ps_managed
    missing_inline = []

    if ps_inline:
        ps_inline_statements = ps_inline.get("Statement", [])
        if not isinstance(ps_inline_statements, list):
            ps_inline_statements = [ps_inline_statements]
    else:
        ps_inline_statements = []

    for group_policy in group_inline:
        group_statements = group_policy.get("Statement", [])
        if not isinstance(group_statements, list):
            group_statements = [group_statements]

        for stmt in group_statements:
            if stmt not in ps_inline_statements:
                missing_inline.append(stmt)

    return missing_managed, missing_inline


def parse_arguments():
    parser = argparse.ArgumentParser(description="Compare IAM group policies to a Permission Set")
    parser.add_argument("profile", help="AWS profile name to use for IAM Groups")
    parser.add_argument("groups_json", help="JSON array of IAM group names (e.g. '[\"Group1\", \"Group2\"]')")
    parser.add_argument("permission_set_name", help="Name of the Permission Set to check")
    return parser.parse_args()


def main():
    args = parse_arguments()

    print(f"\n[*] Using profile for IAM groups: {args.profile}")
    print(f"[*] Target Permission Set: {args.permission_set_name}")

    # Parse group names
    try:
        group_names = json.loads(args.groups_json)
        if not isinstance(group_names, list):
            raise ValueError
    except Exception:
        print(f"[!] Invalid format for groups. Must be a JSON list like '[\"Group1\", \"Group2\"]'")
        exit(1)

    print(f"[*] Groups to compare: {group_names}")

    # IAM session from passed profile
    iam_session = boto3.Session(profile_name=args.profile)
    iam_client = iam_session.client("iam")

    # SSO Admin client from current environment
    sso_admin_client = boto3.client("sso-admin")

    # Get SSO instance ARN
    instance_arn = sso_admin_client.list_instances()["Instances"][0]["InstanceArn"]
    print(f"[*] Using Identity Center Instance ARN: {instance_arn}")

    # Fetch policies from IAM groups
    group_managed_policies = fetch_iam_managed_policies_from_groups(iam_client, group_names)
    group_inline_policies = fetch_iam_inline_policies_from_groups(iam_client, group_names)

    # Fetch permission set details
    permission_set_arn = load_permission_set_arn(
        sso_admin_client, instance_arn, args.permission_set_name
    )

    ps_managed_policies = fetch_permission_set_managed_policies(
        sso_admin_client, instance_arn, permission_set_arn
    )
    ps_inline_policy = fetch_permission_set_inline_policy(
        sso_admin_client, instance_arn, permission_set_arn
    )

    # Compare policies
    missing_managed, missing_inline = compare_policies(
        group_managed_policies, group_inline_policies, ps_managed_policies, ps_inline_policy
    )

    print(f"\n[*] Missing Managed Policies: {len(missing_managed)}")
    print(f"[*] Missing Inline Statements: {len(missing_inline)}")

    save_results_to_csv(missing_managed, missing_inline, args.permission_set_name)


if __name__ == "__main__":
    main()
