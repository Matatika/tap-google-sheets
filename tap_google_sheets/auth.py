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


class _BotocoreAwsSecurityCredentialsSupplier:
    """Supply AWS security credentials to Google WIF via botocore.

    Google's default AWS credential source only reads static env credentials
    or the EC2 instance metadata service (IMDS). This supplier uses botocore's
    default credential provider chain instead, so environments where IMDS is
    unavailable -- notably EKS with IRSA, which exchanges a web identity token
    for temporary credentials -- resolve correctly.
    """

    def get_aws_security_credentials(self, context, request):
        """Return temporary AWS credentials from the botocore provider chain."""
        import botocore.session
        from google.auth import exceptions
        from google.auth.aws import AwsSecurityCredentials

        credentials = botocore.session.get_session().get_credentials()
        if credentials is None:
            raise exceptions.RefreshError(
                "Unable to resolve AWS security credentials from the botocore "
                "provider chain (checked env vars, web identity token file, "
                "shared config, and IMDS)."
            )
        frozen = credentials.get_frozen_credentials()
        return AwsSecurityCredentials(
            frozen.access_key,
            frozen.secret_key,
            frozen.token,
        )

    def get_aws_region(self, context, request):
        """Return the AWS region resolved by botocore (AWS_REGION, config...)."""
        import botocore.session
        from google.auth import exceptions

        region = botocore.session.get_session().get_config_variable("region")
        if not region:
            raise exceptions.RefreshError(
                "Unable to determine the AWS region. Set AWS_REGION or "
                "AWS_DEFAULT_REGION."
            )
        return region


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
        self._credentials_info = None

    def _load_credentials(self):
        if self._credentials_file:
            with open(self._credentials_file) as f:
                info = json.load(f)
        else:
            info = json.loads(self._credentials_json)
        self.logger.info(f"credential info: {info}")
        self._credentials_info = info
        return self._credentials_from_info(info)

    @staticmethod
    def _is_aws_external_account(info):
        if not info or info.get("type") != "external_account":
            return False
        environment_id = info.get("credential_source", {}).get("environment_id", "")
        return environment_id.startswith("aws")

    def _credentials_from_info(self, info, aws_use_botocore=False):
        cred_type = info.get("type")
        if cred_type == "external_account":
            credential_source = info.get("credential_source", {})
            environment_id = credential_source.get("environment_id", "")
            if environment_id.startswith("aws"):
                from google.auth.aws import Credentials

                if aws_use_botocore:
                    # Fallback path: the default AWS source could not resolve
                    # credentials (env static keys / IMDS). Delegate to
                    # botocore's provider chain, which also handles EKS IRSA
                    # (AssumeRoleWithWebIdentity from the web identity token
                    # file) where IMDS is blocked. The supplier replaces
                    # `credential_source` -- they are mutually exclusive.
                    info = {k: v for k, v in info.items() if k != "credential_source"}
                    return Credentials.from_info(
                        info,
                        aws_security_credentials_supplier=(
                            _BotocoreAwsSecurityCredentialsSupplier()
                        ),
                    ).with_scopes(GOOGLE_API_SCOPES)
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
        from google.auth import exceptions
        from google.auth.transport.requests import Request as GoogleAuthRequest

        if self._google_credentials is None:
            self._google_credentials = self._load_credentials()
        if not self._google_credentials.valid:
            try:
                self._google_credentials.refresh(GoogleAuthRequest())
            except (exceptions.RefreshError, exceptions.TransportError) as err:
                # The default AWS credential source (env static keys / IMDS)
                # could not resolve credentials -- e.g. on EKS with IRSA, where
                # IMDS is blocked and credentials come from a web identity token
                # file. Depending on how IMDS is blocked this surfaces either as
                # a RefreshError (proxy returns an error page) or a
                # TransportError (connection times out). Fall back to botocore's
                # provider chain, which handles that case. Re-raise for any
                # non-AWS credential type.
                if not self._is_aws_external_account(self._credentials_info):
                    raise
                self.logger.warning(
                    "Default AWS credential source failed (%s); falling back to "
                    "the botocore credential provider chain.",
                    type(err).__name__,
                )
                self._google_credentials = self._credentials_from_info(
                    self._credentials_info, aws_use_botocore=True
                )
                self._google_credentials.refresh(GoogleAuthRequest())
        self.auth_headers["Authorization"] = f"Bearer {self._google_credentials.token}"
        return super().authenticate_request(request)
