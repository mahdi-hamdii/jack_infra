import boto3
import sys
import ast
import csv


def list_permission_sets(instance_arn):
    """List all permission sets in the AWS IAM Identity Center"""

    client = boto3.client("sso-admin")
    permission_sets = []
    next_token = None

    # Paginate through all permission sets
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

    # Get managed policies attached to the permission set
    try:
        response = client.list_managed_policies_in_permission_set(
            InstanceArn=instance_arn, PermissionSetArn=permission_set_arn
        )
        managed_policies = response.get("AttachedManagedPolicies", [])
    except Exception as e:
        print(f"Error retrieving managed policies: {e}")

    # Get inline policy (if any) attached to the permission set
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

    # Fetch the IdentityStoreId required for resolving user/group names
    instances = sso_client.list_instances()
    identity_store_id = None
    for inst in instances["Instances"]:
        if inst["InstanceArn"] == instance_arn:
            identity_store_id = inst["IdentityStoreId"]
            break

    if identity_store_id is None:
        raise ValueError(f"IdentityStoreId not found for instance ARN: {instance_arn}")

    # Get all AWS account IDs where the permission set is provisioned
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

    # List all assignments for each account
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
                # Resolve the name of the assigned principal
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


def main():
    """Main script entry point."""

    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"

    # Validate CLI arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py ['policy1', 'policy2']")
        sys.exit(1)

    # Parse the policy list input safely using ast.literal_eval
    try:
        input_policies = ast.literal_eval(sys.argv[1])
        if not isinstance(input_policies, list):
            raise ValueError
        input_policies = [p.lower() for p in input_policies]
    except Exception:
        print("Error parsing policy list. Provide as: ['policy1', 'policy2']")
        sys.exit(1)

    # Fetch all permission sets
    permission_sets = list_permission_sets(instance_arn)
    print("Filtered Permission Sets (matching input policies):")

    # Dictionary to hold results per policy
    results_by_policy = {policy: [] for policy in input_policies}

    # Process each permission set
    for ps in permission_sets:
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)

        matched_policy_names = []

        # Check if any attached managed policies match the filter
        for policy in managed_policies:
            name = policy.get("Name", "").lower()
            arn = policy.get("Arn", "").lower()
            for input_policy in input_policies:
                if input_policy in name or input_policy in arn:
                    matched_policy_names.append(input_policy)

        # If any matching policy is found, collect info
        if matched_policy_names:
            ps_name = get_permission_set_name(instance_arn, ps)
            assignments = list_permission_set_assignments(instance_arn, ps)

            # If no user/group is assigned, still output the permission set
            if not assignments:
                for matched_policy in matched_policy_names:
                    results_by_policy[matched_policy].append(
                        {
                            "PermissionSetName": ps_name,
                            "PermissionSetArn": ps,
                            "ManagedPolicies": ", ".join(
                                [p["Name"] for p in managed_policies]
                            ),
                            "InlinePolicy": inline_policy if inline_policy else "None",
                            "PrincipalType": "",
                            "PrincipalName": "",
                            "AccountId": "",
                        }
                    )
            else:
                # Otherwise, add one row per assignment
                for assignment in assignments:
                    for matched_policy in matched_policy_names:
                        results_by_policy[matched_policy].append(
                            {
                                "PermissionSetName": ps_name,
                                "PermissionSetArn": ps,
                                "ManagedPolicies": ", ".join(
                                    [p["Name"] for p in managed_policies]
                                ),
                                "InlinePolicy": (
                                    inline_policy if inline_policy else "None"
                                ),
                                "PrincipalType": assignment["PrincipalType"],
                                "PrincipalName": assignment["PrincipalName"],
                                "AccountId": assignment["AccountId"],
                            }
                        )

    # Write each policy's assignments to a CSV file
    for policy, rows in results_by_policy.items():
        write_to_csv(f"{policy}.csv", rows)


if __name__ == "__main__":
    main()
