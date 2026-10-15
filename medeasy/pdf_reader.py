"""Native Python PDF text first; PDFium only for fallback reading or OCR."""
from io import BytesIO
import math
from threading import RLock
from .explain import ExplanationError, validate_source

_PDF_LOCK = RLock()  # PDFium is not thread-safe, even across documents.
MAX_PAGES = 20
MAX_RENDER_PIXELS = 20_000_000


def _check_pages(count: int) -> None:
    if not count:
        raise ExplanationError("This PDF has no pages. Upload another copy.")
    if count > MAX_PAGES:
        raise ExplanationError("Choose a PDF with no more than 20 pages.")


def _native_pages(data: bytes) -> list[str] | None:
    """Read text without decoding images or loading a native rendering library."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ExplanationError("This PDF is password protected. Upload an unlocked copy.")
        _check_pages(len(reader.pages))
        pages = []
        for page in reader.pages:
            try:
                contents = page.get_contents()
                if contents is not None and len(contents.get_data()) > 10_000_000:
                    raise ExplanationError("A PDF page is too complex to read safely. Upload a normal page-size export.")
                text = page.extract_text() or ""
            except ExplanationError:
                raise
            except Exception:
                text = ""  # Ask the independent reader; never skip the page.
            pages.append(text.strip())
            if any(pages):
                validate_source("\n\n".join(pages))
        return pages
    except ExplanationError:
        raise
    except Exception:
        return None


def _close(resource) -> None:
    """Explicit cleanup supports PDFium releases without context managers."""
    if resource is not None:
        resource.close()


def _fallback_pages(data: bytes, native: list[str] | None, language: str, force_ocr: bool) -> str:
    try:
        import pypdfium2 as pdfium
    except (ImportError, OSError):
        raise ExplanationError("This PDF needs the fallback reader. Run python -m pip install --upgrade -r requirements.txt, then restart Streamlit. Diagnostic: PDF-DEPENDENCY.") from None
    stage = "open"
    try:
        with _PDF_LOCK:
            document = None
            try:
                document = pdfium.PdfDocument(data)
                count = len(document)
                _check_pages(count)
                if native is not None and len(native) != count:
                    raise ExplanationError("The PDF readers disagree about the page count. Upload a new PDF export. No partial document was used.")
                pages = []
                for index in range(count):
                    content = native[index] if native is not None else ""
                    if content and not force_ocr:
                        pages.append(content)
                        continue
                    stage = f"page-{index + 1}"
                    page = textpage = bitmap = image = None
                    try:
                        page = document[index]
                        if not force_ocr:
                            try:
                                textpage = page.get_textpage()
                                # get_text_range also supports older PDFium wrappers.
                                content = (textpage.get_text_range() or "").replace("\r\n", "\n").strip()
                            except Exception:
                                content = ""
                            finally:
                                _close(textpage)
                                textpage = None
                        if force_ocr or not content:
                            stage = f"render-{index + 1}"
                            width, height = page.get_size()
                            if not all(math.isfinite(v) and v > 0 for v in (width, height)):
                                raise ExplanationError(f"PDF page {index + 1} has an invalid size. Upload a new export.")
                            scale = min(2.5, math.sqrt(MAX_RENDER_PIXELS / (width * height)))
                            if scale < 0.5:
                                raise ExplanationError(f"PDF page {index + 1} is too large to read safely. Upload a normal page-size export.")
                            bitmap = page.render(scale=scale)
                            image = bitmap.to_pil()
                            output = BytesIO()
                            image.save(output, format="PNG")
                            from .ocr import read_photo
                            stage = f"ocr-{index + 1}"
                            try:
                                content = read_photo(output.getvalue(), language)
                            except ExplanationError as exc:
                                raise ExplanationError(f"PDF page {index + 1} needs OCR or has no readable text (it may be scanned or blank). {exc} No partial document was used.") from None
                    finally:
                        if image is not None:
                            image.close()
                        _close(bitmap)
                        _close(textpage)
                        _close(page)
                    pages.append(content.strip())
                    validate_source("\n\n".join(pages))
                return validate_source("\n\n".join(pages))
            finally:
                _close(document)
    except ExplanationError:
        raise
    except pdfium.PdfiumError as exc:
        if getattr(exc, "err_code", None) == 4:
            raise ExplanationError("This PDF is password protected. Upload an unlocked copy.") from None
        raise ExplanationError(f"This PDF is damaged or unsupported. Open it in a PDF viewer and export a new copy. No partial document was used. Diagnostic: PDF-{stage}-PdfiumError.") from None
    except Exception as exc:
        # Exception type/stage only: never display patient text, paths or raw errors.
        raise ExplanationError(f"This PDF could not be processed. Update requirements.txt and restart Streamlit, or upload a new PDF export. No partial document was used. Diagnostic: PDF-{stage}-{type(exc).__name__}.") from None


def extract_pdf(data: bytes, *, language: str = "English", force_ocr: bool = False) -> str:
    pages = _native_pages(data)
    if pages is not None and all(pages) and not force_ocr:
        return validate_source("\n\n".join(pages))
    return _fallback_pages(data, pages, language, force_ocr)
