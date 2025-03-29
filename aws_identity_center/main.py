import boto3
import sys
import ast

def list_permission_sets(instance_arn):
    """List all permission sets in the AWS IAM Identity Center"""
    client = boto3.client('sso-admin')
    permission_sets = []
    next_token = None

    while True:
        response = client.list_permission_sets(
            InstanceArn=instance_arn,
            NextToken=next_token
        ) if next_token else client.list_permission_sets(InstanceArn=instance_arn)

        permission_sets.extend(response.get('PermissionSets', []))
        next_token = response.get('NextToken')

        if not next_token:
            break

    return permission_sets

def get_permission_set_name(instance_arn, permission_set_arn):
    client = boto3.client('sso-admin')
    response = client.describe_permission_set(
        InstanceArn=instance_arn,
        PermissionSetArn=permission_set_arn
    )
    return response['PermissionSet'].get('Name', 'Unknown')

def get_principal_name(identity_store_id, principal_id, principal_type):
    client = boto3.client('identitystore')
    try:
        if principal_type == 'GROUP':
            response = client.describe_group(
                IdentityStoreId=identity_store_id,
                GroupId=principal_id
            )
            return response.get('DisplayName', 'Unknown Group')
        elif principal_type == 'USER':
            response = client.describe_user(
                IdentityStoreId=identity_store_id,
                UserId=principal_id
            )
            return response.get('UserName', 'Unknown User')
    except Exception as e:
        return f"Error retrieving name: {e}"

def get_permission_set_policies(instance_arn, permission_set_arn):
    """Retrieve managed and inline policies for a specific permission set"""
    client = boto3.client('sso-admin')

    managed_policies = []
    inline_policy = None

    # Get managed policies
    try:
        response = client.list_managed_policies_in_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        managed_policies = response.get('AttachedManagedPolicies', [])
    except Exception as e:
        print(f"Error retrieving managed policies: {e}")

    # Get inline policy
    try:
        response = client.get_inline_policy_for_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        inline_policy = response.get('InlinePolicy')
    except client.exceptions.ResourceNotFoundException:
        inline_policy = None

    return managed_policies, inline_policy

def list_permission_set_assignments(instance_arn, permission_set_arn):
    """List users and groups assigned to a permission set across all accounts"""
    sso_client = boto3.client('sso-admin')
    identitystore_client = boto3.client('identitystore')
    assignments = []

    # Get Identity Store ID using list_instances instead of describe_instance
    instances = sso_client.list_instances()
    identity_store_id = None
    for inst in instances['Instances']:
        if inst['InstanceArn'] == instance_arn:
            identity_store_id = inst['IdentityStoreId']
            break

    if identity_store_id is None:
        raise ValueError(f"IdentityStoreId not found for instance ARN: {instance_arn}")

    # First, list all accounts where the permission set is provisioned
    account_ids = []
    next_token = None
    while True:
        response = sso_client.list_accounts_for_provisioned_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn,
            NextToken=next_token
        ) if next_token else sso_client.list_accounts_for_provisioned_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )

        account_ids.extend(response.get('AccountIds', []))
        next_token = response.get('NextToken')

        if not next_token:
            break

    # Then list account assignments per account
    for account_id in account_ids:
        next_token = None
        while True:
            response = sso_client.list_account_assignments(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn,
                AccountId=account_id,
                NextToken=next_token
            ) if next_token else sso_client.list_account_assignments(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn,
                AccountId=account_id
            )

            for assignment in response.get('AccountAssignments', []):
                principal_name = get_principal_name(identity_store_id, assignment['PrincipalId'], assignment['PrincipalType'])
                assignment['PrincipalName'] = principal_name
                assignments.append(assignment)

            next_token = response.get('NextToken')
            if not next_token:
                break

    return assignments

def main():
    # Replace with your AWS IAM Identity Center Instance ARN
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"

    if len(sys.argv) < 2:
        print("Usage: python main.py ['policy1', 'policy2']")
        sys.exit(1)

    try:
        input_policies = ast.literal_eval(sys.argv[1])
        if not isinstance(input_policies, list):
            raise ValueError
        input_policies = [p.lower() for p in input_policies]
    except Exception:
        print("Error parsing policy list. Provide as: ['policy1', 'policy2']")
        sys.exit(1)

    permission_sets = list_permission_sets(instance_arn)
    print("Filtered Permission Sets (matching input policies):")
    for ps in permission_sets:
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)

        matched = False
        for policy in managed_policies:
            name = policy.get('Name', '').lower()
            arn = policy.get('Arn', '').lower()
            if any(p in name or p in arn for p in input_policies):
                matched = True
                break

        if matched:
            ps_name = get_permission_set_name(instance_arn, ps)
            print(f"\nPermission Set: {ps_name} ({ps})")
            print("Managed Policies:")
            for policy in managed_policies:
                print(f"  - {policy['Name']} ({policy['Arn']})")

            print("Inline Policy:")
            if inline_policy:
                print(inline_policy)
            else:
                print("  None")

            # Show assignments
            print("Assignments:")
            assignments = list_permission_set_assignments(instance_arn, ps)
            if assignments:
                for a in assignments:
                    print(f"  - {a['PrincipalType']}: {a['PrincipalName']} (Account: {a['AccountId']})")
            else:
                print("  None")

if __name__ == "__main__":
    main()
