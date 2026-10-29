import re

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from api.requests import GenerateRequest, parse_request
from api.responses import text_response
from services.assistant import get_assistant
from utils.ocr import get_text
from utils.youtube import get_youtube_transcript


router = APIRouter(tags=["tools"])


@router.post("/process-ocr")
async def process_ocr(payload: GenerateRequest = Depends(parse_request)) -> dict:
    extracted = await run_in_threadpool(get_text, payload.file_payloads)
    return {"status": 200, "model": "ocr", "message": "OCR processed successfully.", "response": extracted, "prompt": payload.prompt}


@router.post("/crawl-youtube")
async def crawl_youtube(payload: GenerateRequest = Depends(parse_request)) -> dict:
    payload.require_prompt()
    match = re.search(r"https?://[^\s]+", payload.prompt)
    if not match:
        raise HTTPException(status_code=400, detail="Include a valid YouTube URL in the prompt.")
    url = match.group(0)
    try:
        transcript = await run_in_threadpool(get_youtube_transcript, url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL.") from error
    if not transcript.strip():
        raise HTTPException(status_code=502, detail="No YouTube transcript was returned.")
    assistant = await run_in_threadpool(get_assistant)
    prompt = f"User request: {payload.prompt}\nVideo URL: {url}\nUntrusted transcript:\n{transcript}"
    result = await run_in_threadpool(assistant.generate_response, prompt, payload.messages, [], agent="youtube")
    return {**text_response(result), "message": "YouTube transcript processed successfully."}


@router.post("/generate-diagram")
async def generate_diagram(payload: GenerateRequest = Depends(parse_request)) -> dict:
    payload.require_prompt()
    assistant = await run_in_threadpool(get_assistant)
    prompt = (
        f"User description:\n{payload.prompt}\n\nCurrent Mermaid code:\n{payload.code or 'None'}\n\n"
        "Modify the current diagram if supplied; otherwise create a new diagram. Return only complete Mermaid code."
    )
    result = await run_in_threadpool(assistant.generate_response, prompt, payload.messages, [], agent="diagram")
    return {**text_response(result), "message": "Diagram generated successfully."}
