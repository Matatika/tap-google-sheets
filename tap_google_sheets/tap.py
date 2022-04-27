"""google_sheets tap class."""

from typing import List

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_google_sheets.streams import GoogleSheetsStream

STREAM_TYPES = [
    GoogleSheetsStream,
]


class TapGoogleSheets(Tap):
    """google_sheets tap class."""

    name = "tap-google-sheets"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "client_id",
            th.StringType,
            required=True,
            description="Your google client_id",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=True,
            description="Your google client_secret",
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            required=True,
            description="Your google refresh token",
        ),
        th.Property("sheet_id", th.StringType, description="Your google sheet id"),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
