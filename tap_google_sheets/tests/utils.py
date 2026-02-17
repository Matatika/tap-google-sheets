"""Test utilities."""

from singer_sdk.helpers import _catalog
from singer_sdk.singerlib.catalog import Catalog

from tap_google_sheets.tap import TapGoogleSheets

SINGER_MESSAGES = []

MOCK_CONFIG = {
    "oauth_credentials": {
        "client_id": "123",
        "client_secret": "123",
        "refresh_token": "123",
    },
    "sheet_id": "12345",
}


def accumulate_singer_messages(_, message):
    """Collect singer library write_message in tests."""
    SINGER_MESSAGES.append(message)


def set_up_tap_with_custom_catalog(mock_config, stream_list):
    """Create an instance of tap-spotify with specific config and streams."""
    tap = TapGoogleSheets(config=mock_config)
    # Run discovery
    tap.run_discovery()
    # Get catalog from tap
    catalog = Catalog.from_dict(tap.catalog_dict)
    # Reset and re-initialize with an input catalog
    _catalog.deselect_all_streams(catalog=catalog)
    for stream in stream_list:
        _catalog.set_catalog_stream_selected(
            catalog=catalog,
            stream_name=stream,
            selected=True,
        )
    # Initialise tap with new catalog
    return TapGoogleSheets(config=mock_config, catalog=catalog.to_dict())
