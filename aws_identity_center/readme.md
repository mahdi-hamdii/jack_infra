# AWS Identity Center Utilities and Testing

This project provides a set of scripts to inspect and audit AWS IAM Identity Center (SSO) configurations, including permission sets, inline/managed policies, and user provisioning details.

---

## 📁 Folder: `aws_identity_center/`

Contains all the utility and main scripts:

### `main_aws_managed.py`

- Lists permission sets that use **AWS managed policies** (e.g., `IAMFullAccess`, `SecretsManagerReadWrite`).
- Exports relevant permission set assignments to CSV files.

### `main_inline_policy.py`

- Searches **inline policies** within permission sets for specific **keywords** (e.g., `"s3:*"`, `"secretsmanager"`).
- Outputs all matching permission sets and their assignments to CSV.

### `list_users_sso.py`

- Lists users provisioned manually (not through SCIM) in AWS Identity Store.
- Optionally lists **all** users (manual + SCIM).
- Outputs users to a dated CSV file.

### `list_users_iam.py`

- Lists IAM users in each account of the organization using a role to be assumed into each account for access.

### `list_users_iamv2.py`

- Lists IAM users in each account of the accounts that are configured in the .aws/config file as profiles.

### `permission_set_utils.py`

- Contains **shared helper functions**:
  - List permission sets
  - Get inline/managed policies
  - Fetch account assignments
  - Write data to CSV

### `find_duplicate_policies.py`

- Detects **duplicate policies** across permission sets:
  - **Full Match**: Two permission sets have identical inline policy documents.
  - **Partial Match**: Two permission sets share one or more identical statements (but policies are not 100% identical).
- Also detects duplicate **managed policies** attached to multiple permission sets.
- Outputs two CSV files under `outputs/`:
  - `duplicate_inline_policies_YYYY-MM-DD.csv`
  - `duplicate_managed_policies_YYYY-MM-DD.csv`

## 📋 Full vs Partial Match Explained

| MatchType    | Description                                                                 |
| :----------- | :-------------------------------------------------------------------------- |
| fullMatch    | Entire inline policy (JSON) is **identical** between two permission sets    |
| partialMatch | Only **one or more Statement blocks** are identical between permission sets |

In case of **full match**, **partial match detection is skipped** between those permission sets (no double-counting).

---

## 📂 Outputs

After running the scripts, results will be saved under:

---

## 🧪 Folder: `aws_identity_center/tests/`

This folder contains unit tests for the project.

### `test_list_users_sso.py`

- Tests listing of manual and SCIM users.
- Uses **Moto** + **Faker** to mock AWS Identity Store responses.

### `test_find_duplicate_policies.py`

- Tests full match and partial match detection for inline policies.
- Verifies correct CSV output.
- Mocks permission sets, inline policies, and managed policies.
- Ensures no false double-counting between full and partial matches.

---

## 🛠 Environment Setup

### 1. Create a Virtual Environment

````bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


### 2. Install Dependencies

```bash
pip install boto3 "moto>=5.2.0" faker pytest
````

✅ Ensure Moto version is >= 5.2.0 to have full `identitystore` mocking support.

---

Ò

## ▶️ Run Tests

To run the tests for listing manual users and all users:

```bash
pytest aws_identity_center/tests/test_list_users_sso.py
```

You should see passing tests, validating:

- Filtering of manual users
- Listing all users
- Creation and content validation of the CSV export

Temporary CSV files are automatically removed after each test.
