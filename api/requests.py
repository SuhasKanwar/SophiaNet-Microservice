import base64
import binascii
import json
from typing import Literal

from fastapi import HTTPException, Request
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field, field_validator

from config.files import ALLOWED_FILE_TYPES


MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 10


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=100000)


class FilePayload(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content: bytes

    @field_validator("filename")
    @classmethod
    def supported_file(cls, value):
        if value.rsplit(".", 1)[-1].lower() not in ALLOWED_FILE_TYPES:
            raise ValueError("Unsupported file type.")
        return value

    @field_validator("content", mode="before")
    @classmethod
    def decode_content(cls, value, info):
        if isinstance(value, str):
            try:
                value = base64.b64decode(value, validate=True)
            except (binascii.Error, ValueError) as error:
                if info.data.get("filename", "").lower().endswith((".txt", ".md")):
                    value = value.encode("utf-8")
                else:
                    raise ValueError("JSON image and PDF content must be base64 encoded.") from error
        if not isinstance(value, bytes) or len(value) > MAX_FILE_BYTES:
            raise ValueError("Files must contain bytes and be at most 10 MB.")
        return value


class GenerateRequest(BaseModel):
    prompt: str = Field(default="", max_length=100000)
    code: str = Field(default="", max_length=100000)
    session_history: list[HistoryMessage] = Field(default_factory=list, max_length=200)
    files: list[FilePayload] = Field(default_factory=list, max_length=MAX_FILES)

    @field_validator("prompt", "code")
    @classmethod
    def strip_text(cls, value):
        return value.strip()

    @property
    def messages(self):
        return [
            (HumanMessage if message.role == "user" else AIMessage)(content=message.content)
            for message in self.session_history
        ]

    @property
    def file_payloads(self):
        return [file.model_dump() for file in self.files]

    def require_prompt(self):
        if not self.prompt:
            raise HTTPException(status_code=400, detail="Prompt is required.")


async def parse_request(request: Request) -> GenerateRequest:
    try:
        if "multipart/form-data" in request.headers.get("content-type", ""):
            async with request.form(max_files=MAX_FILES, max_fields=20) as form:
                data = {key: form.get(key, "") for key in ("prompt", "code")}
                data["session_history"] = json.loads(form.get("session_history", "[]"))
                uploads = form.getlist("files")
                data["files"] = []
                for upload in uploads:
                    if not hasattr(upload, "read"):
                        raise ValueError("files must be file uploads.")
                    content = await upload.read(MAX_FILE_BYTES + 1)
                    data["files"].append({"filename": upload.filename, "content": content})
        else:
            data = await request.json()
        return GenerateRequest.model_validate(data)
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail="Invalid prompt, history, or files payload.") from error
