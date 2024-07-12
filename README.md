# tap-google-sheets

[![test](https://github.com/matatika/tap-google-sheets/actions/workflows/ci_workflow.yml/badge.svg)](https://github.com/matatika/tap-google-sheets/actions/workflows/ci_workflow.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<a href="https://github.com/Matatika/tap-google-sheets/blob/master/LICENSE"><img alt="GitHub license" src="https://img.shields.io/github/license/Matatika/tap-google-sheets"></a>
[![Python version](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FMatatika%2Ftap-google-sheets%2Fmaster%2Fpyproject.toml&query=tool.poetry.dependencies.python&label=python)](https://docs.python.org/3/)

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

The tap calls the following Google APIs, these need to be enabled in Google Cloud Console
- [spreadsheets.values.get](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/get?hl=en_GB)
- [drive.files.get](https://developers.google.com/drive/api/reference/rest/v3/files/get)

Consent for these scopes needs to be supplied in **required scopes** during OAuth client creation and requested in your authorization flow.

```
https://www.googleapis.com/auth/spreadsheets.readonly https://www.googleapis.com/auth/drive.readonly
```


**Sheet ID**

Your `sheet_id` is also required to run `--discover`, as running this will build the streams schema based on your google sheet.

When you open your Google sheet, the url will look something like: 

`https://docs.google.com/spreadsheets/d/abc123/edit#gid=0`

Your `sheet_id` are the characters after `spreadsheets/d/`, so in this case would be `abc123`.

---

### Credentials

Setting | Required | Type             | Description |
------- | -------- |------------------| ----------- |
`oauth_credentials.client_id` | Required | String           | Your google client id
`oauth_credentials.client_secret` | Required | String           | Your google client secret
`oauth_credentials.refresh_token` | Required | String           | Your google refresh token
`sheet_id` | Required | String           | Your target google sheet id
`output_name` | Optional | String           | Optionailly rename the stream and output file or table from the tap
`child_sheet_name` | Optional | String           | Optionally choose a different sheet from your Google Sheet file
`range` | Optional | String | Optionally choose a range of data from your Google Sheet file (defaults to the entire sheet)<br><br>Range is defined using [A1 notation](https://developers.google.com/sheets/api/guides/concepts#expandable-1) and is start/end inclusive. Examples:<ul><li>`B5:G45` - start at `B5` and end at `G45`</li><li>`A:T` - start at `A1` and end at the last cell of column `T` (same as `A1:T` and `A:T1`)</li><li>`3:5` - start at `A3` and end at the last cell of row `5` (same as `A3:5` and `3:A5`)</li><li>`D3:ZZZ` - start at `D3` and end at the last cell in the sheet</li></ul>
`key_properties` | Optional | Array of Strings | Optionally choose primary key column(s) from your Google Sheet file. Example: `["column_one", "column_two"]`
`sheets` | Optional | Array of Objects | Optionally provide a list of configs for each sheet/stream. See "Per Sheet Config" below. Overrides the `sheet_id` provided at the root level.

### Per Sheet Config

Setting | Required | Type | Description |
------- | -------- | ---- | ----------- |
`sheet_id` | Required | String | Your target google sheet id
`output_name` | Optional | String | Optionailly rename the stream and output file or table from the tap
`child_sheet_name` | Optional | String | Optionally choose a different sheet from your Google Sheet file
`range` | Optional | String | Optionally choose a range of data from your Google Sheet file (defaults to the entire sheet)<br><br>Range is defined using [A1 notation](https://developers.google.com/sheets/api/guides/concepts#expandable-1) and is start/end inclusive. Examples:<ul><li>`B5:G45` - start at `B5` and end at `G45`</li><li>`A:T` - start at `A1` and end at the last cell of column `T` (same as `A1:T` and `A:T1`)</li><li>`3:5` - start at `A3` and end at the last cell of row `5` (same as `A3:5` and `3:A5`)</li><li>`D3:ZZZ` - start at `D3` and end at the last cell in the sheet</li></ul>
`key_properties` | Optional | Array of Strings | Optionally choose primary key column(s) from your Google Sheet file. Example: `["column_one", "column_two"]`

### Environment Variable

These settings expand into environment variables of:
- `TAP_GOOGLE_SHEETS_OAUTH_CREDENTIALS_CLIENT_ID`
- `TAP_GOOGLE_SHEETS_OAUTH_CREDENTIALS_CLIENT_SECRET`
- `TAP_GOOGLE_SHEETS_OAUTH_CREDENTIALS_REFRESH_TOKEN`
- `TAP_GOOGLE_SHEETS_SHEET_ID`
- `TAP_GOOGLE_SHEETS_OUTPUT_NAME`
- `TAP_GOOGLE_SHEETS_CHILD_SHEET_NAME`
- `TAP_GOOGLE_SHEETS_RANGE`
- `TAP_GOOGLE_SHEETS_KEY_PROPERTIES`
- `TAP_GOOGLE_SHEETS_SHEETS`

---

## FAQ / Things to Note

* If you do not provide a `child_sheet_name`, the tap will find the first visible sheet in your Google Sheet and try to sync the data from there.

* You need to provide all the required settings for this tap to run the it. These settings are used to generate the stream and schema for the tap to use from your Google Sheet.

* Currently the tap supports sheets that have the column name in the first row. (The tap builds a usable json object up by using these column names).

* The tap will skip all columns without a name. (The tap builds a usable json object up by using these column names).

* If syncing to a database it will not respect duplicated column names. The last column with the same name will be the only one synced along with its data.

* The tap will use your Google Sheet's name as output file or table name unless you set an `output_name`. It will replace any spaces with underscores.

* The tap will again replace any spaces in column names with underscores.

* When using the `key_properties` setting, you must choose columns with no null values.

* You can extract multiple sheets using the `sheets` config, which is just an array containing configurable properties for each item. Doing so will ignore any sheet config defined by the root level `sheet_id`, `output_name`, `child_sheet_name`, `key_properties` properties.

### Loaders Tested

- [target-jsonl](https://hub.meltano.com/targets/jsonl)
- [target-csv](https://hub.meltano.com/targets/csv)
- [target-postgres transferwise variant](https://hub.meltano.com/targets/postgres)
- [target-snowflake meltano variant (matatika fork)](https://hub.meltano.com/targets/snowflake--meltano) - Does not like numbers as column names


---

## Roadmap

- [x] Add setting to optionally allow the selection of a range of data from a sheet. (Add an optional range setting).

- [ ] Improve default behavior of a sheet with multiple columns of the same name and `target-postgres`.

Currently if have duplicate column names, a database will either:
- Throw an error that you can't have two columns with the same name.
- Sync all the data but only persist the data from the last duplicate column into the table.

---

## Installation

Use pip to install a release from GitHub.

```bash
pip install git+https://github.com/Matatika/tap-google-sheets@vx.x.x
```

## Usage

You can easily run `tap-google-sheets` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-google-sheets --version
tap-google-sheets --help
tap-google-sheets --config CONFIG --discover > ./catalog.json
```

Note: to run `--discover` you need to have set the required tap settings found [here](#configuration).

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
