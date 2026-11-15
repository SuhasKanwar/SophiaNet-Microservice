import asyncio
import json
import time
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from agents.debate import build_debate
from api.requests import GenerateRequest, parse_request
from models.nvidia import create_nvidia_model
from tools.custom_tools import CustomTools
from tools.generic_tools import GenericTools
from utils.logger import logger

router = APIRouter(tags=["debate"])


@lru_cache(maxsize=1)
def get_debate():
    return build_debate(create_nvidia_model(), [*GenericTools().get_generic_tools(), *CustomTools().get_custom_tools()])


@router.post("/generate-debate")
async def generate_debate(request: Request, payload: GenerateRequest = Depends(parse_request)):
    payload.require_prompt()
    if payload.files:
        raise HTTPException(400, "Debate currently supports text only. Use standard chat for attachments.")

    async def events():
        started = time.perf_counter()
        try:
            yield json.dumps({"type": "start", "agent": "advocate"}) + "\n"
            async with asyncio.timeout(300):
                graph = await asyncio.to_thread(get_debate)
                messages = [*payload.messages, HumanMessage(content=payload.prompt)]
                async for update in graph.astream({"messages": messages}, stream_mode="updates"):
                    if await request.is_disconnected():
                        return
                    for role, value in update.items():
                        yield json.dumps({"type": "contribution", "agent": role, "text": value[role]}) + "\n"
                        if role != "judge":
                            yield json.dumps({"type": "start", "agent": "critic" if role == "advocate" else "judge"}) + "\n"
                        else:
                            yield json.dumps({"type": "done", "text": value[role], "performance_metrics": {"latency_ms": round((time.perf_counter()-started)*1000), "agents": 3}}) + "\n"
        except Exception:
            logger.exception("Debate stream failed")
            yield json.dumps({"type": "error", "message": "The review panel could not finish. Please retry."}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
