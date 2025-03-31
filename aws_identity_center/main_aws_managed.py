import sys
import ast
from permission_set_utils import (
    list_permission_sets,
    get_permission_set_name,
    get_permission_set_policies,
    list_permission_set_assignments,
    write_to_csv,
)


def main():
    """Main script for listing permission set assignments based on AWS managed policies."""
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"

    # Validate CLI arguments
    if len(sys.argv) < 2:
        print("Usage: python main_aws_managed.py ['policy1', 'policy2']")
        sys.exit(1)

    # Parse policy names from CLI
    try:
        input_policies = ast.literal_eval(sys.argv[1])
        if not isinstance(input_policies, list):
            raise ValueError
        input_policies = [p.lower() for p in input_policies]
    except Exception:
        print("Error parsing policy list. Provide as: ['policy1', 'policy2']")
        sys.exit(1)

    # Get all permission sets
    permission_sets = list_permission_sets(instance_arn)
    print("Filtered Permission Sets (matching input policies):")

    # Dictionary to store results by policy
    results_by_policy = {policy: [] for policy in input_policies}

    # Loop through each permission set and check if it matches
    for ps in permission_sets:
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)
        matched_policy_names = []

        for policy in managed_policies:
            name = policy.get("Name", "").lower()
            arn = policy.get("Arn", "").lower()
            for input_policy in input_policies:
                if input_policy in name or input_policy in arn:
                    matched_policy_names.append(input_policy)

        if matched_policy_names:
            ps_name = get_permission_set_name(instance_arn, ps)
            assignments = list_permission_set_assignments(instance_arn, ps)

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

    # Write to CSV
    for policy, rows in results_by_policy.items():
        write_to_csv(f"{policy}.csv", rows)


if __name__ == "__main__":
    main()
