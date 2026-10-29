from functools import lru_cache

from fastapi import APIRouter, Depends
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
    payload.require_prompt()
    model_router = await run_in_threadpool(get_model_router)
    classification, description = await run_in_threadpool(model_router.route_request, payload.prompt)
    if classification == "image":
        return {**await image_response(payload), "response": description}
    return await generate_chat(payload)


@router.post("/generate-chat")
async def generate_chat(payload: GenerateRequest = Depends(parse_request)) -> dict:
    payload.require_prompt()
    assistant = await run_in_threadpool(get_assistant)
    result = await run_in_threadpool(assistant.generate_response, payload.prompt, payload.messages, payload.file_payloads)
    return text_response(result)


@router.post("/generate-image")
async def generate_image(payload: GenerateRequest = Depends(parse_request)) -> dict:
    payload.require_prompt()
    return await image_response(payload)
