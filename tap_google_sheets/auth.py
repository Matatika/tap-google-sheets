"""Google Sheets Authentication."""

import json
from datetime import datetime

import requests
from singer_sdk.authenticators import (
    APIAuthenticatorBase,
    OAuthAuthenticator,
    SingletonMeta,
)
from singer_sdk.helpers._util import utc_now
from singer_sdk.streams import RESTStream

GOOGLE_API_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GoogleSheetsAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """Authenticator class for Google Sheets."""

    @property
    def oauth_request_body(self) -> dict:
        """Define the OAuth request body for the GoogleSheets API."""
        oauth_credentials = self.config.get("oauth_credentials", {})
        return {
            "grant_type": "refresh_token",
            "client_id": oauth_credentials.get("client_id"),
            "client_secret": oauth_credentials.get("client_secret"),
            "refresh_token": oauth_credentials.get("refresh_token"),
        }


class ProxyGoogleSheetsAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """API Authenticator for Proxy OAuth 2.0 flows."""

    def __init__(
        self,
        stream: RESTStream,
        auth_endpoint=None,
        oauth_scopes=None,
        auth_headers=None,
        auth_body=None,
    ) -> None:
        """Create a new authenticator."""
        super().__init__(stream=stream)
        self._auth_endpoint = auth_endpoint
        self._oauth_scopes = oauth_scopes
        self._auth_headers = auth_headers
        self._auth_body = auth_body

        # Initialize internal tracking attributes
        self.access_token = None
        self.refresh_token = None
        self.last_refreshed = None
        self.expires_in = None

    def is_token_valid(self) -> bool:
        """Check if token is valid."""
        if self.last_refreshed is None:
            return False
        if not self.expires_in:
            return True

        now = datetime.now(self.last_refreshed.tzinfo)

        if self.expires_in > (now - self.last_refreshed).total_seconds():
            return True
        return False

    # Authentication and refresh
    def update_access_token(self) -> None:
        """Update `access_token` along with: `last_refreshed` and `expires_in`."""
        request_time = utc_now()

        token_response = requests.post(
            self.auth_endpoint,
            headers=self._auth_headers,
            data=json.dumps(self._auth_body),
        )
        try:
            token_response.raise_for_status()
            self.logger.info("OAuth authorization attempt was successful.")
        except Exception as ex:
            raise RuntimeError(
                f"Failed OAuth login, response was '{token_response.json()}'. {ex}"
            )
        token_json = token_response.json()
        self.access_token = token_json["access_token"]
        self.expires_in = token_json["expires_in"]
        self.last_refreshed = request_time

    @property
    def oauth_request_body(self) -> dict:
        """Define the OAuth request body."""
        return {}


class WorkloadIdentityAuthenticator(APIAuthenticatorBase, metaclass=SingletonMeta):
    """Authenticator using Google Workload Identity Federation."""

    def __init__(
        self,
        stream: RESTStream,
        credentials_json: str = None,
        credentials_file: str = None,
    ) -> None:
        """Create a new authenticator."""
        super().__init__(stream=stream)
        self._credentials_json = credentials_json
        self._credentials_file = credentials_file
        self._google_credentials = None

    def _load_credentials(self):
        if self._credentials_file:
            with open(self._credentials_file) as f:
                info = json.load(f)
        else:
            info = json.loads(self._credentials_json)
        self.logger.info(f"credential info: {info}")
        return self._credentials_from_info(info)

    def _credentials_from_info(self, info):
        cred_type = info.get("type")
        if cred_type == "external_account":
            credential_source = info.get("credential_source", {})
            environment_id = credential_source.get("environment_id", "")
            if environment_id.startswith("aws"):
                from google.auth.aws import Credentials
            elif "executable" in credential_source:
                from google.auth.pluggable import Credentials
            else:
                from google.auth.identity_pool import Credentials
            return Credentials.from_info(info).with_scopes(GOOGLE_API_SCOPES)
        if cred_type == "service_account":
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(
                info, scopes=GOOGLE_API_SCOPES
            )
        raise ValueError(f"Unsupported credential type: {cred_type!r}")

    def authenticate_request(self, request):
        """Authenticate the request with a fresh WIF access token."""
        from google.auth.transport.requests import Request as GoogleAuthRequest

        if self._google_credentials is None:
            self._google_credentials = self._load_credentials()
        if not self._google_credentials.valid:
            self._google_credentials.refresh(GoogleAuthRequest())
        self.auth_headers["Authorization"] = f"Bearer {self._google_credentials.token}"
        return super().authenticate_request(request)
