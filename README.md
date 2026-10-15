# MedEasy AI — OpenAI edition (v2.0)

Updated from your attached final app. Python 3.11.4-compatible source, with PDF,
DOCX, TXT, camera/photo OCR, review, consent, source quotes and text download.
The explanation retains exactly SUMMARY, ACTION REQUIRED and IMPORTANT DETAILS.

## Run in VS Code

Extract the ZIP into a new folder and open that folder in VS Code.
Create an environment with Python 3.11:

```bash
python -m venv .venv
```

Activate it (`.venv\Scripts\Activate.ps1` on Windows PowerShell or
`source .venv/bin/activate` on macOS/Linux), then run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Before explaining a letter, edit the included `.env`:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=180
```

Use your own OpenAI platform API key. No working key is included.
Restart the app after changing settings. Old provider keys/settings are not used.

## Streamlit Community Cloud

1. Put the extracted CONTENTS at the GitHub repository root: `app.py`,
   `requirements.txt`, `packages.txt`, `medeasy/`, `assets/`, `examples/`, and
   `.streamlit/config.toml`. The ZIP has no containing folder.
2. Do not upload `.env`, a real `secrets.toml`, patient files or `.venv`.
   `.gitignore` handles Git commits, but manual browser uploads need care.
3. Create a Streamlit app with entry point **app.py**. Select **Python 3.11**
   in Advanced settings. Cloud selects the patch release; `.python-version`
   documents the local target, not Cloud's interpreter selection.
4. Paste the following into Streamlit's Secrets settings (TOML syntax):

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4.1-mini"
OPENAI_TIMEOUT_SECONDS = "180"
```

5. Deploy/reboot. Click **Check API connection**, then test the fictional example.
   The catalog check verifies connectivity and key access, not a successful
   completion. Explaining the example makes a billable API request.

Keep `packages.txt` at the repository ROOT so Cloud installs Tesseract and
English/German language data. Keep `.streamlit/config.toml` at that root too.
If the build fails, share the first error from Manage app → logs, without secrets
or patient information. This package has not been deployed to your account.

## OCR locally

Text PDFs do not need OCR. Photos and scanned PDF pages require Tesseract on the
app server. On Debian/Ubuntu install `tesseract-ocr`, `tesseract-ocr-eng` and
`tesseract-ocr-deu`. On macOS use Homebrew's `tesseract` and `tesseract-lang`.
For Windows, use the installer linked from
https://tesseract-ocr.github.io/tessdoc/Installation.html and optionally set:

```dotenv
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
```

Do not copy this Windows setting into Cloud Secrets. Camera access needs browser
permission and localhost or HTTPS. Photo upload is available if the camera fails.
Review OCR carefully, especially doses, dates and amounts, before submitting.

## OpenAI integration

The app calls `https://api.openai.com/v1/chat/completions` using Bearer authentication,
strict JSON-schema output, `max_completion_tokens=7000`, and `store=false`.
It uses Python's HTTPS client, so no OpenAI SDK dependency is required.
The default `gpt-4.1-mini` supports Chat Completions and structured output.
Use an account with access to this model. Changing to another model may require
request-parameter changes; arbitrary models are not guaranteed compatible.
`python scripts/list_models.py` lists models using your local environment key.

Secrets precedence is Streamlit Secrets → process environment → local `.env`.
Root-level Streamlit Secrets are also exposed as environment variables, including
optional `OPENAI_TIMEOUT_SECONDS` (30–600) and `OPENAI_CA_BUNDLE` (a trusted CA
file supplied by your administrator). TLS verification remains enabled. There
are no automatic paid retries. A timeout does not establish whether a request
was processed or billed.

401: check the key. 403: check permissions/model access. 404: check model ID.
429: check OpenAI API quota/billing and request limits. 400: check model support
for the request schema. Network diagnostics identify DNS/TLS/proxy/timeout issues.

## Preserved behavior and limitations

This conversion preserves the attached final app's explanation logic, including
its manual retry guidance and exact source-number lines. The prompt requests
exact dates, amounts and reference numbers, but the supplied final version no
longer enforces numeric matching for generated claims. Two existing regression
tests expecting rejection of invented numbers fail. This is a known inherited
limitation, not proof of factual accuracy. Source IDs/quotes are checked, but a
real cited passage may still be misinterpreted. Compare the result with the letter;
the app does not diagnose, authenticate documents or establish payment status.

PDF/image bytes are processed on the app server. Reviewed text is sent to OpenAI
only after consent. `store=false` is not a promise of zero retention; review
OpenAI's API data controls and your hosting arrangements. The app has no built-in
login or per-user spending limits. Keep access and API spending controlled.

## Verification

```bash
python -m unittest discover -s tests -v
```

See VALIDATION.md for actual results and remaining checks. Tests mock API calls;
no real medical text or API key is included in the archive.

## Official references

- https://developers.openai.com/api/docs/models/gpt-4.1-mini
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
- https://developers.openai.com/api/docs/guides/your-data
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
