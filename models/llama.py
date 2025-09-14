import sys
import os

from utils.logger import logger
from utils.exception import SophiaNetException
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.prompts import LLAMA_SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class Llama:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.system_prompt = LLAMA_SYSTEM_PROMPT
        try:
            self.llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=self.model_name)
            self.prompt_template = ChatPromptTemplate.from_messages([
                self.system_prompt,
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            self.chain = self.prompt_template | self.llm
        except Exception as e:
            logger.error(f"Error initializing LLaMA model: {str(e)}")
            raise SophiaNetException(f"Failed to initialize LLaMA model ({self.model_name})", sys)

    def generate_response(self, prompt: str, session_history: list, files: list) -> str:
        try:
            history = session_history or []
            response = self.chain.invoke({
                "history": history,
                "input": prompt
            })
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise SophiaNetException(f"Failed to generate response from LLaMA model ({self.model_name})", sys)