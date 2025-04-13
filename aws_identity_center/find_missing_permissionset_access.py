import boto3
import argparse
import csv
import json
from datetime import datetime
from botocore.exceptions import ClientError


def get_iam_group_policies(iam_client, group_names):
    group_managed_policies = set()
    group_inline_policies = set()

    for group in group_names:
        # Managed policies
        attached = iam_client.list_attached_group_policies(GroupName=group)
        for policy in attached.get("AttachedPolicies", []):
            group_managed_policies.add(policy["PolicyArn"])

        # Inline policies
        inline = iam_client.list_group_policies(GroupName=group)
        for policy_name in inline.get("PolicyNames", []):
            group_inline_policies.add(policy_name)

    return group_managed_policies, group_inline_policies


def get_permission_set_policies(sso_admin_client, instance_arn, permission_set_name):
    managed_policies = set()
    inline_policy_names = set()

    # Find the ARN of the permission set by name
    paginator = sso_admin_client.get_paginator("list_permission_sets")
    permission_set_arn = None
    for page in paginator.paginate(InstanceArn=instance_arn):
        for ps_arn in page["PermissionSets"]:
            desc = sso_admin_client.describe_permission_set(
                InstanceArn=instance_arn, PermissionSetArn=ps_arn
            )
            if desc["PermissionSet"]["Name"] == permission_set_name:
                permission_set_arn = ps_arn
                break

    if not permission_set_arn:
        raise Exception(f"Permission set '{permission_set_name}' not found")

    # Get attached managed policies
    response = sso_admin_client.list_managed_policies_in_permission_set(
        InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
    )
    for policy in response.get("AttachedManagedPolicies", []):
        managed_policies.add(policy["PolicyArn"])

    # Get inline policy (we'll just parse the statement names)
    try:
        inline_resp = sso_admin_client.get_inline_policy_for_permission_set(
            InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
        )
        if inline_resp.get("InlinePolicy"):
            inline = json.loads(inline_resp["InlinePolicy"])
            statements = inline.get("Statement", [])
            if not isinstance(statements, list):
                statements = [statements]
            for stmt in statements:
                inline_policy_names.add(json.dumps(stmt, sort_keys=True))
    except ClientError:
        pass

    return managed_policies, inline_policy_names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", help="AWS profile name")
    parser.add_argument("groups", type=json.loads, help="List of IAM groups")
    parser.add_argument("permission_set", help="Permission Set Name")
    args = parser.parse_args()

    # Create sessions
    session = boto3.Session(profile_name=args.profile)
    iam_client = session.client("iam")
    sso_admin_client = session.client("sso-admin")

    # Get identity store
    instance_arn = sso_admin_client.list_instances()["Instances"][0]["InstanceArn"]

    # Get IAM group policies
    group_managed, group_inline = get_iam_group_policies(iam_client, args.groups)

    # Get permission set policies
    ps_managed, ps_inline = get_permission_set_policies(
        sso_admin_client, instance_arn, args.permission_set
    )

    # Diff
    managed_to_add = group_managed - ps_managed
    inline_to_add = group_inline - ps_inline

    # Output CSV
    today = datetime.today().strftime("%Y-%m-%d")
    csv_file = f"iam_to_permissionset_diff_{today}.csv"

    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Policy"])
        for m in managed_to_add:
            writer.writerow(["Managed", m])
        for i in inline_to_add:
            writer.writerow(["Inline", i])

    print(f"\n✅ Differences saved to {csv_file}")


if __name__ == "__main__":
    main()
