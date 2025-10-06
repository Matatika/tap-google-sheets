"""REST client handling, including google_sheetsStream base class."""

from pathlib import Path
from random import random
from typing import Any, Dict, Iterable, Optional

import requests
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream
from typing_extensions import override

from tap_google_sheets.auth import (
    GoogleSheetsAuthenticator,
    ProxyGoogleSheetsAuthenticator,
)

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class GoogleSheetsBaseStream(RESTStream):
    """google_sheets stream class."""

    url_base = ""

    records_jsonpath = "$[*]"  # Or override `parse_response`.
    next_page_token_jsonpath = "$.next_page"  # Or override `get_next_page_token`.

    @property
    def authenticator(self):
        """Return a new authenticator object."""
        base_auth_url = "https://oauth2.googleapis.com/token"

        oauth_credentials = self.config.get("oauth_credentials", {})

        client_id = oauth_credentials.get("client_id")
        client_secret = oauth_credentials.get("client_secret")
        refresh_token = oauth_credentials.get("refresh_token")

        if client_id and client_secret and refresh_token:
            return GoogleSheetsAuthenticator(stream=self, auth_endpoint=base_auth_url)

        auth_body = {}
        auth_headers = {}

        auth_body["refresh_token"] = oauth_credentials.get("refresh_token")
        auth_body["grant_type"] = "refresh_token"

        auth_headers["authorization"] = oauth_credentials.get("refresh_proxy_url_auth")
        auth_headers["Content-Type"] = "application/json"
        auth_headers["Accept"] = "application/json"

        return ProxyGoogleSheetsAuthenticator(
            stream=self,
            auth_endpoint=oauth_credentials.get("refresh_proxy_url"),
            auth_body=auth_body,
            auth_headers=auth_headers,
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        # TODO: If pagination is required, return a token which can be used to get the
        #       next page. If this is the final page, return "None" to end the
        #       pagination loop.
        if self.next_page_token_jsonpath:
            all_matches = extract_jsonpath(
                self.next_page_token_jsonpath, response.json()
            )
            first_match = next(iter(all_matches), None)
            next_page_token = first_match
        else:
            next_page_token = response.headers.get("X-Next-Page", None)

        return next_page_token

    def get_url_params(self, context, next_page_token) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        if next_page_token:
            params["page"] = next_page_token
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        return params

    def prepare_request_payload(self, context, next_page_token) -> Optional[dict]:
        """Prepare the data payload for the REST API request.

        By default, no payload will be sent (return None).
        """
        # TODO: Delete this method if no payload is required. (Most REST APIs.)
        return None

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result rows."""
        # TODO: Parse response body and return a set of records.
        yield from extract_jsonpath(self.records_jsonpath, input=response.json())

    def backoff_jitter(self, value: float):
        jitter = random.uniform(0, 1)
        return value + jitter

    @override
    def backoff_max_tries(self):
        return 8
