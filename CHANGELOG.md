# Number encodings and effective retries — v1.6.1 — 15 October 2026

- Accept numeric claims that copy a letter's number in an equivalent encoding:
  thousand separators (1,500 / 1.500 / 1500), an attached or absent currency
  symbol, dash variants and full-width digits. Decimal commas such as "1,5"
  are never merged with plain digits, and genuinely invented numbers are still
  rejected.
- Reminder: a repeated **Explain my letter →** click now sends an app-generated
  correction instruction with the letter (never patient data), because a failed
  validation was reproducible at temperature 0. One paid request per click;
  still no automatic retries.
- Strengthened the prompt to require copying numbers character for character.
- Added six regression tests for encoding equivalence, decimal commas and the
  correction-note plumbing.

# Source evidence fix — v1.6 — 15 October 2026

- Replaced model-copied source quotes with server-assigned passage IDs.
- The per-request response schema permits only IDs from the current letter.
- Retrieve original passage text locally for source evidence, preserving its line
  breaks, Unicode spaces, dates, amounts and references without model recopying.
- Preserve source order and avoid splitting words/numeric identifiers into pieces.
- Continue to reject unknown IDs, missing evidence and unsupported numeric strings.
- Added nine regressions and updated the mocked API test for the indexed protocol.
- No additional model call or automatic paid retry is introduced.

# Summary validation fix — v1.5 — 15 October 2026

- Removed the failure that rejected an otherwise validated answer merely because
  the summary contained several sentences.
- Keep the first summary sentence and move remaining sentences, unchanged with
  their source quotes, into IMPORTANT DETAILS. No additional API call is made.
- Recognise common titles, initials, decimals and dotted dates before splitting.
- Tighten the summary prompt to request a short sentence with details in the other
  sections. Continue validating the entire response before formatting.
- Added six regression tests and updated the earlier multi-sentence test.

# API connection diagnostics — v1.4 — 15 October 2026

- Added a Check API connection button using GET /models, without sending the letter.
- Replaced the generic transport error with safe DNS, TLS, proxy, timeout, refused,
  interrupted and unknown-connection diagnostic messages.
- Added a bounded, configurable response timeout (default 180 seconds) and optional
  administrator-provided CA file that augments system trust.
- Kept TLS verification and authenticated-redirect protection enabled; no automatic
  paid retries introduced.
- Shared the verified HTTPS transport with the model-listing script.
- Added 15 network/catalog tests and connection troubleshooting instructions.
- Underlying user connectivity issue remains unconfirmed without a diagnostic result.

# Attached PDF follow-up — 15 October 2026

- Verified all four pages of the supplied PDF using native extraction, with no OCR
  or external API call. The original screenshot error did not reproduce locally.
- Changed PDF reading to pure-Python pypdf first; PDFium is loaded only for fallback
  extraction or scanned-page rendering.
- Replaced PDFium context-manager usage with explicit cleanup for compatibility.
- Added safe stage/type diagnostic codes for unexpected fallback failures.
- Added five native-first regression tests. No patient documents or extracted
  patient text are included in this project archive.

# PDF upload fix — 15 October 2026

- Replaced strict PDF parsing and image inspection with tolerant PDFium text reading.
- Text PDFs with logos no longer require image decoding or OCR.
- Added automatic OCR for pages without native text, and optional OCR for every page.
- Added PDF OCR language selection and a retry button for the same upload.
- Added page-specific failure messages; no partial PDF is used after a failed page.
- Preserved edited upload text across switching input modes.
- Added pypdfium2 dependency and nine regression tests, including real scanned-PDF OCR.
- Existing camera, .env setup, three-section output and Streamlit deployment files retained.

# Camera update — 15 October 2026

- Added **Take a picture**, with a browser camera and JPEG/PNG upload fallback.
- Added on-server OCR through Tesseract, with English and German language options.
- Added rotation control and support for adding up to 20 photographed pages in order.
- Required review of the combined OCR text before using the existing explanation flow.
- Added image size/type limits, no-text and timeout handling, duplicate-page prevention,
  and clearing of previous results when the photo changes.
- Added Pillow dependency, Streamlit Cloud `packages.txt`, optional Windows Tesseract
  path setting, photo setup instructions and automated OCR tests.
- The existing three-section explanation format and TrustedTokens integration remain.
