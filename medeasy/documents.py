"""Extract documents locally without silent truncation or saved uploads."""
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from .explain import ExplanationError, validate_source

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 20


def extract_document(data: bytes, filename: str, *, pdf_language: str = "English", pdf_force_ocr: bool = False) -> str:
    if not data or len(data) > MAX_BYTES:
        raise ExplanationError("Choose a non-empty file of 10 MB or less.")
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".txt":
            text = data.decode("utf-8-sig")
        elif suffix == ".pdf":
            from .pdf_reader import extract_pdf
            text = extract_pdf(data, language=pdf_language, force_ocr=pdf_force_ocr)
        elif suffix == ".docx":
            from docx import Document
            with ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 500 or sum(i.file_size for i in entries) > 20_000_000:
                    raise ExplanationError("This Word file is too large to unpack safely. Paste the text instead.")
                names = archive.namelist()
                if any(n.startswith("word/media/") for n in names):
                    raise ExplanationError("This Word file contains images that may hold medical information. Paste a complete, checked transcription instead.")
                if any(n.startswith("word/") and any(tag in n for tag in ("footnotes", "endnotes", "comments")) for n in names):
                    raise ExplanationError("This Word file contains notes or comments. Paste a complete, checked transcription so these details are included.")
            doc = Document(BytesIO(data))
            lines = []
            # Preserve body paragraph/table order, including nested tables.
            def read_blocks(parent):
                for block in parent.iter_inner_content():
                    if hasattr(block, "text"):
                        if block.text.strip():
                            lines.append(block.text)
                    else:
                        for row in block.rows:
                            for cell in row.cells:
                                read_blocks(cell)
            for section in doc.sections:
                for area in (section.header, section.first_page_header, section.even_page_header):
                    read_blocks(area)
            read_blocks(doc)
            for section in doc.sections:
                for area in (section.footer, section.first_page_footer, section.even_page_footer):
                    read_blocks(area)
            # Text boxes and tracked changes are not safely interpreted by python-docx.
            xml = doc.element.xml
            if any(tag in xml for tag in ("txbxContent", "<w:ins ", "<w:del ")):
                raise ExplanationError("This Word file contains text boxes or tracked changes. Paste a complete, checked transcription instead.")
            text = "\n".join(lines)
        else:
            raise ExplanationError("Use a PDF, DOCX, or UTF-8 TXT file.")
        return validate_source(text)
    except ExplanationError:
        raise
    except (UnicodeError, BadZipFile):
        raise ExplanationError("This file could not be read. Use a valid DOCX or UTF-8 TXT file.") from None
    except Exception:
        # Do not expose parser errors containing patient text or filenames.
        raise ExplanationError("This file could not be read safely. Paste the complete text instead.") from None
