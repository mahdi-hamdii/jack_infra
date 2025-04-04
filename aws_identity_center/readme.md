# AWS Identity Center Utilities and Testing

This project provides a set of scripts to inspect and audit AWS IAM Identity Center (SSO) configurations, including permission sets, inline/managed policies, and user provisioning details.

## 📁 Folder: `aws_identity_center/`

Contains all the utility and main scripts:

### `main_aws_managed.py`
- Lists permission sets that use **AWS managed policies** (e.g., `IAMFullAccess`, `SecretsManagerReadWrite`).
- Exports relevant permission set assignments to CSV files.

### `main_inline_policy.py`
- Searches inline policies within permission sets for specific **keywords** (e.g., `"s3:*"`, `"secretsmanager"`).
- Outputs all matching permission sets and their assignments to CSV.

### `permission_set_utils.py`
- Contains shared utility functions:
  - List permission sets
  - Describe permission sets
  - Fetch inline/managed policies
  - List assignments
  - Write CSV output

### `list_users.py`
- Lists users from the Identity Store.
- Supports filtering only manually created users (without SCIM ExternalIds) or listing all users.
- Marks if the user is active and saves results to a dated CSV file.

## 🧪 Folder: `aws_identity_center/tests/`

This folder contains tests for the above modules.

### `test_list_users.py`
- Mocks the Identity Store using Moto.
- Uses Faker to generate fake users (manual and SCIM-provisioned).
- Verifies filtering behavior for manual users and all users.
- Checks CSV file creation and file content.

---

## 🧰 Environment Setup

### 1. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install boto3 "moto>=5.2.0" faker pytest
```
✅ Ensure Moto version is >= 5.2.0 to have full `identitystore` mocking support.

---

## ▶️ Run Tests
To run the tests for listing manual users and all users:
```bash
pytest aws_identity_center/tests/test_list_users.py
```
You should see passing tests, validating:
- Filtering of manual users
- Listing all users
- Creation and content validation of the CSV export

Temporary CSV files are automatically removed after each test.

