import os
import sys
import json
import re

import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, AIMessage

from models.llama import Llama
from models.stable_diffusion import StableDiffusion
from models.flux import Flux
from services.router import ModelRouter

from config.models import LLAMA, STABLE_DIFFUSION, ROUTER_MODEL, FLUX, IMAGE_MODEL, IMAGE_MODELS, FALLBACK_IMAGE_MODEL
from config.cloud import S3_BUCKET
from config.prompts import GENERIC_TOOLS_PROMPT, DIAGRAM_GENERATION_SYSTEM_PROMPT, YOUTUBE_TRANSCRIPT_PROMPT

from utils.logger import logger
from utils.exception import SophiaNetException
from utils.youtube import get_youtube_transcript
from utils.ocr import get_text

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
flux = Flux(
    model_id=FLUX["MODEL_ID"],
    provider=FLUX["PROVIDER"],
    max_tokens=FLUX["MAX_TOKENS"],
    bucket_name=S3_BUCKET["AWS_S3_BUCKET_NAME"],
    object_key=S3_BUCKET["AWS_S3_IMAGES_OBJECT_KEY"],
    chunk_size=FLUX["CHUNK_SIZE"],
    chunk_overlap=FLUX["CHUNK_OVERLAP"]
)
router = ModelRouter(model_name=ROUTER_MODEL["MODEL_NAME"])

IMAGE_GENERATORS = {
    IMAGE_MODELS.STABLE_DIFFUSION: stability,
    IMAGE_MODELS.FLUX: flux
}

ACTIVE_IMAGE_GENERATOR = IMAGE_GENERATORS[IMAGE_MODEL]
ACTIVE_IMAGE_MODEL_NAME = IMAGE_MODEL.value
FALLBACK_IMAGE_GENERATOR = IMAGE_GENERATORS[FALLBACK_IMAGE_MODEL]
FALLBACK_IMAGE_MODEL_NAME = FALLBACK_IMAGE_MODEL.value


def _generate_image_with_fallback(prompt: str, session_history: list, files_payload: list) -> tuple[str, str]:
    try:
        s3_url = ACTIVE_IMAGE_GENERATOR.generate_response(prompt, session_history, files_payload)
        return s3_url, ACTIVE_IMAGE_MODEL_NAME
    except Exception as primary_error:
        if IMAGE_MODEL == FALLBACK_IMAGE_MODEL:
            raise primary_error

        logger.warning(
            f"Primary image model '{ACTIVE_IMAGE_MODEL_NAME}' failed; "
            f"falling back to '{FALLBACK_IMAGE_MODEL_NAME}'. Error: {str(primary_error)}"
        )
        s3_url = FALLBACK_IMAGE_GENERATOR.generate_response(prompt, session_history, files_payload)
        return s3_url, FALLBACK_IMAGE_MODEL_NAME

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
            s3_url, model_name = _generate_image_with_fallback(prompt, session_history, files_payload)
            return {
                "status": 200,
                "model": model_name,
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

        s3_url, model_name = _generate_image_with_fallback(prompt, session_history, files_payload)

        return {
            "status": 200,
            "model": model_name,
            "image_url": s3_url
        }
    except Exception as e:
        logger.error(f"Error in /generate-image: {str(e)}")
        raise SophiaNetException("An error occurred while generating image.", sys)

@app.post('/process-ocr', tags=["ocr"])
async def process_ocr(request: fastapi.Request) -> dict:
    try:
        content_type = request.headers.get("content-type", "")
        prompt = ""
        files_payload = []

        if "multipart/form-data" in content_type:
            form = await request.form()
            prompt = (form.get("prompt") or "").strip()
            uploads_raw = form.getlist("files") or []
            for f in uploads_raw:
                if hasattr(f, "filename"):
                    data = await f.read()
                    files_payload.append({"filename": f.filename, "content": data})
        else:
            data = await request.json()
            prompt = (data.get("prompt") or "").strip()
            json_files = data.get("files", []) or []
            for f in json_files:
                if isinstance(f, dict) and "content" in f and "filename" in f:
                    files_payload.append(f)

        extracted_text = get_text(files_payload)

        return {
            "status": 200,
            "message": "OCR processed successfully.",
            "model": "ocr",
            "response": extracted_text,
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"Error in /process-ocr: {str(e)}")
        raise SophiaNetException("An error occurred while processing OCR.", sys)

@app.post('/crawl-youtube', tags=["youtube"])
async def crawl_youtube(request: fastapi.Request) -> dict:
    try:
        request_data = await request.json()
        raw_prompt = (request_data.get("prompt") or "").strip()
        if not raw_prompt:
            raise SophiaNetException("Prompt is required and must contain a YouTube URL.")

        url_match = re.search(r'(https?://[^\s]+)', raw_prompt)
        if not url_match:
            raise SophiaNetException("No URL found in the prompt. Please include a valid YouTube URL.", sys)
        youtube_url = url_match.group(1)

        transcript = get_youtube_transcript(youtube_url)
        if not transcript.strip():
            raise SophiaNetException("Could not retrieve transcript for the provided YouTube URL.", sys)

        prompt = (
            f"{YOUTUBE_TRANSCRIPT_PROMPT.content}\n\n"
            f"Video URL: {youtube_url}\n\n"
            f"Transcript:\n{transcript}"
        )
        response = llama.generate_response(prompt, session_history=[], files=[])

        return {
            "status": 200,
            "message": "YouTube transcript processed successfully.",
            "model": "LLaMA",
            "response": response
        }
    except Exception as e:
        logger.error(f"Error in /crawl-youtube: {str(e)}")
        raise SophiaNetException("An error occurred while crawling YouTube.", sys)

@app.post('/generate-diagram', tags=["generate"])
async def generate_diagram(request: fastapi.Request) -> dict:
    try:
        content_type = request.headers.get("content-type", "")
        user_prompt = ""
        current_code = ""

        if "multipart/form-data" in content_type:
            form = await request.form()
            user_prompt = (form.get("prompt") or "").strip()
            current_code = (form.get("code") or "").strip()
        else:
            data = await request.json()
            user_prompt = (data.get("prompt") or "").strip()
            current_code = (data.get("code") or "").strip()

        if not user_prompt:
            raise SophiaNetException("Prompt is required for diagram generation.")

        full_prompt = (
            f"{DIAGRAM_GENERATION_SYSTEM_PROMPT}\n\n"
            f"User description:\n{user_prompt}\n\n"
            f"Current Mermaid/code context (if any):\n"
            f"{current_code if current_code.strip() else 'None'}\n\n"
            "If current Mermaid code is provided, MODIFY and IMPROVE that code to satisfy the user description. "
            "Otherwise, CREATE a new diagram. "
            "Always return ONLY the final, complete Mermaid diagram code."
        )

        response = llama.generate_response(full_prompt, session_history=[], files=[])
        mermaid_code = response.strip()

        return {
            "status": 200,
            "message": "Diagram generated successfully.",
            "model": "LLaMA",
            "response": mermaid_code
        }
    except SophiaNetException:
        raise
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