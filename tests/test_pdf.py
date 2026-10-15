"""PDF regressions: text with logos, scans, mixed pages and clear errors."""
from io import BytesIO
import shutil
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfWriter
from pypdf.generic import (DecodedStreamObject, DictionaryObject, NameObject, NumberObject)
from medeasy.documents import extract_document
from medeasy.explain import ExplanationError


def scan_image():
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 40)
    except OSError:
        font = ImageFont.load_default(size=40)
    draw.multiline_text((60, 80), "Discharge letter\nReference: SCAN-2026-0042\nPay GBP 15.00 by 28 October 2026.", font=font, fill="black", spacing=25)
    return image


def pdf_bytes(specs):
    writer = PdfWriter()
    for text, picture in specs:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        resources = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        operators = b""
        if text:
            operators += b"BT /F1 14 Tf 50 730 Td (" + text.encode("ascii") + b") Tj ET\n"
        if picture:
            image = scan_image()
            obj = DecodedStreamObject()
            obj.set_data(image.tobytes())
            obj.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"), NameObject("/Width"): NumberObject(image.width), NameObject("/Height"): NumberObject(image.height), NameObject("/ColorSpace"): NameObject("/DeviceRGB"), NameObject("/BitsPerComponent"): NumberObject(8)})
            resources[NameObject("/XObject")] = DictionaryObject({NameObject("/Im1"): writer._add_object(obj.flate_encode())})
            operators += b"q 570 0 0 321 20 300 cm /Im1 Do Q\n"
        page[NameObject("/Resources")] = resources
        stream = DecodedStreamObject()
        stream.set_data(operators)
        page[NameObject("/Contents")] = writer._add_object(stream)
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


class PDFTests(unittest.TestCase):
    def test_native_text_with_image_does_not_require_ocr(self):
        data = pdf_bytes([("Reference: NATIVE-0042", True)])
        with patch("medeasy.ocr.read_photo") as ocr:
            self.assertIn("NATIVE-0042", extract_document(data, "logo.pdf"))
            ocr.assert_not_called()

    def test_ocr_used_for_scan_and_language_forwarded(self):
        data = pdf_bytes([("", True)])
        with patch("medeasy.ocr.read_photo", return_value="Reference: SCAN-0042") as ocr:
            self.assertIn("SCAN-0042", extract_document(data, "scan.pdf", pdf_language="German"))
        self.assertEqual(ocr.call_args.args[1], "German")
        self.assertTrue(ocr.call_args.args[0].startswith(b"\x89PNG"))

    def test_force_ocr_reads_mixed_page_image_text(self):
        data = pdf_bytes([("Native header", True)])
        with patch("medeasy.ocr.read_photo", return_value="Native header\nReference: IMAGE-0042") as ocr:
            text = extract_document(data, "mixed.pdf", pdf_force_ocr=True)
        self.assertIn("IMAGE-0042", text)
        ocr.assert_called_once()

    def test_mixed_native_and_scanned_pages_in_order(self):
        data = pdf_bytes([("FIRST-PAGE-0042", False), ("", True)])
        with patch("medeasy.ocr.read_photo", return_value="SECOND-PAGE-0043"):
            text = extract_document(data, "mixed.pdf")
        self.assertLess(text.index("FIRST-PAGE-0042"), text.index("SECOND-PAGE-0043"))

    def test_later_unreadable_page_returns_no_partial_document(self):
        data = pdf_bytes([("FIRST-PAGE", False), ("", True)])
        with patch("medeasy.ocr.read_photo", side_effect=ExplanationError("Tesseract is not installed")):
            with self.assertRaisesRegex(ExplanationError, "page 2.*Tesseract.*No partial"):
                extract_document(data, "mixed.pdf")

    def test_tolerates_nonstandard_header_prefix(self):
        data = b"export prefix\n" + pdf_bytes([("Reference: TOLERANT-0042", False)])
        self.assertIn("TOLERANT-0042", extract_document(data, "export.pdf"))

    def test_damaged_file_has_specific_error(self):
        with self.assertRaisesRegex(ExplanationError, "damaged or unsupported"):
            extract_document(b"%PDF-1.7\nbroken", "broken.pdf")

    def test_page_limit(self):
        with self.assertRaisesRegex(ExplanationError, "20 pages"):
            extract_document(pdf_bytes([("Text", False)] * 21), "long.pdf")

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract is not installed")
    def test_real_scanned_pdf_ocr(self):
        text = extract_document(pdf_bytes([("", True)]), "scan.pdf")
        for exact in ("SCAN-2026-0042", "GBP 15.00", "28 October 2026"):
            self.assertIn(exact, text)


class NativeFirstTests(unittest.TestCase):
    def test_text_pdf_never_loads_fallback_reader(self):
        data = pdf_bytes([("Reference: TEXT-0042", True)])
        with patch("medeasy.pdf_reader._fallback_pages", side_effect=AssertionError("Fallback must not run")):
            text = extract_document(data, "letter.pdf")
        self.assertIn("TEXT-0042", text)

    def test_four_text_pages_all_returned_without_renderer(self):
        data = pdf_bytes([(f"Reference: PAGE-{i}", False) for i in range(1, 5)])
        with patch("medeasy.pdf_reader._fallback_pages", side_effect=AssertionError("Fallback must not run")):
            text = extract_document(data, "four-pages.pdf")
        for i in range(1, 5):
            self.assertIn(f"PAGE-{i}", text)
        self.assertEqual(text.count("Reference:"), 4)

    def test_force_ocr_always_requests_fallback(self):
        data = pdf_bytes([("Native text", False)])
        with patch("medeasy.pdf_reader._fallback_pages", return_value="Checked OCR result") as fallback:
            self.assertEqual(extract_document(data, "force.pdf", pdf_force_ocr=True), "Checked OCR result")
        self.assertTrue(fallback.call_args.args[3])

    def test_unexpected_native_failure_uses_independent_reader(self):
        data = pdf_bytes([("Reference: FALLBACK-0042", False)])
        with patch("medeasy.pdf_reader._native_pages", return_value=None):
            text = extract_document(data, "fallback.pdf")
        self.assertIn("FALLBACK-0042", text)

    def test_fallback_error_contains_safe_diagnostic(self):
        import pypdfium2
        with patch("medeasy.pdf_reader._native_pages", return_value=None), patch.object(pypdfium2, "PdfDocument", side_effect=RuntimeError("private patient text")):
            with self.assertRaises(ExplanationError) as caught:
                extract_document(pdf_bytes([("Native text", False)]), "letter.pdf")
        self.assertIn("Diagnostic: PDF-open-RuntimeError", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
