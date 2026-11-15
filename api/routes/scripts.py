from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from utils.metrics import Timer

router = APIRouter(tags=["scripts"])


class ScriptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=10000, pattern=r"\S")
    kind: Literal["narration", "code"] = "narration"


@router.post("/generate-script")
async def generate_script(payload: ScriptRequest):
    from services.scripts import generate_script as run
    with Timer() as timer:
        result = await run_in_threadpool(run, payload.prompt, payload.kind)
    return {"status": 200, "model": "nvidia", "engine": "crewai", "response": result, "performance_metrics": {"latency_ms": timer.elapsed_ms}}
