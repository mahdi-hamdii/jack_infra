import boto3
import csv
import os
import tempfile
import pytest
from moto import mock_aws
from aws_identity_center.deactivate_aws_users import (
    remove_console_login,
    deactivate_access_keys,
    deactivate_ssh_keys,
    process_users,
)


@pytest.fixture
def iam_setup():
    """Create a fake IAM user setup."""
    with mock_aws():
        client = boto3.client("iam", region_name="us-east-1")
        # Create a fake user
        client.create_user(UserName="testuser")
        # Create login profile (console password)
        client.create_login_profile(UserName="testuser", Password="TestPass123!")
        # Create access key
        client.create_access_key(UserName="testuser")
        # Create SSH key
        client.upload_ssh_public_key(
            UserName="testuser",
            SSHPublicKeyBody="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7",
        )
        yield client


@mock_aws
def test_remove_console_login(iam_setup):
    remove_console_login(iam_setup, "testuser")
    # Try fetching login profile should raise
    with pytest.raises(iam_setup.exceptions.NoSuchEntityException):
        iam_setup.get_login_profile(UserName="testuser")


@mock_aws
def test_deactivate_access_keys(iam_setup):
    deactivate_access_keys(iam_setup, "testuser")
    keys = iam_setup.list_access_keys(UserName="testuser")["AccessKeyMetadata"]
    assert all(key["Status"] == "Inactive" for key in keys)


@mock_aws
def test_deactivate_ssh_keys(iam_setup):
    deactivate_ssh_keys(iam_setup, "testuser")
    keys = iam_setup.list_ssh_public_keys(UserName="testuser")["SSHPublicKeys"]
    assert all(key["Status"] == "Inactive" for key in keys)


def test_process_users(iam_setup):
    """End-to-end test processing users from a fake CSV."""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(delete=False, mode="w", newline="") as tmp_csv:
        fieldnames = ["AccountId", "UserName"]
        writer = csv.DictWriter(tmp_csv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"AccountId": "123456789012", "UserName": "testuser"})
        csv_path = tmp_csv.name

    profiles_mapping = {"123456789012": "default"}  # Fake profile mapping for test

    # Patch boto3 Session to always return the mocked IAM client
    original_boto3_Session = boto3.Session

    class FakeSession:
        def __init__(self, profile_name=None):
            pass

        def client(self, service_name):
            if service_name == "iam":
                return iam_setup
            raise Exception(f"Unsupported client {service_name}")

    boto3.Session = FakeSession

    try:
        process_users(csv_path, profiles_mapping)
    finally:
        boto3.Session = original_boto3_Session
        os.remove(csv_path)
