"""Run from the project root: python scripts/list_models.py"""
from pathlib import Path
import json
import sys
import urllib.request
import urllib.error
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from medeasy.config import settings
from medeasy.explain import API_BASE
from medeasy.network import open_request, connection_message, TransportConfigError


def main():
    key, _ = settings()
    if not key or key.startswith("your_"):
        sys.exit("Set OPENAI_API_KEY in .env first.")
    request = urllib.request.Request(f"{API_BASE}/models", headers={"Authorization": f"Bearer {key}"})
    try:
        with open_request(request, timeout=30) as response:
            models = json.load(response)["data"]
        for model in models:
            print(model["id"])
    except urllib.error.HTTPError as exc:
        sys.exit(f"Could not list models (HTTP {exc.code}). Check your account and key.")
    except TransportConfigError as exc:
        sys.exit(str(exc))
    except (urllib.error.URLError, OSError) as exc:
        sys.exit(connection_message(exc))
    except (ValueError, KeyError, TypeError):
        sys.exit("Could not read the model catalog. Check your connection or provider dashboard.")


if __name__ == "__main__":
    main()
