"""Check credentials/network with GET /models, never with patient data."""
from dataclasses import dataclass
import json
import urllib.request
import urllib.error
from .explain import API_BASE, ExplanationError
from .network import open_request, connection_message, TransportConfigError


@dataclass(frozen=True)
class ConnectionCheck:
    models_count: int
    model_listed: bool


def check_connection(api_key: str, model: str) -> ConnectionCheck:
    if not api_key or api_key.startswith("your_"):
        raise ExplanationError("Add your OpenAI API key to .env or Streamlit Secrets first.")
    request = urllib.request.Request(f"{API_BASE}/models", headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"}, method="GET")
    try:
        with open_request(request, timeout=20) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ExplanationError("The model catalog response was too large. Diagnostic: API-CATALOG-SIZE.")
        body = json.loads(data)
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise ExplanationError("The connection returned an unexpected model catalog. Diagnostic: API-CATALOG-FORMAT.")
        models = {item["id"] for item in body["data"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
        return ConnectionCheck(len(models), model in models)
    except ExplanationError:
        raise
    except urllib.error.HTTPError as exc:
        messages = {
            401: "The API key was not accepted. Update .env or Streamlit Secrets and restart. Diagnostic: API-HTTP-401.",
            403: "Access was denied by the API or network gateway. Check account permissions and network policy. Diagnostic: API-HTTP-403.",
            407: "Your proxy requires authentication. Check proxy settings. Diagnostic: CONNECTION-PROXY-AUTH.",
            429: "The provider reports a request limit. Try later or check account limits. Diagnostic: API-HTTP-429.",
        }
        raise ExplanationError(messages.get(exc.code, f"The connection check received HTTP {exc.code}. Check the provider and network gateway. Diagnostic: API-HTTP-{exc.code}.")) from None
    except TransportConfigError as exc:
        raise ExplanationError(str(exc)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ExplanationError(connection_message(exc)) from None
    except (ValueError, TypeError, KeyError):
        raise ExplanationError("The service returned an unreadable model catalog. Diagnostic: API-CATALOG-FORMAT.") from None
