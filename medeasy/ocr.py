"""Server-side photo OCR through Tesseract stdin/stdout; no image temp files."""
from __future__ import annotations

from io import BytesIO
import os
import shutil
import subprocess
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError
from .explain import ExplanationError, validate_source
from .documents import MAX_BYTES

MAX_PIXELS = 24_000_000
LANGUAGES = {"English": "eng", "German": "deu", "English and German": "eng+deu"}


def prepare_photo(data: bytes, rotation: int = 0) -> bytes:
    """Validate, orient and normalize a single JPEG/PNG image in memory."""
    if not data or len(data) > MAX_BYTES:
        raise ExplanationError("Choose a non-empty photo of 10 MB or less.")
    if rotation not in (0, 90, 180, 270):
        raise ExplanationError("Choose a supported photo rotation.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as original:
                if original.format not in ("JPEG", "PNG"):
                    raise ExplanationError("Use a JPEG or PNG photo. Convert HEIC photos to JPEG first.")
                if original.width * original.height > MAX_PIXELS:
                    raise ExplanationError("This photo is too large. Use a photo of no more than 24 megapixels.")
                if getattr(original, "n_frames", 1) != 1:
                    raise ExplanationError("Use a single still photo rather than an animated image.")
                original.load()
                image = ImageOps.exif_transpose(original).convert("RGBA")
                # Preserve black text on transparent PNGs by compositing on white.
                background = Image.new("RGBA", image.size, "white")
                background.alpha_composite(image)
                image = ImageOps.grayscale(background.convert("RGB"))
                if rotation:
                    image = image.rotate(rotation, expand=True, fillcolor=255)
                image = ImageOps.autocontrast(image)
                output = BytesIO()
                image.save(output, format="PNG")
                return output.getvalue()
    except ExplanationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ExplanationError("This photo could not be read safely. Retake it or choose another JPEG or PNG.") from None


def read_photo(data: bytes, language: str = "English", rotation: int = 0) -> str:
    if language not in LANGUAGES:
        raise ExplanationError("Choose English, German, or English and German for photo reading.")
    image_bytes = prepare_photo(data, rotation)
    executable = os.getenv("TESSERACT_CMD", "").strip() or shutil.which("tesseract")
    if not executable:
        raise ExplanationError("Photo reading needs Tesseract OCR installed on the app server. Follow the Photo setup instructions in README.md, or paste your letter's text.")
    try:
        completed = subprocess.run(
            [executable, "stdin", "stdout", "-l", LANGUAGES[language], "--psm", "3"],
            input=image_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=45, check=False,
            env={**os.environ, "OMP_THREAD_LIMIT": "2"},
        )
    except subprocess.TimeoutExpired:
        raise ExplanationError("Photo reading took too long. Retake a clear, close photo of one page and try again.") from None
    except OSError:
        raise ExplanationError("Tesseract could not start. Check its installation and TESSERACT_CMD in .env.") from None
    if completed.returncode or b"Failed loading language" in completed.stderr:
        raise ExplanationError("This photo could not be read. Check that the selected Tesseract language pack is installed, then try a clear photo.")
    try:
        text = completed.stdout.decode("utf-8").strip()
    except UnicodeError:
        raise ExplanationError("Photo reading returned unreadable text. Retake the photo or paste the letter's text.") from None
    if not text:
        raise ExplanationError("No readable text was found. Keep the whole page upright, well lit and in focus, then take another photo.")
    return validate_source(text)


def append_page(existing: str, page: str) -> str:
    """Combine complete OCR pages without numbering or truncating source text."""
    return validate_source("\n\n".join(part.strip() for part in (existing, page) if part.strip()))
