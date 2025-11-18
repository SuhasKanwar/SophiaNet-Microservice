import sys
import io
from PIL import Image
from typing import List, Dict

import pytesseract

from utils.exception import SophiaNetException

def get_text(files: List[Dict]) -> str:
    if not files:
        return "No files provided for OCR."
    supported_ext = {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"}
    results = []
    for f in files:
        name = f.get("filename") or "unnamed"
        ext = name.split(".")[-1].lower()
        if ext not in supported_ext:
            continue
        content = f.get("content")
        if not isinstance(content, (bytes, bytearray)):
            continue
        try:
            img = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(img)
            cleaned = text.strip()
            if cleaned:
                results.append(f"File: {name}\n{cleaned}")
        except Exception as e:
            raise SophiaNetException(f"Failed to process file {name}: {str(e)}", sys)
    if not results:
        return "No extractable text found in provided images."
    return "\n\n".join(results)