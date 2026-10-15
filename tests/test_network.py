from io import BytesIO
import json
import socket
import ssl
import unittest
import urllib.error
from unittest.mock import patch, Mock
from medeasy.connection import check_connection
from medeasy.explain import ExplanationError
from medeasy.network import (connection_message, timeout_seconds, TransportConfigError,
                              open_request, NoRedirect)


class NetworkTests(unittest.TestCase):
    def test_dns_failure_is_distinct(self):
        message = connection_message(urllib.error.URLError(socket.gaierror(-2, "private proxy name")))
        self.assertIn("CONNECTION-DNS", message)
        self.assertNotIn("private", message)

    def test_certificate_failure_is_distinct(self):
        message = connection_message(urllib.error.URLError(ssl.SSLCertVerificationError(1, "private details")))
        self.assertIn("CONNECTION-TLS-CERTIFICATE", message)
        self.assertNotIn("private", message)

    def test_timeout_warns_about_unconfirmed_processing(self):
        message = connection_message(TimeoutError())
        self.assertIn("CONNECTION-TIMEOUT", message)
        self.assertIn("charging", message)

    def test_refused_reset_proxy_and_unknown_do_not_echo_raw_error(self):
        for error, code in [(ConnectionRefusedError(), "REFUSED"), (ConnectionResetError(), "RESET"),
                            (urllib.error.URLError("proxy tunnel failed with private credentials"), "PROXY"),
                            (OSError("private details"), "NETWORK")]:
            with self.subTest(code=code):
                message = connection_message(error)
                self.assertIn(f"CONNECTION-{code}", message)
                self.assertNotIn("private", message)

    def test_timeout_configuration_is_bounded(self):
        for value in ("abc", "0", "601", "-1"):
            with patch.dict("os.environ", {"TRUSTEDTOKENS_TIMEOUT_SECONDS": value}):
                with self.assertRaises(TransportConfigError):
                    timeout_seconds()
        with patch.dict("os.environ", {"TRUSTEDTOKENS_TIMEOUT_SECONDS": "300"}):
            self.assertEqual(timeout_seconds(), 300)

    def test_tls_stays_verified(self):
        import urllib.request
        context = ssl.create_default_context()
        with patch("medeasy.network.ssl.create_default_context", return_value=context), patch("urllib.request.build_opener") as build:
            open_request(urllib.request.Request("https://api.trustedtokens.eu/v1/models"), timeout=20)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(any(isinstance(handler, NoRedirect) for handler in build.call_args.args))

    def test_custom_ca_adds_trust_without_replacing_system_context(self):
        import urllib.request
        context = Mock()
        with patch.dict("os.environ", {"TRUSTEDTOKENS_CA_BUNDLE": "organisation.pem"}), patch("medeasy.network.ssl.create_default_context", return_value=context), patch("urllib.request.build_opener"):
            open_request(urllib.request.Request("https://api.trustedtokens.eu/v1/models"), timeout=20)
        context.load_verify_locations.assert_called_once_with(cafile="organisation.pem")

    def test_ca_configuration_error_is_safe(self):
        import urllib.request
        with patch("medeasy.network.ssl.create_default_context", side_effect=OSError("private filename")):
            with self.assertRaisesRegex(TransportConfigError, "CONNECTION-CA-CONFIG") as caught:
                open_request(urllib.request.Request("https://api.trustedtokens.eu/v1/models"), timeout=20)
        self.assertNotIn("private", str(caught.exception))

    def test_redirects_never_forward_credentials(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))


class ConnectionCheckTests(unittest.TestCase):
    def test_catalog_check_sends_no_document_or_completion(self):
        payload = {"data": [{"id": "test/model"}, {"id": "other/model"}]}
        with patch("medeasy.connection.open_request", return_value=BytesIO(json.dumps(payload).encode())) as call:
            result = check_connection("secret-key", "test/model")
        request = call.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "https://api.trustedtokens.eu/v1/models")
        self.assertIsNone(request.data)
        self.assertEqual(result.models_count, 2)
        self.assertTrue(result.model_listed)

    def test_unknown_model_does_not_claim_it_is_available(self):
        with patch("medeasy.connection.open_request", return_value=BytesIO(b'{"data":[]}')):
            self.assertFalse(check_connection("key", "unlisted").model_listed)

    def test_missing_key_does_not_make_request(self):
        with patch("medeasy.connection.open_request") as call:
            with self.assertRaises(ExplanationError):
                check_connection("", "model")
        call.assert_not_called()

    def test_http_error_masks_body_and_credentials(self):
        error = urllib.error.HTTPError("https://example.invalid", 407, "private proxy credentials", {}, None)
        with patch("medeasy.connection.open_request", side_effect=error):
            with self.assertRaisesRegex(ExplanationError, "PROXY-AUTH") as caught:
                check_connection("secret-key", "model")
        self.assertNotIn("private", str(caught.exception))
        self.assertNotIn("secret", str(caught.exception))

    def test_unreadable_catalog_is_safe(self):
        for body in (b"not-json", b'[]', b'{"data":{}}'):
            with self.subTest(body=body), patch("medeasy.connection.open_request", return_value=BytesIO(body)):
                with self.assertRaisesRegex(ExplanationError, "CATALOG-FORMAT"):
                    check_connection("key", "model")

    def test_dns_error_reaches_user_as_diagnostic(self):
        with patch("medeasy.connection.open_request", side_effect=urllib.error.URLError(socket.gaierror(-2, "private"))):
            with self.assertRaisesRegex(ExplanationError, "CONNECTION-DNS"):
                check_connection("key", "model")


if __name__ == "__main__":
    unittest.main()
