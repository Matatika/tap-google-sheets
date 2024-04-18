import unittest

from tap_google_sheets.tap import TapGoogleSheets


class TestFirstLineRange(unittest.TestCase):
    def test_first_line_range(self):
        """Test first line range."""
        test_pairs = [
            ("", "1:1"),
            ("1:1", "1:1"),
            ("A1:G", "A1:G1"),
            ("A5:G", "A5:G5"),
            ("A6:GE56", "A6:GE6"),
            ("A6:K38", "A6:K6"),
            ("A4:", "A4:4"),
            ("C:G", "C1:G1"),
        ]
        for test_input, expected in test_pairs:
            stream_config = {"range": test_input}
            self.assertEqual(
                expected, TapGoogleSheets.get_first_line_range(stream_config)
            )

    def test_empty_range(self):
        """Test empty range."""
        stream_config = {}
        self.assertEqual("1:1", TapGoogleSheets.get_first_line_range(stream_config))
