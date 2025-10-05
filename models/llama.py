import sys
import os

from utils.logger import logger
from utils.exception import SophiaNetException
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from services.rag import RAGService
from tools.generic_tools import GenericTools

from config.prompts import LLAMA_SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACE_ACCESS_TOKEN")

class Llama(RAGService, GenericTools):
    def __init__(self, model_name: str, langchain_hub_name: str, chunk_size: int=1000, chunk_overlap: int=150):
        RAGService.__init__(self, chunk_size, chunk_overlap)
        GenericTools.__init__(self, langchain_hub_name=langchain_hub_name)
        self.model_name = model_name
        self.system_prompt = LLAMA_SYSTEM_PROMPT
        try:
            self.llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=self.model_name)
            self.llm.bind_tools(self.get_generic_tools())
            self.prompt_template = ChatPromptTemplate.from_messages([
                self.system_prompt,
                ("system", "Relevant context (may be partial):\n{context}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            self.chain = self.prompt_template | self.llm
        except Exception as e:
            logger.error(f"Error initializing LLaMA model: {str(e)}")
            raise SophiaNetException(f"Failed to initialize LLaMA model ({self.model_name})", sys)

    def generate_response(self, prompt: str, session_history: list, files: list) -> str:
        try:
            self._ingest_files(files)

            context = self._retrieve_context(prompt)

            history = session_history or []
            response = self.chain.invoke({
                "history": history,
                "input": prompt,
                "context": context
            })
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise SophiaNetException(f"Failed to generate response from LLaMA model ({self.model_name})", sys)