"""google_sheets tap class."""

import re
from typing import List

import requests
from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_google_sheets.client import GoogleSheetsBaseStream
from tap_google_sheets.streams import GoogleSheetsStream


class TapGoogleSheets(Tap):
    """google_sheets tap class."""

    name = "tap-google-sheets"

    per_sheet_config = th.ObjectType(
        th.Property("sheet_id", th.StringType, description="Your google sheet id"),
        th.Property(
            "output_name",
            th.StringType,
            description="Optionally rename your output file or table",
            required=False,
        ),
        th.Property(
            "child_sheet_name",
            th.StringType,
            description=(
                "Optionally sync data from a different sheet in your Google Sheet"
            ),
            required=False,
        ),
        th.Property(
            "key_properties",
            th.ArrayType(th.StringType),
            description="Optionally choose one or more primary key columns",
            required=False,
        ),
    )

    base_config = th.PropertiesList(
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
        th.Property(
            "sheets",
            required=False,
            description="The list of configs for each sheet/stream.",
            wrapped=th.ArrayType(per_sheet_config),
        ),
    )

    for prop in per_sheet_config.wrapped.values():
        # raise Exception(prop.name)
        base_config.append(prop)

    config_jsonschema = base_config.to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        streams: List[Stream] = []

        sheets = self.config.get("sheets") or [self.config]
        for stream_config in sheets:
            stream_name = stream_config.get("output_name") or self.get_sheet_name(
                stream_config
            )
            stream_name = stream_name.replace(" ", "_")
            key_properties = stream_config.get("key_properties", [])

            google_sheet_data = self.get_sheet_data(stream_config)

            stream_schema = self.get_schema(google_sheet_data)

            child_sheet_name = self.config.get(
                "child_sheet_name"
            ) or self.get_first_visible_child_sheet_name(google_sheet_data)

            if stream_name:
                stream = GoogleSheetsStream(
                    tap=self, name=stream_name, schema=stream_schema
                )
                stream.child_sheet_name = child_sheet_name
                stream.selected
                stream.primary_keys = key_properties
                stream.stream_config = stream_config
                streams.append(stream)

        return streams

    def get_sheet_name(self, stream_config):
        """Get the name of the spreadsheet."""
        config_stream = GoogleSheetsBaseStream(
            tap=self,
            name="config",
            schema={"one": "one"},
            path="https://www.googleapis.com/drive/v2/files/"
            + stream_config["sheet_id"],
        )

        prepared_request = config_stream.prepare_request(None, None)

        response: requests.Response = config_stream._request(prepared_request, None)

        return response.json().get("title")

    def get_schema(self, google_sheet_data: requests.Response):
        """Build the schema from the data returned by the google sheet."""
        headings, *data = google_sheet_data.json()["values"]

        schema = th.PropertiesList()
        for column in headings:
            if column:
                schema.append(
                    th.Property(re.sub(r"\s+", "_", column.strip()), th.StringType)
                )

        return schema.to_dict()

    def get_first_visible_child_sheet_name(self, google_sheet_data: requests.Response):
        """Get the name of the first visible sheet in the google sheet."""
        sheet_in_sheet_name = google_sheet_data.json()["range"].rsplit("!", 1)[0]

        return sheet_in_sheet_name

    @staticmethod
    def get_first_line_range(stream_config):
        """Get the range of the first line in the google sheet."""
        first_line_range = "1:1"
        range = stream_config.get("range")
        if range:
            start_column, start_line, end_column, end_line = re.findall(r"^([A-Za-z]*)(\d*):([A-Za-z]*)(\d*)$", range)[0]
            start_column = start_column or ""
            start_line = start_line or "1"
            end_column = end_column or ""

            first_line_range = start_column + start_line + ":" + end_column + start_line
        return first_line_range

    def get_sheet_data(self, stream_config):
        """Get the data from the selected or first visible sheet in the google sheet."""
        config_stream = GoogleSheetsBaseStream(
            tap=self,
            name="config",
            schema={"not": "null"},
            path="https://sheets.googleapis.com/v4/spreadsheets/"
            + stream_config["sheet_id"]
            + "/values/"
            + stream_config.get("child_sheet_name", "")
            + "!" + self.get_first_line_range(stream_config),
        )

        prepared_request = config_stream.prepare_request(None, None)

        response: requests.Response = config_stream._request(prepared_request, None)

        return response
