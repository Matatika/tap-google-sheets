"""Tests that the tap ignores columns with no name"""

import contextlib
import io
import json
import unittest

import responses

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestIgnoringUnnamedColumns(unittest.TestCase):
    """Test class for ignoring unnamed columns."""

    def setUp(self):
        self.mock_config = test_utils.MOCK_CONFIG

        responses.reset()

    @responses.activate()
    def test_ignoring_unnamed_columns(self):
        self.missing_column_response = {
            "values": [
                ["Column_One", "", "Column_Two"],
                ["1", "1", "1"],
                ["2", "2", "2"],
            ]
        }

        responses.add(
            responses.POST,
            "https://oauth2.googleapis.com/token",
            json={"access_token": "new_token"},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://www.googleapis.com/drive/v2/files/12345",
            json={"title": "file_name"},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/!1:1",
            json={"range": "Sheet1!1:1", "values": [["Column_One", "", "Column_Two"]]},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/Sheet1",
            json=self.missing_column_response,
            status=200,
        )

        tap = TapGoogleSheets(config=self.mock_config)

        captured_stdout = io.StringIO()
        with contextlib.redirect_stdout(captured_stdout):
            tap.sync_all()

        singer_messages = [
            json.loads(line) for line in captured_stdout.getvalue().splitlines()
        ]

        self.assertEqual(len(singer_messages), 5)
        self.assertEqual(singer_messages[0]["type"], "SCHEMA")
        self.assertEqual(singer_messages[1]["type"], "SCHEMA")
        self.assertEqual(singer_messages[2]["type"], "RECORD")
        self.assertEqual(singer_messages[3]["type"], "RECORD")
        self.assertEqual(singer_messages[4]["type"], "STATE")

        # Assert that the second unnamed column and its values are ignored
        self.assertEqual(
            singer_messages[2]["record"],
            {"Column_One": "1", "Column_Two": "1"},
        )

        self.assertEqual(
            singer_messages[3]["record"],
            {"Column_One": "2", "Column_Two": "2"},
        )
