"""Tests for Google Service Account authentication."""

import unittest
from unittest.mock import MagicMock, patch

import responses
from singer_sdk.helpers._util import utc_now

from tap_google_sheets.auth import GOOGLE_SHEETS_SCOPES, GoogleServiceAccountAuthenticator
from tap_google_sheets.tap import TapGoogleSheets

# Placeholder — RSA signing is mocked in tests that trigger it.
_TEST_PRIVATE_KEY = "test-only-private-key"

_SA_CONFIG = {
    "service_account_credentials": {
        "client_email": "tap@my-project.iam.gserviceaccount.com",
        "private_key": _TEST_PRIVATE_KEY,
    },
    "sheet_id": "12345",
}

_DRIVE_MOCK = {"title": "Sheet One"}
_HEADERS_MOCK = {"range": "Sheet1!1:1", "values": [["col_one", "col_two"]]}


def _reset_sa_singleton():
    GoogleServiceAccountAuthenticator._SingletonMeta__single_instance = None


def _make_auth(config):
    """Instantiate authenticator with a minimal mocked stream."""
    _reset_sa_singleton()
    stream = MagicMock()
    stream.config = config
    stream.logger = MagicMock()
    return GoogleServiceAccountAuthenticator(
        stream=stream,
        auth_endpoint="https://oauth2.googleapis.com/token",
    )


def _stub_update_access_token(self):
    """Bypass RSA signing; inject a fake token directly."""
    self.access_token = "fake_access_token"
    self.expires_in = 3600
    self.last_refreshed = utc_now()


class TestGoogleServiceAccountAuthenticatorProperties(unittest.TestCase):
    """Unit tests for GoogleServiceAccountAuthenticator property accessors."""

    def setUp(self):
        _reset_sa_singleton()

    def tearDown(self):
        _reset_sa_singleton()

    def test_client_id_returns_client_email(self):
        auth = _make_auth(_SA_CONFIG)
        self.assertEqual(auth.client_id, "tap@my-project.iam.gserviceaccount.com")

    def test_private_key_expands_escaped_newlines(self):
        config = {
            "service_account_credentials": {
                "client_email": "tap@project.iam.gserviceaccount.com",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\\nfake\\n-----END RSA PRIVATE KEY-----",
            },
            "sheet_id": "12345",
        }
        auth = _make_auth(config)
        self.assertIn("\n", auth.private_key)
        self.assertNotIn("\\n", auth.private_key)

    def test_private_key_returns_none_when_not_set(self):
        config = {"service_account_credentials": {}, "sheet_id": "12345"}
        auth = _make_auth(config)
        self.assertIsNone(auth.private_key)

    def test_oauth_request_body_has_required_jwt_claims(self):
        auth = _make_auth(_SA_CONFIG)
        body = auth.oauth_request_body

        self.assertEqual(body["iss"], "tap@my-project.iam.gserviceaccount.com")
        self.assertEqual(body["scope"], GOOGLE_SHEETS_SCOPES)
        self.assertEqual(body["aud"], "https://oauth2.googleapis.com/token")
        self.assertIn("exp", body)
        self.assertIn("iat", body)
        # exp must be ~1 hour ahead of iat
        self.assertAlmostEqual(body["exp"] - body["iat"], 3600, delta=5)

    def test_oauth_request_payload_uses_jwt_bearer_grant(self):
        auth = _make_auth(_SA_CONFIG)
        with patch("jwt.encode", return_value="fake.jwt.token", create=True) as mock_encode:
            payload = auth.oauth_request_payload

        self.assertEqual(
            payload["grant_type"], "urn:ietf:params:oauth:grant-type:jwt-bearer"
        )
        self.assertEqual(payload["assertion"], "fake.jwt.token")
        args, _ = mock_encode.call_args
        self.assertEqual(args[1], _TEST_PRIVATE_KEY)
        self.assertEqual(args[2], "RS256")


