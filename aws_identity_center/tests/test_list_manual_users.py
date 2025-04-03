import boto3
import pytest
import os
import csv
from datetime import datetime
from moto import mock_aws
from unittest.mock import patch
from faker import Faker
from aws_identity_center.list_manual_users import list_manual_users, write_users_to_csv

fake = Faker()

@mock_aws
@patch("boto3.client")
def test_list_manual_users(mock_boto_client):
    # Setup mock Identity Store client
    identity_store_client = boto3.client("identitystore", region_name="us-east-1")
    identity_store_id = "d-test"

    # Generate fake users: 5 manual, 5 SCIM
    fake_users = []
    for i in range(5):
        fake_users.append({
            "UserName": fake.user_name(),
            "DisplayName": fake.name(),
            "Status": "ACTIVE",
            "ExternalIds": []
        })
    for i in range(5):
        fake_users.append({
            "UserName": fake.user_name(),
            "DisplayName": fake.name(),
            "Status": "ACTIVE",
            "ExternalIds": [{"Issuer": "SCIM", "Id": fake.uuid4()}]
        })

    # Patch client and inject fake user data
    mock_boto_client.return_value = identity_store_client
    identity_store_client.list_users.return_value = {"Users": fake_users}

    # Run function to fetch manually created users
    result = list_manual_users(identity_store_id)

    # Assert only the 5 manually created users are returned
    assert len(result) == 5
    for user in result:
        assert user["Manual"] is True
        assert user["Status"] in ["", "ACTIVE", "INACTIVE"]

    # Write to CSV and verify it exists
    today = datetime.today().strftime("%Y-%m-%d")
    filename = f"manual_users_{today}.csv"
    write_users_to_csv(result, filename=filename)
    assert os.path.isfile(filename)

    # Optionally, read and verify CSV content
    with open(filename, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        assert len(rows) == 5

    # Clean up test file
    # os.remove(filename)