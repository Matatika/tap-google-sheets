# tap-google-sheets

This Google Sheets tap produces JSON-formatted data following the Singer spec.

`tap-google-sheets` is a Singer tap for the Google [Sheets API](https://developers.google.com/sheets/api?hl=en_GB) built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

---

## Configuration

A full list of supported settings and capabilities for this tap is available by running:

```bash
tap-google-sheets --about
```

### Getting Your Credentials

**Client ID, Client Secret & Refresh Token**

To get your google credentials we reccommend reading and following the [OAuth 2.0 Google API Documentation](https://developers.google.com/identity/protocols/oauth2)

The tap calls [Method: spreadsheets.values.get](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/get?hl=en_GB), and on that page you can see the **required scopes** your credentials need.


**Sheet ID**

When you open your Google sheet, the url will look something like: 

`https://docs.google.com/spreadsheets/d/abc123/edit#gid=0`

Your `sheet_id` are the characters after `spreadsheets/d/`, so in this case would be `abc123`.

---

### Credentials

Setting | Required | Type | Description |
------- | -------- | ---- | ----------- |
`client_id` | Required | String | Your google client id
`client_secret` | Required | String | Your google client secret
`refresh_token` | Required | String | Your google refresh token
`sheet_id` | Required | String | Your target google sheet id

---

## Installation

Use pip to pinstall a release from GitHub.

```bash
pip install git+https://github.com/Matatika/tap-shopify@vx.x.x
```

## Usage

You can easily run `tap-google-sheets` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-google-sheets --version
tap-google-sheets --help
tap-google-sheets --config CONFIG --discover > ./catalog.json
```

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_google_sheets/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-google-sheets` CLI interface directly using `poetry run`:

```bash
poetry run tap-google-sheets --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-google-sheets
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-google-sheets --version
# OR run a test `elt` pipeline:
meltano elt tap-google-sheets target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to 
develop your own taps and targets.
