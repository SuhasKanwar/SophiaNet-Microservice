from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from services.study import get_study
from utils.metrics import Timer

router = APIRouter(tags=["study"])


class StudyRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=10000, pattern=r"\S")


@router.post("/generate-quiz")
async def generate_quiz(payload: StudyRequest):
    with Timer() as timer:
        service = await run_in_threadpool(get_study)
        quiz = await run_in_threadpool(service.generate, payload.topic)
    return {"status": 200, "model": "nvidia", "quiz": quiz.model_dump(), "performance_metrics": {"latency_ms": timer.elapsed_ms}}


@router.post("/generate-flashcards")
async def generate_flashcards(payload: StudyRequest):
    with Timer() as timer:
        service = await run_in_threadpool(get_study)
        deck = await run_in_threadpool(service.flashcards, payload.topic)
    return {"status": 200, "model": "nvidia", "deck": deck.model_dump(), "performance_metrics": {"latency_ms": timer.elapsed_ms}}
