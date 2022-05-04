"""Tests standard tap features using the built-in SDK tests library."""

import unittest

import responses
from singer_sdk.testing import get_standard_tap_tests

import tap_google_sheets.tests.utils as test_utils
from tap_google_sheets.tap import TapGoogleSheets


class TestCore(unittest.TestCase):
    """Test class for core tap tests."""

    def setUp(self):
        # reset mock responses
        responses.reset()

        self.mock_config = test_utils.MOCK_CONFIG

    def test_base_credentials_discovery(self):
        """Test basic discover sync"""

        catalog = TapGoogleSheets(self.mock_config).discover_streams()

        # expect valid catalog to be discovered
        self.assertEqual(len(catalog), 2, "Total streams from default catalog")

    # Run standard built-in tap tests from the SDK:
    @responses.activate()
    def test_standard_tap_tests(self):
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
            json={"values": [["1"], ["2"]]},
            status=200,
        )

        tests = get_standard_tap_tests(TapGoogleSheets, config=self.mock_config)
        for test in tests:
            test()
