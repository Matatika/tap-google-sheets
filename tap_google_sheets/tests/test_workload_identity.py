"""Tests for Workload Identity Federation authentication."""

import logging
import unittest
from unittest.mock import MagicMock, patch

from tap_google_sheets.auth import (
    _BotocoreAwsSecurityCredentialsSupplier,
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


class TestBotocoreAwsSecurityCredentialsSupplier(unittest.TestCase):
    """Test the botocore-backed AWS credentials supplier."""

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
        session.get_config_variable.return_value = region
        return session

    def test_resolves_credentials_from_botocore(self):
        supplier = _BotocoreAwsSecurityCredentialsSupplier()
        with patch("botocore.session.get_session", return_value=self._fake_session()):
            creds = supplier.get_aws_security_credentials(None, None)
        self.assertEqual(creds.access_key_id, "AK")
        self.assertEqual(creds.secret_access_key, "SK")
        self.assertEqual(creds.session_token, "TT")

    def test_resolves_region_from_botocore(self):
        supplier = _BotocoreAwsSecurityCredentialsSupplier()
        with patch("botocore.session.get_session", return_value=self._fake_session()):
            self.assertEqual(supplier.get_aws_region(None, None), "ap-southeast-1")

    def test_raises_when_no_credentials(self):
        from google.auth import exceptions

        supplier = _BotocoreAwsSecurityCredentialsSupplier()
        with patch(
            "botocore.session.get_session",
            return_value=self._fake_session(access=None),
        ):
            with self.assertRaises(exceptions.RefreshError):
                supplier.get_aws_security_credentials(None, None)

    def test_raises_when_no_region(self):
        from google.auth import exceptions

        supplier = _BotocoreAwsSecurityCredentialsSupplier()
        with patch(
            "botocore.session.get_session",
            return_value=self._fake_session(region=None),
        ):
            with self.assertRaises(exceptions.RefreshError):
                supplier.get_aws_region(None, None)


class TestAwsCredentialsWiring(unittest.TestCase):
    """Test that AWS external_account resolves through botocore by default."""

    def _authenticator(self):
        auth = WorkloadIdentityAuthenticator.__new__(WorkloadIdentityAuthenticator)
        auth.logger = logging.getLogger("test")
        return auth

    def test_aws_external_account_uses_botocore_supplier(self):
        info = dict(AWS_EXTERNAL_ACCOUNT_INFO)
        creds = self._authenticator()._credentials_from_info(info)
        self.assertIsInstance(
            creds._aws_security_credentials_supplier,
            _BotocoreAwsSecurityCredentialsSupplier,
        )
        # Original config dict must not be mutated for the caller.
        self.assertIn("credential_source", info)

    def test_aws_falls_back_to_default_source_without_botocore(self):
        # If botocore is unavailable, keep google-auth's default AWS source
        # (env static keys / IMDS) rather than crashing.
        auth = self._authenticator()
        with patch.object(
            WorkloadIdentityAuthenticator,
            "_aws_security_credentials_supplier",
            return_value=None,
        ):
            creds = auth._credentials_from_info(dict(AWS_EXTERNAL_ACCOUNT_INFO))
        self.assertNotIsInstance(
            creds._aws_security_credentials_supplier,
            _BotocoreAwsSecurityCredentialsSupplier,
        )

    def test_supplier_none_when_botocore_missing(self):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("botocore"):
                raise ImportError("no botocore")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            supplier = (
                WorkloadIdentityAuthenticator._aws_security_credentials_supplier()
            )
        self.assertIsNone(supplier)


if __name__ == "__main__":
    unittest.main()
