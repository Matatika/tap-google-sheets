"""Tests discovered stream names are returned underscored."""

import unittest

import responses
import singer_sdk.io_base as io

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestDiscoveredStreamName(unittest.TestCase):
    """Test class for discovered stream name."""

    def setUp(self):
        self.mock_config = test_utils.MOCK_CONFIG

        responses.reset()
        del test_utils.SINGER_MESSAGES[:]

        io.singer_write_message = test_utils.accumulate_singer_messages

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
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
            json={"range": "Sheet1!1:1", "values": [["Column One", "Column Two"]]},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/Sheet1",
            json=self.column_response,
            status=200,
        )

        tap = TapGoogleSheets(config=self.mock_config)

        tap.sync_all()

        # Assert the returned stream name is lowercase and underscored
        self.assertEqual(tap.discover_streams()[0].name, "File_Name_One")
