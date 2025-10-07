import unittest
import responses
from tap_google_sheets.tap import TapGoogleSheets
import tap_google_sheets.tests.utils as test_utils


class TestRetryOfDiscoveredStreams(unittest.TestCase):
    def setUp(self):
        self.mock_config = test_utils.MOCK_CONFIG
        responses.reset()
        del test_utils.SINGER_MESSAGES[:]
        TapGoogleSheets.write_message = test_utils.accumulate_singer_messages

    @responses.activate
    def test_retry_of_discovered_streams(self):
        """Ensure the tap retries when it receives a 429."""

        sheet_id = "12345"
        self.column_response = {"values": [["Column One", "Column Two"], ["1", "1"]]}

        # Mock OAuth token request
        responses.add(
            responses.POST,
            "https://oauth2.googleapis.com/token",
            json={"access_token": "mocked_token", "expires_in": 3600},
            status=200,
        )

        responses.add(
            responses.GET,
            f"https://www.googleapis.com/drive/v2/files/{sheet_id}",
            json={"title": "File Name One"},
            status=200,
        )

        # First Sheets API request returns 429 to trigger retry
        responses.add(
            responses.GET,
            f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/!1:1",
            status=429,
        )

        # Second Sheets API request returns 200 (success after retry)
        responses.add(
            responses.GET,
            f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/!1:1",
            json={"range": "Sheet1!1:1", "values": [["Column One", "Column Two"]]},
            status=200,
        )

        # Mock full sheet data
        responses.add(
            responses.GET,
            f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/Sheet1",
            json=self.column_response,
            status=200,
        )
        tap = TapGoogleSheets(config=self.mock_config)

        # Call the method that triggers the request
        tap.sync_all()

        # Assert the returned stream name is correct
        self.assertEqual(tap.discover_streams()[0].name, "File_Name_One")
        # check that a retry happened by confirming both Sheets API responses occurred
        sheet_requests = [
            call
            for call in responses.calls
            if "sheets.googleapis.com/v4/spreadsheets" in call.request.url
        ]
        self.assertGreaterEqual(len(sheet_requests), 2)
