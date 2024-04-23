"""Stream type classes for tap-google-sheets."""

import re
from itertools import zip_longest
from pathlib import Path
from typing import Iterable

import requests
from singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_google_sheets.client import GoogleSheetsBaseStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class GoogleSheetsStream(GoogleSheetsBaseStream):
    """Google sheets stream."""

    child_sheet_name = None
    primary_key = None
    url_base = "https://sheets.googleapis.com/v4/spreadsheets"
    stream_config = None

    @property
    def path(self):
        """Set the path for the stream."""
        path = f"/{self.stream_config['sheet_id']}/values/{self.child_sheet_name}"
        sheet_range = self.stream_config.get("range")
        if sheet_range:
            path += f"!{sheet_range}"
        return path

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse response, build response back up into json, update stream schema."""
        headings, *data = response.json()["values"]
        data_rows = []

        # List of true and false based if heading has value
        mask = [bool(x) for x in headings]

        # Build up a json like response using the mask to ignore unnamed columns
        for values in data:
            data_rows.append(
                dict(
                    [
                        (re.sub(r"\s+", "_", h.strip()), v or "")
                        for m, h, v in zip_longest(mask, headings, values)
                        if m
                    ]
                )
            )

        # We have to re apply the streams schema for target-postgres
        for stream_map in self.stream_maps:
            if stream_map.stream_alias == self.name:
                stream_map.transformed_schema = self.schema

        # You have to send another schema message as well for target-postgres
        self._write_schema_message()

        yield from extract_jsonpath(self.records_jsonpath, input=data_rows)
