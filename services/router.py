from typing import Literal

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict

from config.models import ROUTER_MODEL
from config.prompts import ROUTER_MODEL_SYSTEM_PROMPT
from models.nvidia import create_nvidia_model


class RouteDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: Literal["text", "image"]
    image_description: str = ""


class ModelRouter:
    def __init__(self, model_name: str = ROUTER_MODEL["MODEL_NAME"], *, model=None):
        self.router_model = (model if model is not None else create_nvidia_model(model_name)).bind(
            response_format=ROUTER_MODEL["RESPONSE_FORMAT"],
            temperature=0,
            max_tokens=256,
        )

    def route_request(self, prompt: str) -> tuple[str, str]:
        response = self.router_model.invoke([
            ROUTER_MODEL_SYSTEM_PROMPT,
            HumanMessage(content=prompt),
        ])
        decision = RouteDecision.model_validate_json(response.content)
        return decision.classification, decision.image_description
