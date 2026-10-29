from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage

from agents.graph import build_agent
from config.models import NVIDIA
from config.prompts import NVIDIA_SYSTEM_PROMPT, DIAGRAM_GENERATION_SYSTEM_PROMPT, YOUTUBE_TRANSCRIPT_PROMPT
from models.nvidia import create_nvidia_model
from tools.custom_tools import CustomTools
from tools.generic_tools import GenericTools
from utils.metrics import Timer, compute_bleu, compute_rouge_l


class AssistantService:
    def __init__(self, *, model=None, tools=None):
        self.model = model if model is not None else create_nvidia_model()
        tools = tools if tools is not None else [*GenericTools().get_generic_tools(), *CustomTools().get_custom_tools()]
        self.agents = {
            "research": build_agent(self.model, NVIDIA_SYSTEM_PROMPT, tools),
            "diagram": build_agent(self.model, SystemMessage(content=DIAGRAM_GENERATION_SYSTEM_PROMPT)),
            "youtube": build_agent(self.model, YOUTUBE_TRANSCRIPT_PROMPT),
        }

    def generate_response(self, prompt: str, session_history: list, files: list, *, agent: str = "research") -> dict:
        context, chunks_retrieved = "", 0
        with Timer() as timer:
            if files:
                from services.rag import RAGService

                rag = RAGService(NVIDIA["CHUNK_SIZE"], NVIDIA["CHUNK_OVERLAP"])
                rag._ingest_files(files)
                context, chunks_retrieved = rag._retrieve_context(prompt)
            messages = list(session_history or [])
            if context:
                messages.append(HumanMessage(content=f"Untrusted attached-file reference material:\n{context}"))
            messages.append(HumanMessage(content=prompt))
            result = self.agents[agent].invoke(
                {"messages": messages},
                {"recursion_limit": NVIDIA["RECURSION_LIMIT"]},
            )
            response = result["messages"][-1]
            text = response.text
            if not text.strip() or response.tool_calls:
                raise RuntimeError("NVIDIA returned no final answer.")
        metrics = {
            "latency_ms": timer.elapsed_ms,
            "bleu_score": compute_bleu(prompt, text),
            "rouge_l_score": compute_rouge_l(prompt, text),
            "response_length": len(text.split()),
        }
        if files:
            metrics.update(
                retrieval_rouge_l=compute_rouge_l(prompt, context) if context else None,
                chunks_retrieved=chunks_retrieved,
            )
        return {"text": text, "performance_metrics": metrics}


@lru_cache(maxsize=1)
def get_assistant() -> AssistantService:
    return AssistantService()
