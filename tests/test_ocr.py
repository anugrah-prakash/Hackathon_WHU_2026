from io import BytesIO
import shutil
import subprocess
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont
from medeasy.explain import ExplanationError
from medeasy.ocr import prepare_photo, read_photo, append_page


def photo_bytes(text="Example letter"):
    image = Image.new("RGB", (1600, 700), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 38)
    except OSError:
        font = ImageFont.load_default(size=38)
    draw.multiline_text((65, 70), text, font=font, fill="black", spacing=25)
    out = BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


class PhotoTests(unittest.TestCase):
    def test_prepares_png_and_rotates(self):
        data = prepare_photo(photo_bytes(), 90)
        with Image.open(BytesIO(data)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (700, 1600))
            self.assertEqual(image.mode, "L")

    def test_invalid_input_and_rotation_rejected(self):
        for data, rotation in ((b"", 0), (b"not an image", 0), (b"x" * (10 * 1024 * 1024 + 1), 0), (photo_bytes(), 45)):
            with self.subTest(rotation=rotation), self.assertRaises(ExplanationError):
                prepare_photo(data, rotation)

    def test_non_photo_image_rejected(self):
        out = BytesIO()
        Image.new("RGB", (100, 100)).save(out, "GIF")
        with self.assertRaisesRegex(ExplanationError, "JPEG or PNG"):
            prepare_photo(out.getvalue())

    def test_large_pixel_count_rejected(self):
        with patch("medeasy.ocr.MAX_PIXELS", 100):
            with self.assertRaisesRegex(ExplanationError, "megapixels"):
                prepare_photo(photo_bytes())

    def test_missing_engine_is_actionable(self):
        with patch.dict("os.environ", {"TESSERACT_CMD": ""}), patch("medeasy.ocr.shutil.which", return_value=None):
            with self.assertRaisesRegex(ExplanationError, "Tesseract OCR installed"):
                read_photo(photo_bytes())

    def test_ocr_uses_pipes_and_language_without_shell(self):
        completed = subprocess.CompletedProcess([], 0, b"Pay GBP 15.00 by 28 October 2026.\n", b"")
        with patch.dict("os.environ", {"TESSERACT_CMD": "/test/tesseract"}), patch("medeasy.ocr.subprocess.run", return_value=completed) as run:
            text = read_photo(photo_bytes(), "English and German")
        self.assertEqual(text, "Pay GBP 15.00 by 28 October 2026.")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["/test/tesseract", "stdin", "stdout", "-l", "eng+deu", "--psm", "3"])
        self.assertEqual(kwargs["timeout"], 45)
        self.assertNotIn("shell", kwargs)
        self.assertTrue(kwargs["input"].startswith(b"\x89PNG"))

    def test_no_text_timeout_or_engine_error(self):
        data = photo_bytes()
        outcomes = [
            subprocess.CompletedProcess([], 0, b" \n", b""),
            subprocess.CompletedProcess([], 1, b"", b"private diagnostics"),
            subprocess.TimeoutExpired("tesseract", 45),
            FileNotFoundError("private filesystem path"),
        ]
        for outcome in outcomes:
            with self.subTest(outcome=type(outcome).__name__), patch.dict("os.environ", {"TESSERACT_CMD": "/test/tesseract"}):
                with patch("medeasy.ocr.subprocess.run") as run:
                    if isinstance(outcome, Exception):
                        run.side_effect = outcome
                    else:
                        run.return_value = outcome
                    with self.assertRaises(ExplanationError) as caught:
                        read_photo(data)
                    self.assertNotIn("private", str(caught.exception))

    def test_invalid_language(self):
        with self.assertRaisesRegex(ExplanationError, "English"):
            read_photo(photo_bytes(), "untrusted --parameter")

    def test_append_pages_preserves_text_and_checks_total_limit(self):
        self.assertEqual(append_page("Page one: ABC-001", "Pay GBP 15.00"), "Page one: ABC-001\n\nPay GBP 15.00")
        with self.assertRaisesRegex(ExplanationError, "too long"):
            append_page("a" * 39999, "extra page")

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract is not installed")
    def test_real_tesseract_reads_reference_date_and_amount(self):
        text = read_photo(photo_bytes("Discharge letter\nReference: MED-2026-0042\nVisit by 21 October 2026.\nPay GBP 15.00 by 28 October 2026."))
        for exact in ("MED-2026-0042", "21 October 2026", "GBP 15.00", "28 October 2026"):
            self.assertIn(exact, text)


if __name__ == "__main__":
    unittest.main()
