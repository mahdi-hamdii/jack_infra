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

def get_permission_set_policy(instance_arn, permission_set_arn):
    """Retrieve the inline policy for a specific permission set"""
    client = boto3.client('sso-admin')
    
    try:
        response = client.get_permissions_boundary_for_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn
        )
        return response.get('PermissionsBoundary', {}).get('Policy', 'No policy attached')
    except client.exceptions.ResourceNotFoundException:
        return 'No policy attached'

def main():
    # Replace with your AWS IAM Identity Center Instance ARN
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"
    
    permission_sets = list_permission_sets(instance_arn)
    print("Permission Sets:")
    for ps in permission_sets:
        print(f"\nPermission Set ARN: {ps}")
        policy = get_permission_set_policy(instance_arn, ps)
        print(f"Policy: {policy}")

if __name__ == "__main__":
    main()
