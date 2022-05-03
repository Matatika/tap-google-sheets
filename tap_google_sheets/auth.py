"""google_sheets Authentication."""

from singer_sdk.authenticators import OAuthAuthenticator, SingletonMeta


# The SingletonMeta metaclass makes your streams reuse the same authenticator instance.
# If this behaviour interferes with your use-case, you can remove the metaclass.
class GoogleSheetsAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """Authenticator class for Google Sheets."""

    @property
    def oauth_request_body(self) -> dict:
        """Define the OAuth request body for the GoogleSheets API."""
        return {
            "grant_type": "refresh_token",
            "client_id": self.config.get("client_id"),
            "client_secret": self.config.get("client_secret"),
            "refresh_token": self.config.get("refresh_token"),
        }


class ProxyGoogleSheetsAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    """API Authenticator for Proxy OAuth 2.0 flows."""

    @property
    def oauth_request_body(self) -> dict:
        """Define the OAuth request body for the GoogleAds API."""
        return {}
