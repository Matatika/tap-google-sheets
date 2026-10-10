"""Tests for Workload Identity Federation authentication."""

import logging
import unittest
from unittest.mock import MagicMock, patch

from tap_google_sheets.auth import (
    _AwsSecurityCredentialsSupplier,
    WorkloadIdentityAuthenticator,
)

AWS_EXTERNAL_ACCOUNT_INFO = {
    "type": "external_account",
    "audience": "//iam.googleapis.com/projects/1/locations/global/x",
    "subject_token_type": "urn:ietf:params:aws:token-type:aws4_request",
    "token_url": "https://sts.googleapis.com/v1/token",
    "credential_source": {
        "environment_id": "aws1",
        "region_url": "http://169.254.169.254/latest/meta-data/placement/availability-zone",  # noqa: E501
        "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials",
        "regional_cred_verification_url": "https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",  # noqa: E501
    },
}


class TestAwsSecurityCredentialsSupplier(unittest.TestCase):
    """Test the boto3-backed AWS credentials supplier."""

    def _fake_session(
        self, access="AK", secret="SK", token="TT", region="ap-southeast-1"
    ):
        session = MagicMock()
        if access is None:
            session.get_credentials.return_value = None
        else:
            frozen = MagicMock(access_key=access, secret_key=secret, token=token)
            session.get_credentials.return_value.get_frozen_credentials.return_value = (
                frozen
            )
        session.region_name = region
        return session

    def test_resolves_credentials_from_boto3(self):
        supplier = _AwsSecurityCredentialsSupplier()
        with patch("boto3.Session", return_value=self._fake_session()):
            creds = supplier.get_aws_security_credentials(None, None)
        self.assertEqual(creds.access_key_id, "AK")
        self.assertEqual(creds.secret_access_key, "SK")
        self.assertEqual(creds.session_token, "TT")

    def test_resolves_region_from_boto3(self):
        supplier = _AwsSecurityCredentialsSupplier()
        with patch("boto3.Session", return_value=self._fake_session()):
            self.assertEqual(supplier.get_aws_region(None, None), "ap-southeast-1")

    def test_raises_when_no_credentials(self):
        supplier = _AwsSecurityCredentialsSupplier()
        with patch("boto3.Session", return_value=self._fake_session(access=None)):
            with self.assertRaises(AttributeError):
                supplier.get_aws_security_credentials(None, None)

    def test_returns_none_when_no_region(self):
        supplier = _AwsSecurityCredentialsSupplier()
        with patch("boto3.Session", return_value=self._fake_session(region=None)):
            self.assertIsNone(supplier.get_aws_region(None, None))


class TestAwsCredentialsWiring(unittest.TestCase):
    """Test that AWS external_account resolves through boto3 by default."""

    def _authenticator(self, credentials_json=None):
        auth = WorkloadIdentityAuthenticator.__new__(WorkloadIdentityAuthenticator)
        auth.logger = logging.getLogger("test")
        auth._credentials_json = credentials_json
        auth._credentials_file = None
        return auth

    def test_aws_external_account_uses_boto3_supplier(self):
        import json

        auth = self._authenticator(json.dumps(AWS_EXTERNAL_ACCOUNT_INFO))
        creds = auth._load_credentials()
        self.assertIsInstance(
            creds._aws_security_credentials_supplier,
            _AwsSecurityCredentialsSupplier,
        )

    def test_rejects_non_aws_credential_source(self):
        import json

        info = dict(AWS_EXTERNAL_ACCOUNT_INFO)
        info["credential_source"] = {"environment_id": "gcp1"}
        auth = self._authenticator(json.dumps(info))
        with self.assertRaises(NotImplementedError):
            auth._load_credentials()

    def test_rejects_non_external_account_type(self):
        import json

        info = dict(AWS_EXTERNAL_ACCOUNT_INFO)
        info["type"] = "service_account"
        auth = self._authenticator(json.dumps(info))
        with self.assertRaises(NotImplementedError):
            auth._load_credentials()


if __name__ == "__main__":
    unittest.main()
