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

    @property
    def path(self):
        """Set the path for the stream."""
        path = "spreadsheets/" + self.config.get("sheet_id") + "/"
        path = path + "values/" + "Sheet1"  # self.config.get("sheet_name")
        if self.config.get("range"):
            path = path + "!" + self.config.get("range")
        return path

    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse response, build response back up into json, update stream schema."""
        headings = response.json()["values"][0]
        data = response.json()["values"][1:]
        data_rows = []

        for values in data:
            data_rows.append(dict(zip(headings, values)))

        if not self.sheet_headings:
            properties = []
            for column in headings:
                properties.append(th.Property(column, th.StringType()))

            self.schema = th.PropertiesList(*properties).to_dict()
            self.sheet_headings = headings

        yield from extract_jsonpath(self.records_jsonpath, input=data_rows)
