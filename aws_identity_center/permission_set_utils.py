import boto3
import csv


def list_permission_sets(instance_arn):
    """List all permission sets in the AWS IAM Identity Center"""
    client = boto3.client("sso-admin")
    permission_sets = []
    next_token = None

    while True:
        response = (
            client.list_permission_sets(InstanceArn=instance_arn, NextToken=next_token)
            if next_token
            else client.list_permission_sets(InstanceArn=instance_arn)
        )
        permission_sets.extend(response.get("PermissionSets", []))
        next_token = response.get("NextToken")
        if not next_token:
            break
    return permission_sets


def get_permission_set_name(instance_arn, permission_set_arn):
    """Get the human-readable name of a permission set given its ARN."""
    client = boto3.client("sso-admin")
    response = client.describe_permission_set(
        InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
    )
    return response["PermissionSet"].get("Name", "Unknown")


def get_principal_name(identity_store_id, principal_id, principal_type):
    """Resolve a principal ID (user or group) to its display name."""
    client = boto3.client("identitystore")
    try:
        if principal_type == "GROUP":
            response = client.describe_group(
                IdentityStoreId=identity_store_id, GroupId=principal_id
            )
            return response.get("DisplayName", "Unknown Group")
        elif principal_type == "USER":
            response = client.describe_user(
                IdentityStoreId=identity_store_id, UserId=principal_id
            )
            return response.get("UserName", "Unknown User")
    except Exception as e:
        return f"Error retrieving name: {e}"


def get_permission_set_policies(instance_arn, permission_set_arn):
    """Get managed and inline policies attached to a permission set."""
    client = boto3.client("sso-admin")
    managed_policies = []
    inline_policy = None

    try:
        response = client.list_managed_policies_in_permission_set(
            InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
        )
        managed_policies = response.get("AttachedManagedPolicies", [])
    except Exception as e:
        print(f"Error retrieving managed policies: {e}")

    try:
        response = client.get_inline_policy_for_permission_set(
            InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
        )
        inline_policy = response.get("InlinePolicy")
    except client.exceptions.ResourceNotFoundException:
        inline_policy = None

    return managed_policies, inline_policy


def list_permission_set_assignments(instance_arn, permission_set_arn):
    """List all account assignments (users/groups) for a given permission set across all provisioned accounts."""
    sso_client = boto3.client("sso-admin")
    identitystore_client = boto3.client("identitystore")
    assignments = []

    instances = sso_client.list_instances()
    identity_store_id = None
    for inst in instances["Instances"]:
        if inst["InstanceArn"] == instance_arn:
            identity_store_id = inst["IdentityStoreId"]
            break

    if identity_store_id is None:
        raise ValueError(f"IdentityStoreId not found for instance ARN: {instance_arn}")

    account_ids = []
    next_token = None
    while True:
        response = (
            sso_client.list_accounts_for_provisioned_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn,
                NextToken=next_token,
            )
            if next_token
            else sso_client.list_accounts_for_provisioned_permission_set(
                InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
            )
        )
        account_ids.extend(response.get("AccountIds", []))
        next_token = response.get("NextToken")
        if not next_token:
            break

    for account_id in account_ids:
        next_token = None
        while True:
            response = (
                sso_client.list_account_assignments(
                    InstanceArn=instance_arn,
                    PermissionSetArn=permission_set_arn,
                    AccountId=account_id,
                    NextToken=next_token,
                )
                if next_token
                else sso_client.list_account_assignments(
                    InstanceArn=instance_arn,
                    PermissionSetArn=permission_set_arn,
                    AccountId=account_id,
                )
            )
            for assignment in response.get("AccountAssignments", []):
                principal_name = get_principal_name(
                    identity_store_id,
                    assignment["PrincipalId"],
                    assignment["PrincipalType"],
                )
                assignment["PrincipalName"] = principal_name
                assignment["AccountId"] = account_id
                assignments.append(assignment)

            next_token = response.get("NextToken")
            if not next_token:
                break

    return assignments


def write_to_csv(filename, rows):
    """Write the collected assignment details into a CSV file."""
    fieldnames = [
        "PermissionSetName",
        "PermissionSetArn",
        "ManagedPolicies",
        "InlinePolicy",
        "PrincipalType",
        "PrincipalName",
        "AccountId",
    ]
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
