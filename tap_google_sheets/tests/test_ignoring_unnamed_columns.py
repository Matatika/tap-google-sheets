"""Tests standard tap features using the built-in SDK tests library."""

import unittest

import responses
import singer

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestCore(unittest.TestCase):
    """Test class for core tap tests."""

    def setUp(self):
        self.mock_config = test_utils.MOCK_CONFIG

        responses.reset()
        del test_utils.SINGER_MESSAGES[:]

        singer.write_message = test_utils.accumulate_singer_messages

    @responses.activate()
    def test_ignoring_unnamed_columns(self):

        self.missing_column_response = {
            "values": [["Column_One", "", "Column_Two"], [1, 1, 1]]
        }

        tap = TapGoogleSheets(config=self.mock_config)

        """Run standard tap tests from the SDK."""
        responses.add(
            responses.POST,
            "https://oauth2.googleapis.com/token",
            json={"access_token": "new_token"},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://www.googleapis.com/drive/v2/files/12345",
            json={"title": "test"},
            status=200,
        ),
        responses.add(
            responses.GET,
            "https://sheets.googleapis.com/v4/spreadsheets/12345/values/Sheet1",
            json=self.missing_column_response,
            status=200,
        )

        tap.sync_all()

        self.assertEqual(len(test_utils.SINGER_MESSAGES), 7)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[0], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[1], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[2], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[3], singer.RecordMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[4], singer.StateMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[5], singer.RecordMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[6], singer.StateMessage)

        self.assertEquals(
            test_utils.SINGER_MESSAGES[3].record, {"Column_One": 1, "Column_Two": 1}
        )

        self.assertEquals(test_utils.SINGER_MESSAGES[5].record, {"title": "test"})
