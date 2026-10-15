"""Verified HTTPS transport and privacy-safe connection diagnostics."""
import errno
import os
import socket
import ssl
import urllib.error
import urllib.request


class TransportConfigError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        # Never forward bearer credentials to a redirected host.
        return None


def timeout_seconds() -> int:
    try:
        value = int(os.getenv("TRUSTEDTOKENS_TIMEOUT_SECONDS", "180"))
    except ValueError:
        raise TransportConfigError("TRUSTEDTOKENS_TIMEOUT_SECONDS must be a whole number from 30 to 600.") from None
    if not 30 <= value <= 600:
        raise TransportConfigError("TRUSTEDTOKENS_TIMEOUT_SECONDS must be a whole number from 30 to 600.")
    return value


def open_request(request, *, timeout: int):
    try:
        context = ssl.create_default_context()
        # Add an administrator-supplied CA to system roots; never disable TLS checks.
        ca_file = os.getenv("TRUSTEDTOKENS_CA_BUNDLE", "").strip()
        if ca_file:
            context.load_verify_locations(cafile=ca_file)
    except (OSError, ssl.SSLError):
        raise TransportConfigError("Certificate setup failed. Check TRUSTEDTOKENS_CA_BUNDLE and your Python certificate installation. Diagnostic: CONNECTION-CA-CONFIG.") from None
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
    return opener.open(request, timeout=timeout)


def connection_message(error: BaseException) -> str:
    """Classify known failures without echoing URLs, proxy credentials or raw errors."""
    reason = error.reason if isinstance(error, urllib.error.URLError) else error
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "The secure connection could not verify the server certificate. Update your Python/OS trusted certificates. If your organisation inspects HTTPS traffic, ask IT for its trusted CA file and set TRUSTEDTOKENS_CA_BUNDLE. Keep certificate verification enabled. Diagnostic: CONNECTION-TLS-CERTIFICATE."
    if isinstance(reason, ssl.SSLError):
        return "The secure connection failed. Check your system clock, HTTPS proxy and trusted certificates. Diagnostic: CONNECTION-TLS."
    if isinstance(reason, socket.gaierror):
        return "The API hostname or configured proxy could not be resolved. Check DNS, internet access and proxy settings for api.trustedtokens.eu. Diagnostic: CONNECTION-DNS."
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "The API connection or response timed out. Check connectivity with Check API connection. For slow model responses, increase TRUSTEDTOKENS_TIMEOUT_SECONDS in .env and restart. A timeout does not prove the provider stopped processing or charging for the request. Diagnostic: CONNECTION-TIMEOUT."
    if isinstance(reason, ConnectionRefusedError) or getattr(reason, "errno", None) == errno.ECONNREFUSED:
        return "The API or proxy refused the connection. Check firewall, VPN and proxy settings for outbound HTTPS access. Diagnostic: CONNECTION-REFUSED."
    if isinstance(reason, ConnectionResetError):
        return "The API connection was interrupted. Check your connection, VPN/proxy and provider status before retrying. Diagnostic: CONNECTION-RESET."
    # urllib may provide a string for proxy tunnel errors. Classify but never echo it.
    if isinstance(reason, str) and ("tunnel" in reason.lower() or "proxy" in reason.lower()):
        return "The configured proxy could not establish an HTTPS connection. Check HTTPS_PROXY/HTTP_PROXY and ask your network administrator about access to api.trustedtokens.eu. Diagnostic: CONNECTION-PROXY."
    return "The AI service could not be reached. Check API connection to narrow down the problem. Check outbound HTTPS, VPN and proxy settings for api.trustedtokens.eu. Diagnostic: CONNECTION-NETWORK."
