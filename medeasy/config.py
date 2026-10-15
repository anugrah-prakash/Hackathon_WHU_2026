"""Secrets supplied by Streamlit Cloud override environment variables and .env."""
import os
from pathlib import Path
from collections.abc import Mapping
from dotenv import load_dotenv


def settings(secrets: Mapping | None = None) -> tuple[str, str]:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    secrets = secrets or {}
    key = str(secrets.get("TRUSTEDTOKENS_API_KEY") or os.getenv("TRUSTEDTOKENS_API_KEY", "")).strip()
    model = str(secrets.get("TRUSTEDTOKENS_MODEL") or os.getenv("TRUSTEDTOKENS_MODEL") or "zai-org/GLM-5.3").strip()
    return key, model
