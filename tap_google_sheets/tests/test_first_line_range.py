import unittest

from singer_sdk.exceptions import ConfigValidationError

from tap_google_sheets.tap import TapGoogleSheets


class TestFirstLineRange(unittest.TestCase):
    def test_first_line_range_valid(self):
        """Test first line range."""
        test_pairs = [
            ("D5", "D5:D5"),
            ("1:1", "1:1"),
            ("5:8", "5:5"),
            ("A1:G", "A1:G1"),
            ("A5:G", "A5:G5"),
            ("A5:7", "A5:5"),
            ("G8:3", "G3:3"),
            ("C:G", "C1:G1"),
            ("2:B5", "2:B2"),
            ("A:B5", "A5:B5"),
            ("A6:GE56", "A6:GE6"),
            ("A6:K38", "A6:K6"),
        ]
        for test_input, expected in test_pairs:
            stream_config = {"range": test_input}
            self.assertEqual(
                expected, TapGoogleSheets.get_first_line_range(stream_config)
            )

    def test_invalid_range(self):
        """Test invalid range."""
        test_values = ["", "invalid", "A:G:5", "A:", ":G", "5:", ":3", "A:5"]
        for test_input in test_values:
            stream_config = {"range": test_input}
            with self.assertRaises(ConfigValidationError):
                TapGoogleSheets.get_first_line_range(stream_config)

    def test_empty_range(self):
        """Test empty range."""
        stream_config = {}
        self.assertEqual("1:1", TapGoogleSheets.get_first_line_range(stream_config))
