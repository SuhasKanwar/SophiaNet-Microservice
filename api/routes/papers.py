from datetime import date
from openai import APIError, RateLimitError
from utils.logger import logger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool
from services.paper_research import research_papers as search_papers

router = APIRouter(tags=["research papers"])


class PaperSearch(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    since: int | None = Field(default=None, ge=1900)
    limit: int = Field(default=10, ge=1, le=20)

    @field_validator('query')
    @classmethod
    def trim_query(cls, value):
        if len(value.strip()) < 2:
            raise ValueError('Enter at least two nonblank characters')
        return value.strip()

    @field_validator('since')
    @classmethod
    def valid_year(cls, value):
        if value and value > date.today().year:
            raise ValueError('Year cannot be in the future')
        return value


@router.post('/search-papers')
async def paper_search(payload: PaperSearch):
    try:
        result = await run_in_threadpool(search_papers, payload.query, payload.since, payload.limit)
    except RateLimitError as error:
        logger.warning("Paper search model rate limited")
        raise HTTPException(503, 'The research model is busy. Please try again shortly.') from error
    except APIError as error:
        logger.warning("Paper search model failed: %s", type(error).__name__)
        raise HTTPException(502, 'The research model could not complete the search. Please retry.') from error
    except ValueError as error:
        logger.warning("Paper search output rejected: %s", type(error).__name__)
        raise HTTPException(502, 'The research model returned an invalid selection after correction. Please retry your search.') from error
    except RuntimeError as error:
        logger.warning("Paper search unavailable: %s", type(error).__name__)
        raise HTTPException(502, 'Scholarly sources or the research service are unavailable. Please retry shortly.') from error
    return {"status": 200, **result}
