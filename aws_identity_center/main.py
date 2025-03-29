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

def main():
    # Replace with your AWS IAM Identity Center Instance ARN
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"

    permission_sets = list_permission_sets(instance_arn)
    print("Permission Sets:")
    for ps in permission_sets:
        print(f"\nPermission Set ARN: {ps}")
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)

        print("Managed Policies:")
        if managed_policies:
            for policy in managed_policies:
                print(f"  - {policy['Name']} ({policy['Arn']})")
        else:
            print("  None")

        print("Inline Policy:")
        if inline_policy:
            print(inline_policy)
        else:
            print("  None")

if __name__ == "__main__":
    main()
