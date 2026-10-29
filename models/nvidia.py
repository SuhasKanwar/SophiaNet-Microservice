import os

from langchain_openai import ChatOpenAI

from config.models import NVIDIA


def create_nvidia_model(model_name: str = NVIDIA["MODEL_NAME"]) -> ChatOpenAI:
    """Use NVIDIA's hosted, OpenAI-compatible API; no local inference or Groq."""
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is required for NVIDIA cloud inference.")
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=NVIDIA["BASE_URL"],
        temperature=NVIDIA["TEMPERATURE"],
        top_p=NVIDIA["TOP_P"],
        max_tokens=NVIDIA["MAX_TOKENS"],
        timeout=NVIDIA["TIMEOUT"],
        max_retries=NVIDIA["MAX_RETRIES"],
        use_responses_api=False,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
