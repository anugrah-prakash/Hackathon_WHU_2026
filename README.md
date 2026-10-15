# MedEasy AI

A Python 3.11-compatible Streamlit app that explains diagnoses, discharge letters,
and care plans in simple English through TrustedTokens. It displays and exports
exactly these explanation sections. You can now photograph a document or upload a
JPEG/PNG photo, then check the extracted text before explaining it:


1. SUMMARY — one simple sentence.
2. ACTION REQUIRED — actions, deadlines, medicines and payments stated in the letter.
3. IMPORTANT DETAILS — essential facts, uncertainty, missing information, and optional supported FAQs.

The interface uses a clean, spacious, card-based design inspired by Reguly, with
an original MedEasy identity, muted green accents, and a light neutral background.
No Reguly logos, assets or claims are copied.

## Update from the earlier ZIP

1. Extract this complete ZIP into a new folder. Keep a secure local copy of your
   existing API key; the included `.env` contains placeholders only.
2. Copy your own API key/model settings into the new `.env` locally.
3. In your virtual environment run:

   ```bash
   python -m pip install --upgrade -r requirements.txt
   ```

   The reader now uses pure-Python `pypdf` first for selectable text. `pypdfium2`
   is loaded only when native extraction needs a fallback or a page needs OCR.
   It does not require installing Poppler. PDFium is protected by a process-wide
   lock because its native API is not thread-safe across Streamlit sessions.
4. Restart Streamlit and upload the PDF again. Select the OCR language if needed.
   Scanned pages require the same Tesseract setup as photos. For Streamlit Cloud,
   commit the updated project, including requirements.txt and packages.txt, and
   reboot the app. Keep your real key in Cloud Secrets, outside the repository.

The supplied four-page PDF was tested locally after this update. All four pages
extract successfully through the native-text path without PDFium or Tesseract.
The screenshot error did not reproduce in this environment, so its exact local
cause remains unconfirmed. A damaged or unsupported PDF can still need a fresh export. The reader attempts
tolerant parsing; compare recovered text with the original before explaining it.

## Start in VS Code

1. Install **Python 3.11.4**, VS Code, and the Microsoft Python extension.
2. Extract this ZIP and open the **medeasy_ai** folder in VS Code. It must be the
   folder containing `app.py` and `requirements.txt`.
3. Open the VS Code terminal. Create and activate a virtual environment:

   **Windows PowerShell**

   ```powershell
   py -3.11 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, skip activation and use
   `.venv\Scripts\python.exe` in place of `python` in the commands below.

   **macOS / Linux**

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

4. Select **Python: Select Interpreter → .venv** in VS Code.
5. Install Python dependencies, then install Tesseract as described under **Photo setup** below:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Open the included `.env` file and replace its placeholder:

   ```dotenv
   TRUSTEDTOKENS_API_KEY=your_real_account_token
   TRUSTEDTOKENS_MODEL=zai-org/GLM-5.3
   ```

   No real key is included. The model shown is the example in the provider's
   documentation, not a guarantee of availability in your account. To list your
   account's current model IDs:

   ```bash
   python scripts/list_models.py
   ```

   Copy an exact supported model ID into `.env`. The app uses structured JSON
   output; select a model/provider combination supporting that feature. Restart
   Streamlit after changing `.env` because existing environment values take priority.

7. Run:

   ```bash
   python -m streamlit run app.py
   ```

   Open the local URL printed in the terminal, usually http://localhost:8501.
   Alternatively, press **F5** with the included **MedEasy AI: Streamlit** launch
   configuration and the Python Debugger extension installed.

8. Choose **Try an example**, review the fictional letter, tick the consent box,
   and click **Explain my letter**. This sends a real API request and may incur
   provider charges. Upload and paste features can be inspected without a key.

## Connection troubleshooting (v1.4)

If **Explain my letter** reports that the AI service cannot be reached, first
click **Check API connection**. This makes an authenticated GET request to the
TrustedTokens model catalog; it does not send patient text or request a completion.
A successful catalog check verifies that this endpoint was reachable with the key;
it does not prove model generation, billing access or structured output will work.
The app warns if the configured model is not in the catalog.

| Diagnostic code | What to check |
| --- | --- |
| CONNECTION-DNS | Your computer/server cannot resolve the API or proxy hostname. Check internet, DNS, VPN and proxy settings. |
| CONNECTION-TLS-CERTIFICATE | Python cannot trust the HTTPS certificate chain. Update OS/Python certificate trust; ask IT about a corporate HTTPS inspection CA. |
| CONNECTION-TLS | Check system time, HTTPS proxy compatibility and certificate installation. |
| CONNECTION-CA-CONFIG | Check the optional custom CA file exists, is readable and contains valid PEM certificates. |
| CONNECTION-TIMEOUT | Check connectivity first. A model may take longer than the configured response timeout; increasing it does not fix DNS or firewall issues. |
| CONNECTION-REFUSED / CONNECTION-RESET | Check firewall, VPN, proxy, service access and provider status. |
| CONNECTION-PROXY / CONNECTION-PROXY-AUTH | Check HTTP_PROXY/HTTPS_PROXY and proxy authentication with your administrator. Never share proxy passwords. |
| API-HTTP-401 | Check the TrustedTokens key in .env or Cloud Secrets. Restart after changes. |
| API-HTTP-403 | Access may be denied by the API or a network gateway. Check both account permissions and network policy. |
| API-HTTP-429 | Check account/request limits and try later. |
| CONNECTION-NETWORK | Share this code and the connection-check result; the underlying reason was not classified. |

The documented API address remains `https://api.trustedtokens.eu/v1`. For a local
Windows reachability check you may run these in PowerShell (no API key required):