class TestAuthenticatorSelection(unittest.TestCase):
    """Tests that the right authenticator is selected based on config."""

    def setUp(self):
        responses.reset()
        _reset_sa_singleton()

    def tearDown(self):
        _reset_sa_singleton()

    @responses.activate
    def test_sa_credentials_select_service_account_authenticator(self):
        responses.add(responses.GET, "https://www.googleapis.com/drive/v2/files/12345",
                      json=_DRIVE_MOCK, status=200)
        responses.add(responses.GET,
                      "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
                      json=_HEADERS_MOCK, status=200)

        with patch.object(GoogleServiceAccountAuthenticator, "update_access_token",
                          _stub_update_access_token):
            stream = TapGoogleSheets(config=_SA_CONFIG).discover_streams()[0]

        self.assertIsInstance(stream.authenticator, GoogleServiceAccountAuthenticator)

    @responses.activate
    def test_missing_private_key_falls_through_to_oauth(self):
        config = {
            "service_account_credentials": {"client_email": "tap@project.iam.gserviceaccount.com"},
            "oauth_credentials": {"client_id": "id", "client_secret": "secret", "refresh_token": "tok"},
            "sheet_id": "12345",
        }
        responses.add(responses.POST, "https://oauth2.googleapis.com/token",
                      json={"access_token": "tok"}, status=200)
        responses.add(responses.GET, "https://www.googleapis.com/drive/v2/files/12345",
                      json=_DRIVE_MOCK, status=200)
        responses.add(responses.GET,
                      "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
                      json=_HEADERS_MOCK, status=200)

        stream = TapGoogleSheets(config=config).discover_streams()[0]

        self.assertNotIsInstance(stream.authenticator, GoogleServiceAccountAuthenticator)

    @responses.activate
    def test_missing_client_email_falls_through_to_oauth(self):
        config = {
            "service_account_credentials": {"private_key": _TEST_PRIVATE_KEY},
            "oauth_credentials": {"client_id": "id", "client_secret": "secret", "refresh_token": "tok"},
            "sheet_id": "12345",
        }
        responses.add(responses.POST, "https://oauth2.googleapis.com/token",
                      json={"access_token": "tok"}, status=200)
        responses.add(responses.GET, "https://www.googleapis.com/drive/v2/files/12345",
                      json=_DRIVE_MOCK, status=200)
        responses.add(responses.GET,
                      "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
                      json=_HEADERS_MOCK, status=200)

        stream = TapGoogleSheets(config=config).discover_streams()[0]

        self.assertNotIsInstance(stream.authenticator, GoogleServiceAccountAuthenticator)


    @responses.activate
    def test_authenticator_singleton_reused_across_requests(self):
        responses.add(responses.GET, "https://www.googleapis.com/drive/v2/files/12345",
                      json=_DRIVE_MOCK, status=200)
        responses.add(responses.GET,
                      "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
                      json=_HEADERS_MOCK, status=200)

        with patch.object(GoogleServiceAccountAuthenticator, "update_access_token",
                          _stub_update_access_token):
            stream = TapGoogleSheets(config=_SA_CONFIG).discover_streams()[0]

        first = stream.authenticator
        second = stream.authenticator
        self.assertIs(first, second)


class TestServiceAccountIntegration(unittest.TestCase):
    """End-to-end tests for the service account authentication flow."""

    def setUp(self):
        responses.reset()
        _reset_sa_singleton()

    def tearDown(self):
        _reset_sa_singleton()

    @responses.activate
    def test_discovery_completes_with_service_account_credentials(self):
        responses.add(responses.GET, "https://www.googleapis.com/drive/v2/files/12345",
                      json={"title": "SA Sheet"}, status=200)
        responses.add(responses.GET,
                      "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
                      json={"range": "Sheet1!1:1", "values": [["column_one", "column_two"]]},
                      status=200)

        with patch.object(GoogleServiceAccountAuthenticator, "update_access_token",
                          _stub_update_access_token):
            catalog = TapGoogleSheets(config=_SA_CONFIG).discover_streams()

        self.assertEqual(len(catalog), 1)
