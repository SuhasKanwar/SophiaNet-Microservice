from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from api.requests import GenerateRequest, parse_request
from api.responses import text_response
from services.assistant import get_assistant
from services.images import generate_image_with_fallback
from services.router import ModelRouter


router = APIRouter(tags=["generate"])


@lru_cache(maxsize=1)
def get_model_router() -> ModelRouter:
    return ModelRouter()


async def image_response(payload: GenerateRequest) -> dict:
    result, model = await run_in_threadpool(
        generate_image_with_fallback, payload.prompt, payload.messages, payload.file_payloads,
    )
    return {"status": 200, "model": model, "image_url": result["s3_url"], "performance_metrics": result["performance_metrics"]}


@router.post("/generate")
async def generate_response(payload: GenerateRequest = Depends(parse_request)) -> dict:
    if payload.command:
        from services.commands import run_command
        return await run_command(payload)
    payload.require_prompt()
    model_router = await run_in_threadpool(get_model_router)
    classification, description = await run_in_threadpool(model_router.route_request, payload.prompt)
    if classification == "image":
        return {**await image_response(payload), "response": description}
    return await generate_chat(payload)


@router.post("/generate-chat")
async def generate_chat(payload: GenerateRequest = Depends(parse_request)) -> dict:
    if payload.command:
        raise HTTPException(400, "Use /generate for chat commands or /generate-debate for agent-battleground.")
    payload.require_prompt()
    assistant = await run_in_threadpool(get_assistant)
    result = await run_in_threadpool(assistant.generate_response, payload.prompt, payload.messages, payload.file_payloads)
    return text_response(result)


@router.post("/generate-image")
async def generate_image(payload: GenerateRequest = Depends(parse_request)) -> dict:
    if payload.command:
        raise HTTPException(400, "Use /generate for chat commands or /generate-debate for agent-battleground.")
    payload.require_prompt()
    return await image_response(payload)


@router.post("/generate-summary")
async def generate_summary(payload: GenerateRequest = Depends(parse_request)) -> dict:
    from services.adk_summary import summarize
    from utils.metrics import Timer
    payload.require_prompt()
    if payload.files or payload.command:
        raise HTTPException(400, "Summary endpoint accepts text without commands or attachments.")
    with Timer() as timer:
        result = await summarize(payload.prompt)
    return {**text_response({"text": result, "performance_metrics": {"latency_ms": timer.elapsed_ms}}), "engine": "google-adk"}
