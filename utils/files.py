import io
import base64
from typing import List, Dict
from pypdf import PdfReader
from langchain_core.documents import Document

from config.files import ALLOWED_FILE_TYPES
from config.models import IMAGE_CAPTIONING_MODEL

from services.image_captioning import ImageCaptioningService

image_captioning = ImageCaptioningService(
    model_name=IMAGE_CAPTIONING_MODEL["MODEL_NAME"],
    task=IMAGE_CAPTIONING_MODEL["TASK"],
    processor_name=IMAGE_CAPTIONING_MODEL["PROCESSOR"]
)

def _normalize_file_input(file_obj):
    """
    Accepts:
      - {"filename": str, "content": bytes|str (raw or base64)}
    Returns (filename, bytes)
    """
    if isinstance(file_obj, dict):
        filename = file_obj.get("filename") or file_obj.get("name")
        content = file_obj.get("content")
        if isinstance(content, str):
            try:
                content = base64.b64decode(content)
            except Exception:
                content = content.encode("utf-8")
        return filename, content
    return None, None

def process_pdf(filename: str, data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return f"Name of the file: {filename}\n" + "\n".join(pages).strip()
    except Exception:
        return ""

def process_txt(filename: str, data: bytes) -> str:
    try:
        decoded_data = data.decode("utf-8", errors="ignore")
        return f"Name of the file: {filename}\n" + decoded_data
    except Exception:
        return ""

def process_md(filename: str, data: bytes) -> str:
    return process_txt(filename, data)

def process_image(filename: str, data: bytes) -> str:
    try:
        caption = image_captioning.generate_caption(data)
        return f"Based on the given data generate a description of the image, it should be descriptive, the given data is just for reference: Name of the file: {filename}\nImage Caption: {caption}"
    except Exception:
        return ""

def process_files(files: List[Dict]) -> List[Document]:
    docs: List[Document] = []
    for f in files:
        filename, content = _normalize_file_input(f)
        if not filename or content is None:
            continue
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_FILE_TYPES:
            continue
        text = ""
        if ext == "pdf":
            text = process_pdf(filename, content)
        elif ext == "txt":
            text = process_txt(filename, content)
        elif ext == "md":
            text = process_md(filename, content)
        elif ext == "png" or ext == "jpg" or ext == "jpeg":
            text = process_image(filename, content)
        if not text.strip():
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "extension": ext,
                    "length": len(text)
                }
            )
        )
    return docs