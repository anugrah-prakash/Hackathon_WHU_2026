# Validation record — v1.6 source passage evidence

Updated: 15 October 2026.

## Completed

- 79 core/photo/PDF/network/summary/evidence tests passed on Python 3.12.14.
- Four Streamlit browser smoke tests skipped because Streamlit is not installed.
- New regressions cover original text with line breaks and Unicode spaces, invalid
  IDs, model-written quotes where IDs are required, invented amounts, missing
  information, complete source coverage, long identifiers, and multiple passages.
- The mocked API test verifies source passages in the request and a per-request
  JSON schema whose evidence enum contains the current source IDs only.
- Quote retrieval is local and exact. Source text is not rewritten by the model.
  No additional API call is made for citation resolution.
- Python 3.11 grammar check and bytecode compilation passed.
- Earlier PDF/OCR/network/summary tests continue to pass. No patient documents,
  screenshots or extracted patient text are bundled with the app.

## Limitations and remaining checks

- The screenshot identifies an unmatched generated source quote, but the actual
  response was not provided. Whether that quote was reformatted, paraphrased or
  invented is unknown. Tests use fictional examples of the failure class.
- A valid source ID establishes that a passage exists, not that its meaning
  supports the generated claim. Semantic accuracy still needs source review.
- No live API call, clinical evaluation, Python 3.11.4 runtime, browser execution,
  deployment, real camera capture or German OCR was verified in this environment.

## Run after updating

Extract into a fresh folder, copy your own .env, activate your environment, then:

```bash
python -m pip install --upgrade -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

Confirm the footer says MedEasy AI v1.6. With all dependencies and Tesseract
installed, all 83 tests should run. Source IDs are internal; the patient sees
original source text inside Check the source quotes. Explain my letter still
makes one normal paid API request when clicked.
