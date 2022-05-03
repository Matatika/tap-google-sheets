# tap-google-sheets

[![test](https://github.com/matatika/tap-google-sheets/actions/workflows/ci_workflow.yml/badge.svg)](https://github.com/matatika/tap-google-sheets/actions/workflows/ci_workflow.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<a href="https://github.com/Matatika/tap-google-sheets/blob/master/LICENSE"><img alt="GitHub license" src="https://img.shields.io/github/license/Matatika/tap-google-sheets"></a>
[![Python](https://img.shields.io/static/v1?logo=python&label=python&message=3.7%20|%203.8%20|%203.9&color=blue)]()

This Google Sheets tap produces JSON-formatted data following the Singer spec.

`tap-google-sheets` is a Singer tap for the Google [Sheets API](https://developers.google.com/sheets/api?hl=en_GB) built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

---

## Configuration

A full list of supported settings and capabilities for this tap is available by running:

```bash
tap-google-sheets --about
```

### Getting Your Credentials

**OAuth**

At [Matatika](https://www.matatika.com/), we have OAuth support for this tap. This means when you sign up and use this tap in one of our workspaces you can go through the Google OAuth flow, allowing the Matatika app access to your Google Sheet to sync data on your behalf.

Using the tap this way means you do not have to get any of the following credentials.

**Client ID, Client Secret & Refresh Token**

To get your google credentials we recommend reading and following the [OAuth 2.0 Google API Documentation](https://developers.google.com/identity/protocols/oauth2)

The tap calls [Method: spreadsheets.values.get](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/get?hl=en_GB), and on that page you can see the **required scopes** your credentials need.


**Sheet ID**

When you open your Google sheet, the url will look something like: 

`https://docs.google.com/spreadsheets/d/abc123/edit#gid=0`

Your `sheet_id` are the characters after `spreadsheets/d/`, so in this case would be `abc123`.

---

### Credentials

Setting | Required | Type | Description |
------- | -------- | ---- | ----------- |
`oauth_credentials.client_id` | Required | String | Your google client id
`oauth_credentials.client_secret` | Required | String | Your google client secret
`oauth_credentials.refresh_token` | Required | String | Your google refresh token
`sheet_id` | Required | String | Your target google sheet id

### Environment Variable

These settings expand into environment variables of:
- `TAP_GOOGLE_SHEETS_OAUTH_CREDENTIALS_CLIENT_ID`
- `TAP_GOOGLE_SHEETS_OAUTH_CREDENTIALS_CLIENT_SECRET`
- `TAP_GOOGLE_SHEETS_OAUTH_CREDENTIALS_REFRESH_TOKEN`
- `TAP_GOOGLE_SHEETS_SHEET_ID`

---

## FAQ / Things to Note

* Currently the tap supports sheets that have the column name in the first row.

(The tap builds a usable json object up by using these column names)

* The tap will skip all columns without a name

* If syncing to a database that all the column names are unique.


---

## Roadmap

- [ ] Add setting to optionally allow renaming the sheet stream name (file or table name output by stream).
- [ ] Add setting to optionally allow the selection of a range of data from a sheet.


- [ ] Improve default behavior of a sheet with multiple columns of the same name and `target-postgres`.

Currently if have duplicate column names, a database will either:
- Throw an error that you can't have two columns with the same name.
- Sync all the data but only persist the data from the last duplicate column into the table.

---

## Installation

Use pip to install a release from GitHub.

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
