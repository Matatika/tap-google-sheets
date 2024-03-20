"""Tests that the tap ignores columns with no name"""

import unittest

import responses
import singer_sdk.io_base as io
import singer_sdk._singerlib as singer

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestIgnoringUnnamedColumns(unittest.TestCase):
    """Test class for ignoring unnamed columns."""

    def setUp(self):
        self.mock_config = test_utils.MOCK_CONFIG

        responses.reset()
        del test_utils.SINGER_MESSAGES[:]

        io.singer_write_message = test_utils.accumulate_singer_messages

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

        tap.sync_all()

        self.assertEqual(len(test_utils.SINGER_MESSAGES), 6)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[0], singer.StateMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[1], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[2], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[3], singer.RecordMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[4], singer.RecordMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[5], singer.StateMessage)

        # Assert that the second unnamed column and its values are ignored
        self.assertEquals(
            test_utils.SINGER_MESSAGES[3].record, {"Column_One": "1", "Column_Two": "1"}
        )

        self.assertEquals(
            test_utils.SINGER_MESSAGES[4].record, {"Column_One": "2", "Column_Two": "2"}
        )
