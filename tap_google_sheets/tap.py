"""google_sheets tap class."""

from typing import List

import requests
from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_google_sheets.client import GoogleSheetsBaseStream
from tap_google_sheets.streams import GoogleSheetsStream


class TapGoogleSheets(Tap):
    """google_sheets tap class."""

    name = "tap-google-sheets"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "oauth_credentials.client_id",
            th.StringType,
            description="Your google client_id",
        ),
        th.Property(
            "oauth_credentials.client_secret",
            th.StringType,
            description="Your google client_secret",
        ),
        th.Property(
            "oauth_credentials.refresh_token",
            th.StringType,
            description="Your google refresh token",
        ),
        th.Property("sheet_id", th.StringType, description="Your google sheet id"),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        streams: List[Stream] = []

        stream_name = self.get_sheet_name()
        stream_schema = self.get_schema()

        if stream_name:
            stream = GoogleSheetsStream(
                tap=self, name=stream_name, schema=stream_schema
            )
            stream.selected
            streams.append(stream)

        return streams

    def get_sheet_name(self):
        """Get the name of the spreadsheet."""
        config_stream = GoogleSheetsBaseStream(
            tap=self,
            name="config",
            schema={"one": "one"},
            path="https://www.googleapis.com/drive/v2/files/" + self.config["sheet_id"],
        )

        prepared_request = config_stream.prepare_request(None, None)

        response: requests.Response = config_stream._request(prepared_request, None)

        return response.json().get("title").lower().replace(" ", "_")

    def get_schema(self):
        """Build the schema from the data returned by the google sheet."""
        config_stream = GoogleSheetsBaseStream(
            tap=self,
            name="config",
            schema={"not": "null"},
            path="https://sheets.googleapis.com/v4/spreadsheets/"
            + self.config["sheet_id"]
            + "/values/Sheet1!1:1",
        )

        prepared_request = config_stream.prepare_request(None, None)

        response: requests.Response = config_stream._request(prepared_request, None)

        headings, *data = response.json()["values"]

        schema = th.PropertiesList()
        for column in headings:
            if column:
                schema.append(th.Property(column.replace(" ", "_"), th.StringType))

        return schema.to_dict()
