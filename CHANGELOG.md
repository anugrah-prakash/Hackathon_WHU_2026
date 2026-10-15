# v2.0 — OpenAI conversion

Based on the user-supplied final ZIP. Changed authentication settings, fixed API
endpoint, model default, connection check, consent/privacy wording, scripts and
network configuration to OpenAI. Uses max_completion_tokens and store=false.
Includes local .env placeholders and Streamlit Secrets template. Archive files
are at root for Cloud deployment. Preserves existing document/OCR and validation
behavior. See VALIDATION.md for inherited test failures.
