"""google_sheets Authentication."""

from singer_sdk.authenticators import OAuthAuthenticator, SingletonMeta


# The SingletonMeta metaclass makes your streams reuse the same authenticator instance.
# If this behaviour interferes with your use-case, you can remove the metaclass.
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

    @property
    def oauth_request_body(self) -> dict:
        """Define the OAuth request body for the GoogleAds API."""
        return {}
