"""Tests tap setting child_sheet_name."""

import unittest

import responses
import singer_sdk.singerlib as singer

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestChildSheetNameSetting(unittest.TestCase):
    """Test class for tap setting child_sheet_name"""

    def setUp(self):
        self.mock_config = {
            "oauth_credentials": {
                "client_id": "123",
                "client_secret": "123",
                "refresh_token": "123",
            },
            "sheet_id": "12345",
        }
        self.mock_config["child_sheet_name"] = "Test Sheet"

        responses.reset()
        del test_utils.SINGER_MESSAGES[:]

        TapGoogleSheets.write_message = test_utils.accumulate_singer_messages

    @responses.activate()
    def test_discovered_stream_name(self):
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
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/"
            + "Test%20Sheet!1:1",
            json={
                "range": "Test%20Sheet!1:1",
                "values": [["Column One", "Column Two"]],
            },
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/Test%20Sheet",
            json=self.column_response,
            status=200,
        )

        tap = TapGoogleSheets(config=self.mock_config)

        tap.sync_all()

        self.assertEqual(len(test_utils.SINGER_MESSAGES), 5)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[0], singer.StateMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[1], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[2], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[3], singer.RecordMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[4], singer.StateMessage)

        # Assert that data is sycned from the mocked response
        self.assertEqual(
            test_utils.SINGER_MESSAGES[3].record, {"Column_One": "1", "Column_Two": "1"}
        )
