import os
import sys

import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

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
        data = await request.json()
        prompt = data.get("prompt", "")
        session_history = data.get("session_history", [])
        if not prompt:
            raise SophiaNetException("Prompt is required.")

        response = llama.generate_response(prompt, session_history)
        
        return {
            "status": 200,
            "response": response
        }
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