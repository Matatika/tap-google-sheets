"""Stream type classes for tap-google-sheets."""

from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable

from singer_sdk import typing as th

from tap_google_sheets.client import GoogleSheetsBaseStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class GoogleSheetsStream(GoogleSheetsBaseStream):
    """Google sheets stream."""
    # Set as child of GoogleDriveFileList
    # Only use this stream if the file passed is spreadsheet

    @property
    def path(self):
        #path = "https://sheets.googleapis.com/v4/"
        path = "spreadsheets/" + self.config["file_id"] + '/'
        path = path + "values/Sheet1!A1:B6"
        return path

    # @property
    # def schema(self) -> dict:
    #     """Return dictionary of record schema.

    #     Dynamically detect the json schema for the stream.
    #     This is evaluated prior to any records being retrieved.
    #     """
    #     properties: List[th.Property] = []

    #     for file_path in self.get_file_paths():
    #         for header in self.get_rows(file_path):
    #             break
    #         break

    #     for column in header:
    #         # Set all types to string
    #         # TODO: Try to be smarter about inferring types.
    #         properties.append(th.Property(column, th.StringType()))
    #     return th.PropertiesList(*properties).to_dict()

    # def get_url_params(self, context: Optional[dict], next_page_token: Optional[Any]) -> Dict[str, Any]:
    #     super().get_url_params(context, next_page_token)
    #     params = {}
    #     params["mimeType"] = "text/csv"
    #     return params



    name = "spreadsheets"
    #records_jsonpath = "$.values[*]"
    #primary_keys = ["id"]
    primary_keys = None
    #replication_key = "modified"
    schema = th.PropertiesList(
        th.Property("values", th.ArrayType(th.ArrayType(th.StringType)))
    ).to_dict()