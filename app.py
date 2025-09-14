import os
import sys
import json

import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

from models.llama import Llama
from config.models import LLAMA

from utils.logger import logger
from utils.exception import SophiaNetException

from dotenv import load_dotenv

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

app = fastapi.FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llama = Llama(model_name=LLAMA["MODEL_NAME"])

@app.get("/", tags=["Root"])
def read_root() -> dict:
    return {
        "status": 200,
        "message": "Welcome to SophiaNet. Visit /docs for API documentation."
    }

@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {
        "status": 200,
        "message": "SophiaNet microservice is healthy and running."
    }

@app.post('/generate-chat', tags=["Generate"])
async def generate_chat(request: fastapi.Request) -> dict:
    try:
        content_type = request.headers.get("content-type", "")
        prompt = ""
        session_history = []

        if "multipart/form-data" in content_type:
            form = await request.form()
            prompt = form.get("prompt", "").strip()
            session_history_str = form.get("session_history", "[]")
            session_history_raw = json.loads(session_history_str) if session_history_str else []
            uploads = form.getlist("files") or []
        else:
            data = await request.json()
            prompt = data.get("prompt", "").strip()
            session_history_raw = data.get("session_history", [])
            uploads = data.get("files", []) or []

        session_history = []
        for msg in session_history_raw:
            if msg.get("role") == "user":
                session_history.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                session_history.append(AIMessage(content=msg.get("content", "")))

        if not prompt:
            raise SophiaNetException("Prompt is required.")

        response = llama.generate_response(prompt, session_history, uploads)

        return {
            "status": 200,
            "response": response
        }
    except SophiaNetException:
        raise
    except Exception as e:
        logger.error(f"Error in /generate-chat: {str(e)}")
        raise SophiaNetException("An error occurred while generating chat response.", sys)

@app.exception_handler(SophiaNetException)
def sophianet_exception_handler(request: fastapi.Request, exc: SophiaNetException):
    logger.error(f"SophiaNet Exception: {exc.error_message}")
    return fastapi.responses.JSONResponse(
        status_code=400,
        content={
            "status": 400,
            "message": exc.error_message
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)