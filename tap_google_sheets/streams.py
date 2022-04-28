"""Stream type classes for tap-google-sheets."""

from pathlib import Path
from typing import Iterable

import requests
from singer_sdk import typing as th
from singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_google_sheets.client import GoogleSheetsBaseStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class GoogleSheetsStream(GoogleSheetsBaseStream):
    """Google sheets stream."""

    sheet_headings = None
    name = "spreadsheetstwo"
    primary_key = None

    # Start with empty schema then update in parse_response
    schema = th.PropertiesList().to_dict()

    # @property
    # def path(self):
    #     """Set the path for the stream."""
    #     path = "spreadsheets/" + self.config.get("sheet_id") + "/"
    #     path = path + "values/" + "Sheet1"  # self.config.get("sheet_name")
    #     if self.config.get("range"):
    #         path = path + "!" + self.config.get("range")
    #     return path

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse response, build response back up into json, update stream schema."""
        headings, *data = response.json()["values"]
        data_rows = []

        mask = [bool(x) for x in headings]

        for values in data:
            data_rows.append(
                dict([(h, v) for m, h, v in zip(mask, headings, values) if m])
            )

        if not self.sheet_headings:
            properties = []
            for column in headings:
                if column:
                    properties.append(th.Property(column, th.StringType()))

            self.schema = th.PropertiesList(*properties).to_dict()

            for stream_map in self.stream_maps:
                if stream_map.stream_alias == self.name:
                    stream_map.transformed_schema = self.schema

            self.sheet_headings = headings

            self._write_schema_message()

        yield from extract_jsonpath(self.records_jsonpath, input=data_rows)
