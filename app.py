"""Run with: python -m streamlit run app.py"""
from pathlib import Path
import hashlib
import html
import streamlit as st
from medeasy.config import settings
from medeasy.connection import check_connection
from medeasy.documents import extract_document
from medeasy.ocr import read_photo, append_page
from medeasy.explain import ExplanationError, exact_number_lines, explain, render_text, validate_source

ROOT = Path(__file__).parent
st.set_page_config(page_title="MedEasy AI | Understand your letter", page_icon="✚", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets/style.css').read_text()}</style>", unsafe_allow_html=True)


def clear_all():
    epoch = st.session_state.get("epoch", 0) + 1
    for key in list(st.session_state):
        del st.session_state[key]
    st.session_state.epoch = epoch


def show_claim(text):
    # All document/model strings are escaped before HTML insertion.
    st.markdown(f'<div class="claim">{html.escape(text)}</div>', unsafe_allow_html=True)


st.session_state.setdefault("epoch", 0)
epoch = st.session_state.epoch
st.markdown('<div class="brand"><span class="brand-icon">+</span> MedEasy AI <span>YOUR HEALTH. IN PLAIN ENGLISH.</span></div>', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">LESS CONFUSION. A CLEARER NEXT STEP.</div>', unsafe_allow_html=True)
st.title("Understand your letter.\nKnow what to do next.")
st.markdown('<p class="hero-copy">Turn a medical letter into simple English. See what it says, what you need to do, and the details to keep.</p><div class="steps"><span class="step">01 &nbsp; Add your letter</span><span class="step">02 &nbsp; Check the text</span><span class="step">03 &nbsp; Read your next steps</span></div>', unsafe_allow_html=True)

try:
    cloud_secrets = dict(st.secrets)
except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
    cloud_secrets = {}
api_key, model = settings(cloud_secrets)

left, right = st.columns([2.2, 1], gap="large")
with right:
    st.markdown('<div class="side-card"><h3>A little clarity.<br>A lot less worry.</h3><p><b>SUMMARY</b><br>What your letter is about.</p><p><b>ACTION REQUIRED</b><br>What to do, and when.</p><p><b>IMPORTANT DETAILS</b><br>Dates, numbers and things to keep.</p></div>', unsafe_allow_html=True)
    st.caption("AI can make mistakes. Check the explanation against your letter. Ask your care team if anything is unclear. Do not change medicines based only on this app.")
    with st.expander("What happens to my information?"):
        st.write("Your file or photo is read on the app server. Photo text is extracted there with OCR. Only the text you review is sent to TrustedTokens when you click Explain my letter. You can remove names and addresses first.")
        st.write("The app does not intentionally save letters or explanations to files, a database, or a shared cache. They are held in your session. Clear this letter removes the app's session copy; it does not erase provider records, browser downloads, or infrastructure records. The hosting service and API provider may process or retain data under their policies.")
        st.link_button("TrustedTokens privacy policy", "https://trustedtokens.eu/privacy-policy/")
    if not api_key or api_key.startswith("your_"):
        st.info("Setup needed: add your API key to .env before explaining a letter. You can still try uploading the fictional example.")
    if st.button("Check API connection", use_container_width=True):
        try:
            with st.spinner("Checking API access without sending your letter…"):
                check = check_connection(api_key, model)
            st.success("API model catalog reached and the key was accepted. No letter text was sent. This does not test a model response.")
            if not check.model_listed:
                st.warning("The configured model was not listed in the catalog. Check TRUSTEDTOKENS_MODEL before explaining the letter.")
        except ExplanationError as exc:
            st.error(str(exc))
    st.caption("The connection check requests the model catalog. It does not submit your letter or generate an explanation.")
    st.button("Clear this letter", on_click=clear_all, use_container_width=True)

with left:
    with st.container(border=True):
        st.subheader("Add your letter")
        mode = st.radio("Choose how to add your letter", ["Paste text", "Upload a file", "Take a picture", "Try an example"], horizontal=True, key=f"mode_{epoch}")
        document_error = None
        pending_photo = False
        photo_context = ""
        if mode == "Upload a file":
            upload = st.file_uploader("Choose a PDF, Word or text file", type=["pdf", "docx", "txt"], key=f"upload_{epoch}")
            st.caption("Up to 10 MB. PDFs: up to 20 pages. Scanned pages use OCR; text PDFs with logos are supported.")
            pdf_language = "English"
            pdf_force_ocr = False
            if upload is not None and upload.name.lower().endswith(".pdf"):
                pdf_language = st.selectbox("PDF language (used if OCR is needed)", ["English", "German", "English and German"], key=f"pdf_language_{epoch}")
                pdf_force_ocr = st.checkbox("Read every PDF page as an image (for missing or incorrect text)", key=f"pdf_force_ocr_{epoch}")
                st.caption("Check all pages against the original, including any text inside images. Use the image-reading option if native text is incomplete. OCR needs Tesseract installed.")
            retry_upload = st.button("Read file again", disabled=upload is None, key=f"retry_upload_{epoch}")
            if upload is not None:
                data = upload.getvalue()
                upload_id = hashlib.sha256(data + upload.name.lower().encode() + f"{pdf_language}:{pdf_force_ocr}".encode()).hexdigest()
                if st.session_state.get("upload_id") != upload_id or retry_upload:
                    st.session_state.pop("result", None)
                    try:
                        with st.spinner("Reading all document pages. Scanned pages may take longer…"):
                            st.session_state[f"review_{epoch}"] = extract_document(data, upload.name, pdf_language=pdf_language, pdf_force_ocr=pdf_force_ocr)
                        st.session_state.upload_text = st.session_state[f"review_{epoch}"]
                        st.session_state.upload_error = None
                    except ExplanationError as exc:
                        st.session_state[f"review_{epoch}"] = ""
                        st.session_state.upload_text = ""
                        st.session_state.upload_error = str(exc)
                    st.session_state.upload_id = upload_id
                document_error = st.session_state.get("upload_error")
                if document_error:
                    st.error(document_error)
                st.session_state.setdefault(f"review_{epoch}", st.session_state.get("upload_text", ""))
                source = st.text_area("Check the extracted text. Correct any mistakes before continuing.", height=320, key=f"review_{epoch}")
                st.session_state.upload_text = source
            else:
                source = ""
        elif mode == "Take a picture":
            st.write("Photograph one complete page at a time. Keep the page upright, in focus and well lit. Add every page in order before asking for an explanation.")
            photo_method = st.radio("Add a photo", ["Use camera", "Upload a photo"], horizontal=True, key=f"photo_method_{epoch}")
            if photo_method == "Use camera":
                photo = st.camera_input("Take a picture of your document", key=f"camera_{epoch}")
                st.caption("Allow camera access in your browser. If the camera is unavailable or the text looks small, choose Upload a photo and use a clear photo from your phone.")
            else:
                photo = st.file_uploader("Choose a document photo (JPEG or PNG)", type=["jpg", "jpeg", "png"], key=f"photo_upload_{epoch}")
            language = st.selectbox("Language in the document", ["English", "German", "English and German"], key=f"ocr_language_{epoch}")
            rotation = st.selectbox("Rotate photo before reading", [0, 90, 180, 270], format_func=lambda degrees: "Keep as shown" if degrees == 0 else f"{degrees}° anticlockwise", key=f"photo_rotation_{epoch}")
            st.session_state.setdefault("photo_pages", [])
            # Keep a non-widget backup: Streamlit removes hidden widget keys.
            st.session_state.setdefault(f"photo_review_{epoch}", st.session_state.get("photo_text", ""))
            photo_data = photo.getvalue() if photo is not None else None
            photo_id = hashlib.sha256(photo_data).hexdigest() if photo_data is not None else ""
            photo_context = f"{photo_method}:{photo_id}:{language}:{rotation}"
            already_added = photo_id in st.session_state.photo_pages
            pending_photo = bool(photo_id) and not already_added
            # A new photo must never leave a previous result visible during OCR.
            if st.session_state.get("photo_context") != photo_context:
                st.session_state.pop("result", None)
                st.session_state.photo_context = photo_context
                st.session_state.photo_error = None
            if already_added:
                st.caption("This photo is already added. Retake the picture or choose another photo to add the next page.")
            if st.button("Read and add this page", disabled=photo is None or already_added or len(st.session_state.photo_pages) >= 20, key=f"read_photo_{epoch}"):
                st.session_state.pop("result", None)
                try:
                    with st.spinner("Reading the photo…"):
                        page_text = read_photo(photo_data, language, rotation)
                    combined = append_page(st.session_state.get(f"photo_review_{epoch}", ""), page_text)
                    st.session_state[f"photo_review_{epoch}"] = combined
                    st.session_state.photo_pages = st.session_state.photo_pages + [photo_id]
                    st.session_state.photo_error = None
                    pending_photo = False
                except ExplanationError as exc:
                    st.session_state.photo_error = str(exc)
            document_error = st.session_state.get("photo_error")
            if document_error:
                st.error(document_error)
            st.caption(f"Pages added: {len(st.session_state.photo_pages)} / 20. Photo reading runs on this app server. Only the checked text is sent to TrustedTokens.")
            if pending_photo:
                st.info("Read and add the current photo before explaining the letter. To leave it out, remove the current photo.")
            st.warning("Photo reading can miss words or misread numbers. Check every page against the photos, especially medicine names, doses, dates and amounts. Type any missing text below.")
            source = st.text_area("Check and correct the text from all pages", height=340, key=f"photo_review_{epoch}")
            st.session_state.photo_text = source
        elif mode == "Try an example":
            st.caption("Fictional example. Explaining it makes a real API request and may use API credits.")
            source = st.text_area("Example letter — you can edit it", value=(ROOT / "examples/sample_letter.txt").read_text(), height=320, key=f"example_{epoch}")
        else:
            source = st.text_area("Paste the complete letter here", placeholder="Paste a diagnosis, discharge letter or care plan…", height=300, key=f"paste_{epoch}")
        source_id = hashlib.sha256((mode + "\0" + source + "\0" + photo_context).encode()).hexdigest()
        if st.session_state.get("source_id") != source_id:
            st.session_state.pop("result", None)
            st.session_state.source_id = source_id
        st.caption(f"{len(source):,} / 40,000 characters. Check names, dates, amounts, medicines and doses against the original.")
        consent = st.checkbox("I checked this text. I agree to send it to TrustedTokens to get an explanation.", key=f"consent_{epoch}_{source_id}")
        if st.button("Explain my letter →", type="primary", use_container_width=True,
                     disabled=not source.strip() or not consent or bool(document_error) or pending_photo or len(source.strip()) > 40_000):
            st.session_state.pop("result", None)
            try:
                source = validate_source(source)
                with st.spinner("Reading your letter and checking the explanation…"):
                    result = explain(source, api_key, model)
                st.session_state.result = (result, source)
            except ExplanationError as exc:
                st.error(str(exc))
            except Exception:
                st.error("The explanation could not be completed. Please try again. No partial explanation was shown.")

if "result" in st.session_state:
    result, result_source = st.session_state.result
    st.divider()
    for heading, claims in (("1. SUMMARY", (result.summary,)), ("2. ACTION REQUIRED", result.actions), ("3. IMPORTANT DETAILS", result.details)):
        with st.container(border=True):
            st.markdown(f'<div class="result-label">{heading}</div>', unsafe_allow_html=True)
            for claim in claims:
                show_claim(claim.text)
            if heading == "3. IMPORTANT DETAILS":
                lines = exact_number_lines(result_source)
                if lines:
                    st.caption("Exact text with numbers from the letter. Read these lines in their original context.")
                    for line in lines:
                        st.markdown(f'<div class="source-line">{html.escape(line)}</div>', unsafe_allow_html=True)
                with st.expander("Check the source quotes"):
                    for claim in (result.summary,) + result.actions + result.details:
                        st.text(claim.text)
                        for quote in claim.evidence:
                            st.text(f'“{quote}”')
    st.download_button("Download explanation (.txt)", render_text(result, result_source), file_name="medeasy_explanation.txt", mime="text/plain", use_container_width=False)

st.markdown('<div class="footer">MedEasy AI v1.6 · Simple words. Clear next steps. &nbsp; This app explains the supplied text. It does not verify the letter or replace your care team.</div>', unsafe_allow_html=True)
