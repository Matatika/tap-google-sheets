"""Tests column names are returned underscored."""

import unittest

import responses
import json
import singer_sdk._singerlib as singer

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestUnderscoringColumnNamed(unittest.TestCase):
    """Test class for testing column naming."""

    def setUp(self):
        self.mock_config = test_utils.MOCK_CONFIG

        responses.reset()
        del test_utils.SINGER_MESSAGES[:]

        singer.write_message = test_utils.accumulate_singer_messages

    @responses.activate()
    def test_underscoring_column_names(self):
        self.column_response = {
            "values": [
                [
                    "Column One",
                    " Column Two",
                    "   Column Three   ",
                    "Column\nFour",
                    "Column  \n\tFive\n\n\t  ",
                    "Multi Column One",
                    "  Multi Column  Two ",
                    "\tMulti \r\nColumn\f\vThree",
                ], ["1"] * 8
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
            json={"range": "Sheet1!1:1", "values": [self.column_response["values"][0]]},
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

        self.assertEqual(len(test_utils.SINGER_MESSAGES), 4)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[0], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[1], singer.SchemaMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[2], singer.RecordMessage)
        self.assertIsInstance(test_utils.SINGER_MESSAGES[3], singer.StateMessage)

        # Assert that column names have been underscored
        self.assertEquals(
            test_utils.SINGER_MESSAGES[2].record,
            {
                "Column_One": "1",
                "Column_Two": "1",
                "Column_Three": "1",
                "Column_Four": "1",
                "Column_Five": "1",
                "Multi_Column_One": "1",
                "Multi_Column_Two": "1",
                "Multi_Column_Three": "1",
            },
        )
