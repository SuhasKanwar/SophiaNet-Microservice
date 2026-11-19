"""Chat command handlers reuse the same services as the studio pages."""
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from api.requests import GenerateRequest
from api.responses import text_response
from utils.metrics import Timer


async def run_command(payload: GenerateRequest) -> dict:
    payload.require_prompt()
    if payload.files:
        raise HTTPException(400, "Slash commands accept text only. Remove attachments first.")
    if payload.command == "agent-battleground":
        raise HTTPException(400, "Use /generate-debate for agent-battleground commands.")
    if len(payload.prompt) > (500 if payload.command == "research" else 10000):
        raise HTTPException(400, "Command input is too long (research: 500 characters; other commands: 10000).")
    with Timer() as timer:
        if payload.command == "summarize":
            from services.adk_summary import summarize
            text = await summarize(payload.prompt)
        elif payload.command in ("quiz", "flashcards"):
            from services.study import get_study
            study = await run_in_threadpool(get_study)
            if payload.command == "quiz":
                result = await run_in_threadpool(study.generate, payload.prompt)
                questions = []
                for index, question in enumerate(result.questions, 1):
                    options = "\n".join(f"- {chr(65 + i)}. {option}" for i, option in enumerate(question.options))
                    questions.append(f"### {index}. {question.question}\n{options}\n\n**Answer: {chr(65 + question.answer)}.** {question.explanation}")
                text = f"## {result.title}\n\n" + "\n\n".join(questions)
            else:
                result = await run_in_threadpool(study.flashcards, payload.prompt)
                text = f"## {result.title}\n\n" + "\n\n".join(f"### {card.front}\n{card.back}" for card in result.cards)
        elif payload.command == "research":
            from services.paper_research import research_papers
            result = await run_in_threadpool(research_papers, payload.prompt, None, 5)
            text = "## Research papers\n\n" + "\n\n".join(
                f"### {paper['title']}\n{paper.get('year') or 'Year unavailable'} · {paper.get('venue') or 'Preprint'}\n\n"
                f"{paper['relevance']}\n\n[Read paper]({paper['url']})" for paper in result['papers']
            )
            if not result['papers']:
                text += "No relevant papers were found. Try a more specific question."
            if result.get('warnings'):
                text += "\n\nSome scholarly sources were unavailable; these results may be incomplete."
        else:
            raise HTTPException(400, "Unknown chat command.")
    return {**text_response({"text": text, "performance_metrics": {"latency_ms": timer.elapsed_ms}}),
            "command": payload.command, "engine": "google-adk" if payload.command == "summarize" else "langgraph" if payload.command == "research" else "langchain"}
