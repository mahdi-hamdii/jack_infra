import boto3
import pytest
import os
import csv
import json
import hashlib
from unittest.mock import patch
from collections import defaultdict
from datetime import datetime
from aws_identity_center.find_duplicate_policies import (
    list_permission_sets,
    get_inline_policy,
    get_managed_policies,
    save_duplicates_to_csv,
    extract_statements,
    detect_full_matches,
    detect_partial_matches,
)

# -------------------------------
# Mock data
# -------------------------------

mock_permission_sets = [
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-1111",
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-2222",
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-3333",
]

mock_inline_policies = {
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-1111": json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
            {"Effect": "Allow", "Action": "ec2:*", "Resource": "*"}
        ]
    }),
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-2222": json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
            {"Effect": "Allow", "Action": "ec2:*", "Resource": "*"}
        ]
    }),  # full match with A
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-3333": json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:*", "Resource": "*"}
        ]
    }),  # only partial match with A or B
}

mock_managed_policies = {
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-1111": ["arn:aws:iam::aws:policy/AmazonS3FullAccess"],
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-2222": ["arn:aws:iam::aws:policy/AmazonS3FullAccess"],
    "arn:aws:sso:::permissionSet/ssoins-xxxx/ps-3333": ["arn:aws:iam::aws:policy/AmazonEC2FullAccess"],
}

# -------------------------------
# Actual test
# -------------------------------

@patch("boto3.client")
def test_detect_full_and_partial_duplicates(mock_boto_client):
    """Test full and partial matches detection and CSV export."""

    # Setup mock boto3 client
    sso_admin_client = mock_boto_client.return_value

    # Mock list_permission_sets
    sso_admin_client.list_permission_sets.side_effect = [
        {"PermissionSets": mock_permission_sets, "NextToken": None}
    ]

    # Mock describe_permission_set
    def describe_permission_set_side_effect(InstanceArn, PermissionSetArn):
        name_mapping = {
            mock_permission_sets[0]: "PermissionSetA",
            mock_permission_sets[1]: "PermissionSetB",
            mock_permission_sets[2]: "PermissionSetC",
        }
        return {"PermissionSet": {"Name": name_mapping[PermissionSetArn]}}

    sso_admin_client.describe_permission_set.side_effect = describe_permission_set_side_effect

    # Mock get_inline_policy_for_permission_set
    def get_inline_policy_for_permission_set_side_effect(InstanceArn, PermissionSetArn):
        return {"InlinePolicy": mock_inline_policies.get(PermissionSetArn)}

    sso_admin_client.get_inline_policy_for_permission_set.side_effect = get_inline_policy_for_permission_set_side_effect

    # Mock list_managed_policies_in_permission_set
    def list_managed_policies_in_permission_set_side_effect(InstanceArn, PermissionSetArn):
        policies = mock_managed_policies.get(PermissionSetArn, [])
        return {"AttachedManagedPolicies": [{"Arn": p, "Name": p.split("/")[-1]} for p in policies]}

    sso_admin_client.list_managed_policies_in_permission_set.side_effect = list_managed_policies_in_permission_set_side_effect

    # -------------------
    # Simulation
    # -------------------
    instance_arn = "arn:aws:sso:::instance/ssoins-xxxx"
    permission_sets = list_permission_sets(instance_arn)

    # Build policy data map
    policy_data_map = {}
    for ps in permission_sets:
        ps_name = boto3.client("sso-admin").describe_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=ps
        )["PermissionSet"]["Name"]

        policy_text = get_inline_policy(instance_arn, ps)
        if policy_text:
            policy_data_map[ps_name] = {
                "policy_text": policy_text,
                "policy_hash": hashlib.md5(policy_text.encode('utf-8')).hexdigest(),
                "statements": extract_statements(policy_text)
            }

    # Detect full matches
    full_matches, full_match_pairs = detect_full_matches(policy_data_map)

    # Detect partial matches
    partial_matches = detect_partial_matches(policy_data_map, full_match_pairs)

    # Save results to CSV
    today = datetime.today().strftime("%Y-%m-%d")
    os.makedirs("outputs", exist_ok=True)
    output_csv = f"outputs/duplicate_inline_policies_{today}.csv"

    save_duplicates_to_csv(
        full_matches + partial_matches,
        f"duplicate_inline_policies_{today}.csv",
        headers=["MatchType", "PolicyHash", "PermissionSets", "PolicyContent"]
    )

    # -------------------
    # Assertions
    # -------------------
    assert os.path.isfile(output_csv)

    with open(output_csv, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

        # 1 full match (A and B)
        # 1 partial match (A and C) OR (B and C)
        full_count = sum(1 for row in rows if row["MatchType"] == "fullMatch")
        partial_count = sum(1 for row in rows if row["MatchType"] == "partialMatch")

        assert full_count == 1
        assert partial_count == 2

    # Clean up
    os.remove(output_csv)

    print("\nTest passed: Full matches and partial matches detected correctly, CSV created successfully.")