```powershell
Resolve-DnsName api.trustedtokens.eu
Test-NetConnection api.trustedtokens.eu -Port 443
```

TCP reachability alone does not verify TLS, authentication or model access. Any
firewall/proxy change should follow your organisation's network policy.

The explanation response timeout now defaults to 180 seconds. For a slow model,
set this in local `.env`, then restart Streamlit:

```dotenv
TRUSTEDTOKENS_TIMEOUT_SECONDS=300
```

Allowed range: 30–600 seconds. The connection-check timeout is independently fixed
at 20 seconds. There are no automatic paid retries. A timeout does not confirm
that the provider stopped processing or charging for the original request.

For corporate HTTPS inspection only, your administrator can supply a trusted CA
certificate file. Add its path locally and restart:

```dotenv
TRUSTEDTOKENS_CA_BUNDLE=C:/certificates/organisation-root-ca.pem
```

The file adds trust to Python's default system certificate context. Do not set it
unless you have the correct CA file. TLS hostname/certificate verification remains
enabled, and authenticated redirects are blocked. Never turn off TLS verification
or post your API key, proxy credentials or patient text while troubleshooting.

The original screenshot did not identify the underlying network failure. These
changes improve diagnosis and allow timeout/CA configuration; they cannot repair
an unreachable service, DNS problem, blocked network or invalid account on their own.

## Photo setup

Python packages alone do not install the Tesseract OCR engine. Paste and document
upload features still work without it; photo reading shows an installation hint.

