"""Tests tap setting key_properties."""

import unittest

import responses

from tap_google_sheets.tap import TapGoogleSheets


class TestKeyPropertiesSetting(unittest.TestCase):
    """Test class for tap setting key_properties"""

    def setUp(self):
        self.mock_config = {
            "oauth_credentials": {
                "client_id": "123",
                "client_secret": "123",
                "refresh_token": "123",
            },
            "sheet_id": "12345",
        }
        self.mock_config["key_properties"] = ["column_one", "column_two"]

    @responses.activate()
    def test_key_properties_being_set_in_stream(self):
        """"""
        self.column_response = {"values": [["Column One", "Column Two"], ["1", "1"]]}

        responses.add(
            responses.POST,
            "https://oauth2.googleapis.com/token",
            json={"access_token": "new_token"},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://www.googleapis.com/drive/v2/files/12345",
            json={"title": "File Name One"},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
            json={
                "range": "!1:1",
                "values": [["Column One", "Column Two"]],
            },
            status=200,
        )

        tap = TapGoogleSheets(config=self.mock_config)

        # Assert that the key_properties in a stream is equal to the setting key_properties
        for stream in tap.catalog_dict.get("streams"):
            self.assertEquals(stream.get("key_properties"), tap.config.get("key_properties"))
        