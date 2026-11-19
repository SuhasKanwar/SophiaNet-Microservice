import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

load_dotenv()

from api.routes import generation, health, tools, debate, scripts, study, papers
from services.guardrails import guard_request
from utils.exception import SophiaNetException
from utils.logger import logger


app = FastAPI(title="SophiaNet AI Microservice")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (health.router, generation.router, tools.router, debate.router, scripts.router, study.router, papers.router):
    app.include_router(router, dependencies=[] if router is health.router else [Depends(guard_request)])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": exc.status_code, "message": exc.detail})


@app.exception_handler(SophiaNetException)
async def sophianet_exception_handler(request: Request, exc: SophiaNetException):
    logger.error("SophiaNet request failed: %s", exc)
    return JSONResponse(status_code=502, content={"status": 502, "message": "An upstream AI or tool service failed."})


@app.exception_handler(Exception)
async def service_exception_handler(request: Request, exc: Exception):
    logger.error("Request failed on %s", request.url.path, exc_info=exc)
    return JSONResponse(status_code=502, content={"status": 502, "message": "An AI or tool service is unavailable. Please retry later."})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
