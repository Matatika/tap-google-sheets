"""Tests tap setting child_sheet_name."""

import contextlib
import io
import json
import unittest

import responses
import singer_sdk.singerlib as singer

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

        captured_stdout = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout):
            tap.sync_all()

        singer_messages = [
            json.loads(line) for line in captured_stdout.getvalue().splitlines()
        ]

        self.assertEqual(len(singer_messages), 4)
        self.assertEqual(singer_messages[0]["type"], singer.SingerMessageType.SCHEMA)
        self.assertEqual(singer_messages[1]["type"], singer.SingerMessageType.SCHEMA)
        self.assertEqual(singer_messages[2]["type"], singer.SingerMessageType.RECORD)
        self.assertEqual(singer_messages[3]["type"], singer.SingerMessageType.STATE)

        # Assert that data is sycned from the mocked response
        self.assertEqual(
            singer_messages[2]["record"],
            {"Column_One": "1", "Column_Two": "1"},
        )