**Windows:** install Tesseract using the Windows installer linked from the
[official Tesseract installation documentation](https://tesseract-ocr.github.io/tessdoc/Installation.html).
Install English language data, and German data if needed. If `tesseract` is not
on PATH, add this line to your existing `.env` file (adjust the path):

```dotenv
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
```

**macOS (Homebrew):**

```bash
brew install tesseract
# Optional: extra language data, including German
brew install tesseract-lang
```

**Ubuntu / Debian:**

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
```

Verify the installation, then restart Streamlit:

```bash
tesseract --version
tesseract --list-langs
```

The app supports English (`eng`), German (`deu`), and both (`eng+deu`) for OCR.
Choose a language with installed data. The final explanation is always in English.
No additional OCR API key is needed. Tesseract runs on the same server as the app;
image bytes go through stdin and extracted text through stdout, with no intentional
image temporary files or external OCR service.

To use the camera, allow browser camera permission. Camera access normally
requires `localhost` during local testing or HTTPS when hosted. On a phone,
`localhost` means the phone itself; use your HTTPS-hosted app to access the app
from another device. A plain HTTP LAN address may not allow browser camera access.
If the camera is unavailable, take a photo with the phone's camera app and choose
**Take a picture → Upload a photo**. Camera resolution varies by browser/device;
use an uploaded high-resolution photo when the built-in capture misses small text.

Add every page in order with **Read and add this page**. The same image cannot be
added twice. Rotate a sideways photo before reading it. A new photo must be read
and added (or removed) before explaining the current letter. If the wrong page is
added, edit the combined text carefully or use **Clear this letter** to start over.
Changing OCR settings does not reread pages already added. Review the full letter
against all original photos; OCR cannot confirm that you photographed every page.

OCR is best for clear, printed, upright text. It may omit words, mix columns or
misread doses, currency symbols and dates. Handwriting and poor-quality photos
should be transcribed and checked manually. The existing evidence/number checks
compare the explanation with the reviewed OCR text, **not with the original
photo or scanned PDF**, so they cannot detect a transcription mistake that you leave uncorrected.

## Host on Streamlit Community Cloud

1. Create a GitHub repository and upload the project, including `.streamlit/config.toml`.
   **Do not upload `.env`, a real `secrets.toml`, patient letters, or `.venv`.**
   The included `.gitignore` excludes secrets for normal Git operations. Manual
   browser uploads still require you to exclude them yourself.
   Include the new `packages.txt` alongside `requirements.txt`: Community Cloud
   uses it to install Tesseract and the English/German language packs. If the app
   is in a subfolder, keep both files beside `app.py`.
2. In Streamlit Community Cloud, create an app using your repository and branch.
   Set the entry point to `app.py` if the project contents are at the repository
   root, or `medeasy_ai/app.py` if you committed the containing folder.
3. In Advanced settings choose **Python 3.11**, if offered. Community Cloud may
   choose the patch release; `.python-version` records the local 3.11.4 target
   and does not force a particular Cloud interpreter. A newer 3.11 patch release
   is recommended for hosted security fixes.
4. Paste the contents of `.streamlit/secrets.toml.example` into the app's Secrets
   settings, replacing the placeholder with your real key:

   ```toml
   TRUSTEDTOKENS_API_KEY = "your_real_account_token"
   TRUSTEDTOKENS_MODEL = "your_exact_model_id"
   ```

5. Deploy. Try the fictional example before using any patient information.

Secrets precedence: Streamlit Secrets → process environment → project `.env`.
The API URL is fixed to `https://api.trustedtokens.eu/v1`; a document cannot
change the endpoint or access the API key. Authentication is Bearer-token based.
The app never follows API redirects carrying the token.

**Hosting patient data:** this is a development prototype with no built-in user
login, per-user rate limits or clinical validation. Anyone allowed to open the
app can spend the configured API credits. Keep access restricted, set provider
spending limits, and establish appropriate hosting/provider agreements and data
handling arrangements before accepting real patient records. Streamlit hosting
is separate from TrustedTokens; an EU API does not make the whole app EU-hosted
or certify the app's compliance.

## Use the app

- Paste text or upload one PDF, DOCX or UTF-8 TXT file, up to 10 MB.
- PDFs: maximum 20 pages. Tolerant `pypdf` extraction reads native text first,
  without loading PDFium or decoding images such as logos. PDFium is used only
  for fallback native extraction or rendering scanned pages. Pages without native text are
  rendered in memory and read with Tesseract OCR. Text PDFs do not need Tesseract.
  Choose the PDF language if OCR is needed. A blank/unreadable page fails with a
  page-specific message; the app does not silently use a partial document.
- If a PDF combines native text with text inside images, native extraction can
  miss the image text. Enable **Read every PDF page as an image** to OCR the full
  document, then check the transcription. This option requires Tesseract.
- Click **Read file again** after correcting a local OCR installation or to retry
  the same upload. This rereads the document and replaces edits in the review box.
- DOCX: ordinary paragraphs, tables, headers and footers are read. Files with
  images, footnotes, endnotes, comments, body text boxes or tracked body changes
  are rejected rather than silently summarised as complete. Complex Word layouts
  may still extract in an unexpected order. Review is essential.
- Choose **Take a picture** to use the camera or upload a JPEG/PNG photo. Click
  **Read and add this page**, add all pages in order, then review the combined
  text. Up to 20 photos, each no more than 10 MB and 24 megapixels, are supported.
  Photos are read with on-server Tesseract OCR; HEIC and handwriting are not supported.
- Scanned PDFs now use automatic OCR in **Upload a file**. JPEG/PNG photos still
  use **Take a picture**. Both OCR paths require Tesseract on the app server.
- Review and edit the extracted text. Keep its clinical meaning and values intact.
- Confirm consent before the reviewed text is sent to TrustedTokens.
- Read the three sections. Open **Check the source quotes** inside IMPORTANT
  DETAILS to compare the AI's claims with the letter.
- Download the result as plain text. The file can contain sensitive information.
- **Clear this letter** removes the app's session-held inputs and results. It
  cannot erase copies held by providers, infrastructure, or downloaded files.

A letter longer than 40,000 characters is rejected without sending it. The app
does not silently truncate or split medical instructions. If a model has a smaller
context window, use a suitable model; do not remove essential clinical context.

## Accuracy and limitations

The system prompt requires simple English, all deadlines/payment amounts,
verbatim dates/amounts/reference numbers, exact missing-value wording
`Not specified in the letter`, and uncertainty when the text is unclear.
It forbids assuming authenticity, payment status, or adding medical advice.
Missing fields use `Field name: Not specified in the letter`.

The app labels original source passages before sending the letter. Each substantive
generated claim must cite one or more supplied passage IDs; the response schema
restricts these IDs to the current letter. The app retrieves the exact original
text itself for **Check the source quotes**, so the model does not have to copy
PDF line breaks or Unicode spaces. IDs are internal metadata, not medical reference
numbers. The app validates the JSON shape, rejects unknown IDs and unsupported
numeric strings in each claim, and rejects incomplete/refused responses. A malformed
response is not displayed. There are no automatic paid retries; the user may retry.
The SUMMARY formatter keeps the first sentence and moves any remaining sentences
into IMPORTANT DETAILS, preserving their text and source quotes. Common titles,
initials, decimals and dotted dates are recognised to avoid false sentence breaks.
This is a conservative English heuristic, not a complete grammar parser. Source
and numeric validation still run on the full original response before formatting.
No additional API request is made for this adjustment.

IMPORTANT DETAILS also includes every distinct original line containing a number,
in original order. This backstop preserves numeric facts even when the model
omits one. It can include technical text or patient identifiers and can repeat
facts explained above. Dates written entirely in words still depend on the AI
and the user's source review. These lines are source text, not new advice.

**These checks do not prove a claim's meaning, detect every omission, or guarantee
that dates, currencies, medicine instructions or payment status are correct.**
A cited passage can be real yet irrelevant or misinterpreted; valid IDs do not
prove that the passage supports the claim. Prompt injection cannot be eliminated
by a prompt. The model may misunderstand a letter or fail to use the exact missing
wording in every case. Clinical review and representative evaluation are required
before patient use. Always compare with the original, especially medications and
urgent return instructions. The app cannot diagnose, authenticate a letter or
confirm a payment. It provides no independent treatment recommendations.

The app does not intentionally persist patient data to disk, a database, logging,
or a shared cache. Streamlit holds inputs/results in session memory. Uploads reach
the hosting server; reviewed text reaches TrustedTokens after consent. Hosting,
network, and provider processing/retention remain subject to their policies.
Dependencies may emit parser diagnostics; operate with appropriate restricted log
access. No telemetry SDK or external web font is included; Streamlit usage stats
are disabled.

## Tests

Run from the project folder:

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py medeasy scripts tests
```

The suite tests strict output shape, source grounding, amount/date/reference
checks, missing fields, exact numeric-line retention, API request format with
mocked transport, timeouts, incomplete responses, input limits, corrupt files,
PDF text/encryption handling, logo images, nonstandard headers, mixed native/scanned
pages, full-page OCR, failed-page handling, and Word table/header order. It makes no live API
calls and needs no patient data. OCR tests use mocked failures and a real
Tesseract check with a synthetic image when Tesseract is installed; the real-engine
check is skipped if Tesseract is absent. Dependencies from `requirements.txt` are needed
for document tests. No separate test framework is required.

For a real integration check, run the app with your own key and the fictional
example. Confirm the follow-up deadline is **21 October 2026**, payment is
**£15.00** by **28 October 2026**, reference is **MED-2026-0042**, and payment is
not described as confirmed. Test missing and contradictory details before use.

## Project files

```text
medeasy_ai/
  app.py                         Streamlit interface and session handling
  requirements.txt               Pinned direct dependencies
  packages.txt                   Cloud Tesseract engine and language packs
  CHANGELOG.md                   Camera update details
  .env                           Local key placeholder; never commit a real key
  .env.example                   Reusable environment template
  .gitignore                     Secret and virtual-environment exclusions
  .python-version                Local target: 3.11.4
  .vscode/launch.json             F5 Streamlit debugger configuration
  .vscode/extensions.json         Suggested editor extensions
  .streamlit/config.toml         Theme, upload limit and telemetry settings
  .streamlit/secrets.toml.example Cloud secrets template
  assets/style.css               Responsive MedEasy theme
  medeasy/config.py              Environment and Cloud secrets loading
  medeasy/network.py             Verified HTTPS and safe connection diagnostics
  medeasy/connection.py          Model catalog connection check (no letter text)
  medeasy/documents.py           Document routing and Word/text extraction
  medeasy/pdf_reader.py          Native Python text first, rendering/OCR fallback
  medeasy/ocr.py                 Photo validation, OCR and page combination
  medeasy/explain.py             Prompt, API client, validation and export
  medeasy/summary.py             Summary sentence and overflow formatting
  medeasy/evidence.py            Exact source passages and model citation IDs
  scripts/list_models.py         List account model IDs
  examples/sample_letter.txt     Fictional test document
  tests/test_core.py             Core automated tests
  tests/test_app.py              Streamlit smoke tests
  tests/test_ocr.py              Photo/OCR tests, including a real engine check
  tests/test_pdf.py              PDF parser, logo, scan and mixed-page regressions
  tests/test_network.py          Connection diagnostics, verified TLS and catalog checks
  tests/test_summary.py          Abbreviations, overflow preservation and validation
  tests/test_evidence.py         Source IDs, wrapped text and numeric safeguards
  VALIDATION.md                  Checks run and remaining checks
```

## Troubleshooting

- **Module not found:** select `.venv` in VS Code and run installation using the
  same `python` used to start Streamlit.
- **401 / key rejected:** check the account token in `.env` or Cloud Secrets.
- **403 / 404:** choose an available model from `scripts/list_models.py` or the
  TrustedTokens dashboard.
- **400 / request rejected:** the selected model may not support the JSON schema,
  sampling parameters, requested output length or document context size. Choose
  a compatible model. The app does not silently downgrade to unchecked text.
- **429:** check usage limits and retry later.
- **PDF processing diagnostic:** the error now includes a stage and exception
  type, without document text. Share that code along with the output of
  `python --version` if a file still fails. The native text path does not require
  Tesseract or PDFium for ordinary text PDFs.
- **Evidence/number mismatch:** no explanation is displayed if the model cites an
  unknown passage ID or uses a number absent from its cited passages. Check source
  text and retry, or consult your care team. Validation is not bypassed. Version
  1.6 removes the older requirement for the model to copy source quotes verbatim.
- **Camera unavailable:** allow camera permission, use localhost or HTTPS, or
  choose **Take a picture → Upload a photo**.
- **Photo reading unavailable:** install Tesseract separately from Python packages,
  install the selected language data, and check `TESSERACT_CMD` if needed. For Cloud,
  commit `packages.txt` and reboot the app.
- **File rejected:** paste a complete checked transcription. Password-protected,
  unsupported or damaged files may need a new PDF export. Native PDF text is
  supported without OCR; scans need Tesseract. Blank/unreadable pages are reported
  explicitly so the app does not explain a partially read letter.
- **Cloud secrets missing:** configure top-level keys as shown above and reboot
  the app. Do not put real secrets into the repository.

## Sources

Integration and deployment were based on these primary sources:

- [TrustedTokens API documentation](https://trustedtokens.eu/docs/)
- [TrustedTokens privacy policy](https://trustedtokens.eu/privacy-policy/)
- [Streamlit Cloud secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Streamlit configuration](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
- [Reguly design reference](https://www.reguly.de/)
- [Streamlit camera input](https://docs.streamlit.io/1.50.0/develop/api-reference/widgets/st.camera_input)
- [Tesseract installation](https://tesseract-ocr.github.io/tessdoc/Installation.html)
- [PDFium Python API](https://pypdfium2.readthedocs.io/en/stable/python_api.html)
- [Tesseract command-line usage](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html)
- [Streamlit Cloud dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
