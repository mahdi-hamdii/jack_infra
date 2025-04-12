import json
import csv
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from aws_identity_center.find_duplicate_inline_statement import (
    find_duplicate_statements,
    main,
)

@pytest.fixture
def mock_sso_admin_client():
    """Mock boto3 SSO Admin client with complex inline policies."""
    with patch("boto3.client") as mock_client:
        sso_client = MagicMock()

        # Mock list_permission_sets
        sso_client.list_permission_sets.return_value = {
            "PermissionSets": [
                "arn:aws:sso:::permissionSet/pset-111",
                "arn:aws:sso:::permissionSet/pset-222",
                "arn:aws:sso:::permissionSet/pset-333",
            ]
        }

        # Mock describe_permission_set
        def describe_permission_set_side_effect(InstanceArn, PermissionSetArn):
            if PermissionSetArn.endswith("111"):
                return {"PermissionSet": {"Name": "AdminPS"}}
            elif PermissionSetArn.endswith("222"):
                return {"PermissionSet": {"Name": "DevPS"}}
            elif PermissionSetArn.endswith("333"):
                return {"PermissionSet": {"Name": "AuditPS"}}
            else:
                return {"PermissionSet": {"Name": "Unknown"}}

        sso_client.describe_permission_set.side_effect = describe_permission_set_side_effect

        # Mock get_inline_policy_for_permission_set
        def get_inline_policy_side_effect(InstanceArn, PermissionSetArn):
            if PermissionSetArn.endswith("111"):
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
                        {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"},
                        {"Effect": "Allow", "Action": "s3:PutObject", "Resource": "*"},
                        {"Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "*"},
                        {"Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "*"},
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}
            elif PermissionSetArn.endswith("222"):
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "ec2:StartInstances", "Resource": "*"},
                        {"Effect": "Allow", "Action": "ec2:StartInstances", "Resource": "*"},
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}
            elif PermissionSetArn.endswith("333"):
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "cloudtrail:LookupEvents", "Resource": "*"},
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}
            else:
                return {"InlinePolicy": None}

        sso_client.get_inline_policy_for_permission_set.side_effect = get_inline_policy_side_effect

        mock_client.return_value = sso_client
        yield mock_client

def test_find_duplicate_statements():
    """Unit test for finding duplicates including wildcard overlaps."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
            {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"},
            {"Effect": "Allow", "Action": "s3:PutObject", "Resource": "*"},
            {"Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "*"},
            {"Effect": "Deny", "Action": "s3:DeleteObject", "Resource": "*"},
        ]
    }
    policy_json = json.dumps(policy)
    duplicates = find_duplicate_statements(policy_json)

    match_types = {d[0] for d in duplicates}
    assert "ExactMatch" in match_types
    assert "WildcardMatch" in match_types

@pytest.mark.usefixtures("mock_sso_admin_client")
def test_main_creates_complex_csv():
    """Integration test for full run."""
    today = datetime.today().strftime("%Y-%m-%d")
    expected_csv_filename = f"duplicate_inline_statements_{today}.csv"

    if os.path.exists(expected_csv_filename):
        os.remove(expected_csv_filename)

    main()

    assert os.path.exists(expected_csv_filename)

    with open(expected_csv_filename, newline="") as csvfile:
        rows = list(csv.DictReader(csvfile))

    admin_rows = [row for row in rows if row["PermissionSetName"] == "AdminPS"]
    dev_rows = [row for row in rows if row["PermissionSetName"] == "DevPS"]

    assert len(admin_rows) > 0
    assert len(dev_rows) > 0

    match_types = {row["MatchType"] for row in rows}
    assert "ExactMatch" in match_types
    assert "WildcardMatch" in match_types
