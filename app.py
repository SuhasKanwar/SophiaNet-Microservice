import os
import sys
import json

import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

from models.llama import Llama
from models.stable_diffusion import StableDiffusion
from services.router import ModelRouter

from config.models import LLAMA, STABLE_DIFFUSION, ROUTER_MODEL
from config.cloud import S3_BUCKET
from config.prompts import GENERIC_TOOLS_PROMPT

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

llama = Llama(
    model_name=LLAMA["MODEL_NAME"],
    langchain_hub_name=GENERIC_TOOLS_PROMPT["langchain_hub_name"],
    chunk_size=LLAMA["CHUNK_SIZE"],
    chunk_overlap=LLAMA["CHUNK_OVERLAP"]
)
stability = StableDiffusion(
    model_id=STABLE_DIFFUSION["MODEL_ID"],
    runtime=STABLE_DIFFUSION["RUNTIME"],
    region=STABLE_DIFFUSION["REGION"],
    max_tokens=STABLE_DIFFUSION["MAX_TOKENS"],
    bucket_name=S3_BUCKET["AWS_S3_BUCKET_NAME"],
    object_key=S3_BUCKET["AWS_S3_IMAGES_OBJECT_KEY"],
    chunk_size=STABLE_DIFFUSION["CHUNK_SIZE"],
    chunk_overlap=STABLE_DIFFUSION["CHUNK_OVERLAP"]
)
router = ModelRouter(model_name=ROUTER_MODEL["MODEL_NAME"])

@app.get("/", tags=["Root"])
def root() -> dict:
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

@app.post('/generate', tags=["generate"])
async def generate_response(request: fastapi.Request) -> dict:
    try:
        content_type = request.headers.get("content-type", "")
        prompt = ""
        session_history = []

        if "multipart/form-data" in content_type:
            form = await request.form()
            prompt = form.get("prompt", "").strip()
            session_history_str = form.get("session_history", "[]")
            session_history_raw = json.loads(session_history_str) if session_history_str else []
            uploads_raw = form.getlist("files") or []
            files_payload = []
            for f in uploads_raw:
                if hasattr(f, "filename"):
                    data = await f.read()
                    files_payload.append({"filename": f.filename, "content": data})
        else:
            data = await request.json()
            prompt = data.get("prompt", "").strip()
            session_history_raw = data.get("session_history", [])
            json_files = data.get("files", []) or []
            files_payload = []
            for f in json_files:
                if isinstance(f, dict):
                    files_payload.append(f)

        session_history = []
        for msg in session_history_raw:
            if msg.get("role") == "user":
                session_history.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                session_history.append(AIMessage(content=msg.get("content", "")))

        if not prompt:
            raise SophiaNetException("Prompt is required.")
        
        classification, image_description = router.route_request(prompt)
        if classification == "text":
            response = llama.generate_response(prompt, session_history, files_payload)
            return {
                "status": 200,
                "model": "llama",
                "response": response
            }
        elif classification == "image":
            s3_url = stability.generate_response(prompt, session_history, files_payload)
            return {
                "status": 200,
                "model": "stable_diffusion",
                "image_url": s3_url,
                "response": image_description or ""
            }
        else:
            return {
                "status": 400,
                "message": "Unable to classify the prompt to a valid model."
            }

    except Exception as e:
        logger.error(f"Error in /generate: {str(e)}")
        raise SophiaNetException("An error occurred while generating response.", sys)

@app.post('/generate-chat', tags=["generate"])
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
            uploads_raw = form.getlist("files") or []
            files_payload = []
            for f in uploads_raw:
                if hasattr(f, "filename"):
                    data = await f.read()
                    files_payload.append({"filename": f.filename, "content": data})
        else:
            data = await request.json()
            prompt = data.get("prompt", "").strip()
            session_history_raw = data.get("session_history", [])
            json_files = data.get("files", []) or []
            files_payload = []
            for f in json_files:
                if isinstance(f, dict):
                    files_payload.append(f)

        session_history = []
        for msg in session_history_raw:
            if msg.get("role") == "user":
                session_history.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                session_history.append(AIMessage(content=msg.get("content", "")))

        if not prompt:
            raise SophiaNetException("Prompt is required.")

        response = llama.generate_response(prompt, session_history, files_payload)

        return {
            "status": 200,
            "model": "llama",
            "response": response
        }
    except Exception as e:
        logger.error(f"Error in /generate-chat: {str(e)}")
        raise SophiaNetException("An error occurred while generating chat response.", sys)

@app.post('/generate-image', tags=["generate"])
async def generate_image(request: fastapi.Request) -> dict:
    try:
        content_type = request.headers.get("content-type", "")
        prompt = ""
        session_history = []

        if "multipart/form-data" in content_type:
            form = await request.form()
            prompt = form.get("prompt", "").strip()
            session_history_str = form.get("session_history", "[]")
            session_history_raw = json.loads(session_history_str) if session_history_str else []
            uploads_raw = form.getlist("files") or []
            files_payload = []
            for f in uploads_raw:
                if hasattr(f, "filename"):
                    data = await f.read()
                    files_payload.append({"filename": f.filename, "content": data})
        else:
            data = await request.json()
            prompt = data.get("prompt", "").strip()
            session_history_raw = data.get("session_history", [])
            json_files = data.get("files", []) or []
            files_payload = []
            for f in json_files:
                if isinstance(f, dict):
                    files_payload.append(f)

        session_history = []
        for msg in session_history_raw:
            if msg.get("role") == "user":
                session_history.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                session_history.append(AIMessage(content=msg.get("content", "")))

        if not prompt:
            raise SophiaNetException("Prompt is required.")

        s3_url = stability.generate_response(prompt, session_history, files_payload)

        return {
            "status": 200,
            "model": "stable_diffusion",
            "image_url": s3_url
        }
    except Exception as e:
        logger.error(f"Error in /generate-image: {str(e)}")
        raise SophiaNetException("An error occurred while generating image.", sys)

@app.post('/process-ocr', tags=["ocr"])
async def process_ocr(request: fastapi.Request) -> dict:
    try:
        return {
            "status": 200,
            "message": "OCR processing endpoint is under development.",
            "model": "LLaMA",
            "response": "Dummy OCR response."
        }
    except Exception as e:
        logger.error(f"Error in /process-ocr: {str(e)}")
        raise SophiaNetException("An error occurred while processing OCR.", sys)

@app.post('/crawl-youtube', tags=["youtube"])
async def crawl_youtube(request: fastapi.Request) -> dict:
    try:
        return {
            "status": 200,
            "message": "YouTube crawling endpoint is under development.",
            "model": "LLaMA",
            "response": "Dummy YouTube response."
        }
    except Exception as e:
        logger.error(f"Error in /crawl-youtube: {str(e)}")
        raise SophiaNetException("An error occurred while crawling YouTube.", sys)

@app.post('/generate-diagram', tags=["generate"])
async def generate_diagram(request: fastapi.Request) -> dict:
    try:
        return {
            "status": 200,
            "message": "Diagram generation endpoint is under development.",
            "model": "LLaMA",
            "response": "Dummy diagram response."
        }
    except Exception as e:
        logger.error(f"Error in /generate-diagram: {str(e)}")
        raise SophiaNetException("An error occurred while generating diagram.", sys)

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