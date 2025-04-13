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
    """Mock boto3 SSO Admin client with rich realistic inline policies."""
    with patch("boto3.client") as mock_client:
        sso_client = MagicMock()

        # Mock list_permission_sets
        sso_client.list_permission_sets.return_value = {
            "PermissionSets": [
                "arn:aws:sso:::permissionSet/pset-111",
                "arn:aws:sso:::permissionSet/pset-222",
                "arn:aws:sso:::permissionSet/pset-333",
                "arn:aws:sso:::permissionSet/pset-444",
                "arn:aws:sso:::permissionSet/pset-555",
            ]
        }

        # Mock describe_permission_set
        def describe_permission_set_side_effect(InstanceArn, PermissionSetArn):
            return {"PermissionSet": {"Name": PermissionSetArn.split("/")[-1]}}

        sso_client.describe_permission_set.side_effect = describe_permission_set_side_effect

        # Mock get_inline_policy_for_permission_set
        def get_inline_policy_side_effect(InstanceArn, PermissionSetArn):
            if PermissionSetArn.endswith("111"):
                # S3 exact and wildcard duplicates
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"},
                        {"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"},
                        {"Effect": "Allow", "Action": "s3:*", "Resource": "*"},
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}

            if PermissionSetArn.endswith("222"):
                # EC2 with small duplicates
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": ["ec2:StartInstances", "ec2:StopInstances"], "Resource": "*"},
                        {"Effect": "Allow", "Action": "ec2:StartInstances", "Resource": "*"},
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}

            if PermissionSetArn.endswith("333"):
                # Audit no duplicates
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "cloudtrail:LookupEvents", "Resource": "*"},
                        {"Effect": "Deny", "Action": ["s3:PutBucketAcl", "s3:PutBucketPolicy", "s3:DeleteBucketPolicy"], "Resource": "*"},
                        {"Effect": "Deny", "Action": ["s3: *"], "Resource": ["arn:aws:s3:::com.hoopladigital.video", "arn:aws:s3:..com.hoopladigital.video/*", "arn:aws:s3:/.com.hoopladigital.video.master", "arn:aws:s3:..com.hoopladigital.video.master/*"]}
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}

            if PermissionSetArn.endswith("444"):
                # Glue example with condition
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "iam:PassRole",
                            "Resource": ["arn:aws:iam::*:role/AWSGlueServiceRole"],
                            "Condition": {"StringLike": {"iam:PassedToService": "glue.amazonaws.com"}}
                        },
                        {
                            "Effect": "Allow",
                            "Action": "iam:PassRole",
                            "Resource": ["arn:aws:iam::*:role/AWSGlueServiceRole"],
                            "Condition": {"StringLike": {"iam:PassedToService": "glue.amazonaws.com"}}
                        },
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}

            if PermissionSetArn.endswith("555"):
                # Redshift example
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": [
                            "redshift-serverless:GetWorkgroup",
                            "redshift-serverless:ListWorkgroups",
                        ], "Resource": "*"},
                        {"Effect": "Allow", "Action": "redshift-serverless:GetWorkgroup", "Resource": "*"},
                    ]
                }
                return {"InlinePolicy": json.dumps(policy)}

            return {"InlinePolicy": None}

        sso_client.get_inline_policy_for_permission_set.side_effect = get_inline_policy_side_effect

        mock_client.return_value = sso_client
        yield mock_client


@pytest.mark.usefixtures("mock_sso_admin_client")
def test_main_creates_enhanced_csv():
    today = datetime.today().strftime("%Y-%m-%d")
    expected_csv_filename = f"duplicate_inline_statements_{today}.csv"

    if os.path.exists(expected_csv_filename):
        os.remove(expected_csv_filename)

    main()

    assert os.path.exists(expected_csv_filename)

    with open(expected_csv_filename, newline="") as csvfile:
        rows = list(csv.DictReader(csvfile))

    psets_found = {row["PermissionSetName"] for row in rows}
    match_types = {row["MatchType"] for row in rows}

    assert "pset-111" in psets_found  # S3 examples
    assert "pset-222" in psets_found  # EC2 examples
    assert "pset-444" in psets_found  # Glue examples
    assert "pset-555" in psets_found  # Redshift examples

    assert "ExactMatch" in match_types
    assert "WildcardMatch" in match_types

    print(f"✅ CSV generated with {len(rows)} duplicate rows.")
