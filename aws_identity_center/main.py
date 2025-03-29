import boto3

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
    """List users and groups assigned to a permission set"""
    client = boto3.client('sso-admin')
    assignments = []
    next_token = None

    while True:
        response = client.list_account_assignments(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn,
            NextToken=next_token
        ) if next_token else client.list_account_assignments(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )

        assignments.extend(response.get('AccountAssignments', []))
        next_token = response.get('NextToken')

        if not next_token:
            break

    return assignments

def main():
    # Replace with your AWS IAM Identity Center Instance ARN
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"

    permission_sets = list_permission_sets(instance_arn)
    print("Filtered Permission Sets (with IAM, SecretsManager, or Administrator Access):")
    for ps in permission_sets:
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)

        # Filter logic for IAM, SecretsManager, or AdministratorAccess
        matched = False
        for policy in managed_policies:
            name = policy.get('Name', '').lower()
            arn = policy.get('Arn', '').lower()
            if ('iamfullaccess' in name or 'iamfullaccess' in arn or
                'secretsmanagerreadwrite' in name or 'secretsmanagerreadwrite' in arn or
                'secretsmanagerfullaccess' in name or 'secretsmanagerfullaccess' in arn):
                matched = True
                break

        if matched:
            print(f"\nPermission Set ARN: {ps}")
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
                    print(f"  - {a['PrincipalType']}: {a['PrincipalId']} (Account: {a['AccountId']})")
            else:
                print("  None")

if __name__ == "__main__":
    main()
