import sys

from utils.logger import logger
from utils.exception import SophiaNetException

class Llama:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate_response(self, prompt: str, session_history: list, files: list) -> str:
        try:
            response = f"Response from {self.model_name} for prompt: {prompt} with history: {session_history} and files: {files}"
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise SophiaNetException(f"Failed to generate response from LLaMA model ({self.model_name})", sys)