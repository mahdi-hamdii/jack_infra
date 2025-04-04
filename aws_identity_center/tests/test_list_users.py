import boto3
import pytest
import os
import csv
from datetime import datetime
from moto import mock_aws
from unittest.mock import patch
from faker import Faker
from aws_identity_center.list_users import list_users, write_users_to_csv

fake = Faker()


def generate_fake_users():
    """Helper to generate 5 manual + 5 SCIM users."""
    fake_users = []
    for _ in range(5):
        fake_users.append(
            {
                "UserName": fake.user_name(),
                "DisplayName": fake.name(),
                "Status": "ACTIVE",
                "ExternalIds": [],
            }
        )
    for _ in range(5):
        fake_users.append(
            {
                "UserName": fake.user_name(),
                "DisplayName": fake.name(),
                "Status": "ACTIVE",
                "ExternalIds": [{"Issuer": "SCIM", "Id": fake.uuid4()}],
            }
        )
    return fake_users


@mock_aws
@patch("boto3.client")
def test_list_manual_users(mock_boto_client):
    # Setup mock Identity Store client
    identity_store_client = boto3.client("identitystore", region_name="us-east-1")
    identity_store_id = "d-test"

    # Patch client and inject fake user data
    mock_boto_client.return_value = identity_store_client
    identity_store_client.list_users.return_value = {"Users": generate_fake_users()}

    # Run function to fetch manually created users
    result = list_users(identity_store_id)

    # Assert only the 5 manually created users are returned
    assert len(result) == 5
    for user in result:
        assert user["Manual"] is True
        assert user["Status"] in ["", "ACTIVE", "INACTIVE"]

    # Write to CSV and verify it exists
    write_users_to_csv(result, manual_only=True)
    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"manual_users_{today}.csv"
    assert os.path.isfile(filename)

    # Optionally, read and verify CSV content
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        assert len(rows) == 5

    # Clean up test file
    # os.remove(filename)


@mock_aws
@patch("boto3.client")
def test_list_all_users(mock_boto_client):
    """Test listing all users (manual + SCIM) with manual=false."""
    identity_store_client = boto3.client("identitystore", region_name="us-east-1")
    identity_store_id = "d-test"

    # Patch client and inject fake user data
    mock_boto_client.return_value = identity_store_client
    identity_store_client.list_users.return_value = {"Users": generate_fake_users()}

    # Run function to fetch ALL users (manual_only=False)
    result = list_users(identity_store_id, manual_only=False)

    # Assert all 10 users are returned
    assert len(result) == 10
    for user in result:
        assert user["Status"] in ["", "ACTIVE", "INACTIVE"]

    # Write to CSV and verify it exists
    write_users_to_csv(result, manual_only=False)
    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"all_users_{today}.csv"
    assert os.path.isfile(filename)

    # Optionally, read and verify CSV content
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        assert len(rows) == 10

    # Clean up
    # os.remove(filename)
