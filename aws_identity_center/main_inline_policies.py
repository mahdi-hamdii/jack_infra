# This file is responsible for inline Policies, which are:
#   - Embedded directly into a specific IAM identity or SSO permission set

import sys
import ast
from permission_set_utils import (
    list_permission_sets,
    get_permission_set_name,
    get_permission_set_policies,
    list_permission_set_assignments,
    write_to_csv,
)


def parse_inline_filter():
    """Parse and validate the list of keywords to search inside inline policies."""
    if len(sys.argv) < 2:
        print("Usage: python main_aws_inline.py ['keyword1', 'keyword2']")
        sys.exit(1)

    try:
        inline_keywords = ast.literal_eval(sys.argv[1])
        if not isinstance(inline_keywords, list):
            raise ValueError
        return [k.lower() for k in inline_keywords]
    except Exception:
        print(
            "Error parsing inline policy keywords. Provide as: ['keyword1', 'keyword2']"
        )
        sys.exit(1)


def inline_policy_matches(inline_policy, keywords):
    """Check if any keyword exists in the inline policy JSON string."""
    if not inline_policy:
        return False
    policy_str = str(inline_policy).lower()
    return any(keyword in policy_str for keyword in keywords)


def collect_inline_permission_set_data(instance_arn, keywords):
    """Collect data for permission sets where inline policy matches any of the keywords."""
    permission_sets = list_permission_sets(instance_arn)
    results = []

    for ps in permission_sets:
        managed_policies, inline_policy = get_permission_set_policies(instance_arn, ps)
        if inline_policy_matches(inline_policy, keywords):
            ps_name = get_permission_set_name(instance_arn, ps)
            assignments = list_permission_set_assignments(instance_arn, ps)

            if not assignments:
                results.append(
                    {
                        "PermissionSetName": ps_name,
                        "PermissionSetArn": ps,
                        "ManagedPolicies": ", ".join(
                            [p["Name"] for p in managed_policies]
                        ),
                        "InlinePolicy": inline_policy,
                        "PrincipalType": "",
                        "PrincipalName": "",
                        "AccountId": "",
                    }
                )
            else:
                for assignment in assignments:
                    results.append(
                        {
                            "PermissionSetName": ps_name,
                            "PermissionSetArn": ps,
                            "ManagedPolicies": ", ".join(
                                [p["Name"] for p in managed_policies]
                            ),
                            "InlinePolicy": inline_policy,
                            "PrincipalType": assignment["PrincipalType"],
                            "PrincipalName": assignment["PrincipalName"],
                            "AccountId": assignment["AccountId"],
                        }
                    )

    return results


def main():
    """Main script for listing permission set assignments based on keywords in inline policies."""
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxxxxxxxxxx"
    keywords = parse_inline_filter()
    data = collect_inline_permission_set_data(instance_arn, keywords)

    print("Filtered Permission Sets (matching inline policy keywords):")
    for keyword in keywords:
        filtered = [row for row in data if keyword in str(row["InlinePolicy"]).lower()]
        write_to_csv(f"inline_{keyword}.csv", filtered)


if __name__ == "__main__":
    main()
