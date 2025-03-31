# This file is responsible for managed Policies, which are 2 types:
#   - AWS Managed policies: Predefined by AWS (e.g., AdministratorAccess, AmazonS3ReadOnlyAccess)
#   - Customer Managed Policies: Policies that you create and manage in your account


import sys
import ast
from permission_set_utils import (
    list_permission_sets,
    get_permission_set_name,
    get_permission_set_policies,
    list_permission_set_assignments,
    write_to_csv,
)


def parse_policy_list():
    """Parse and validate the list of policies from CLI arguments."""
    if len(sys.argv) < 2:
        print("Usage: python main_aws_managed.py ['policy1', 'policy2']")
        sys.exit(1)

    try:
        input_policies = ast.literal_eval(sys.argv[1])
        if not isinstance(input_policies, list):
            raise ValueError
        return [p.lower() for p in input_policies]
    except Exception:
        print("Error parsing policy list. Provide as: ['policy1', 'policy2']")
        sys.exit(1)


def collect_permission_set_data(instance_arn, input_policies):
    """Collect relevant permission set assignment data for matched managed policies."""
    permission_sets = list_permission_sets(instance_arn)
    results_by_policy = {policy: [] for policy in input_policies}

    for ps in permission_sets:
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)
        matched_policy_names = [
            input_policy
            for input_policy in input_policies
            for policy in managed_policies
            if input_policy in policy.get("Name", "").lower()
            or input_policy in policy.get("Arn", "").lower()
        ]

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

    return results_by_policy


def main():
    """Main script for listing permission set assignments based on AWS managed policies."""
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"
    input_policies = parse_policy_list()
    results_by_policy = collect_permission_set_data(instance_arn, input_policies)

    print("Filtered Permission Sets (matching input policies):")
    for policy, rows in results_by_policy.items():
        write_to_csv(f"{policy}.csv", rows)


if __name__ == "__main__":
    main()
