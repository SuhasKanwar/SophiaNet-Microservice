import sys
import boto3
import json
import base64
import io
from PIL import Image

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.logger import logger
from utils.exception import SophiaNetException
from utils.s3_syncer import S3Syncer
from services.rag import RAGService

from config.prompts import STABLE_DIFFUSION_SYSTEM_PROMPT

class StableDiffusion(S3Syncer, RAGService):
    def __init__(self, model_id: str, runtime: str, region: str, max_tokens: int, bucket_name: str, object_key: str="", chunk_size: int=1000, chunk_overlap: int=150):
        S3Syncer.__init__(self, bucket_name=bucket_name, object_key=object_key)
        RAGService.__init__(self, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.model_id = model_id
        self.client = boto3.client(runtime, region_name=region)
        self.max_tokens = max_tokens
        self.system_prompt = STABLE_DIFFUSION_SYSTEM_PROMPT
        self.prompt_template = ChatPromptTemplate.from_messages([
            self.system_prompt,
            ("system", "Relevant context:\n{context}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

    def generate_image(self, prompt: str):
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    'prompt': prompt
                })
            )
            output_body = json.loads(response["body"].read().decode("utf-8"))
            
            logger.info(f"Stable Diffusion response structure: {list(output_body.keys())}")
            
            base64_output_image = None
            
            if "images" in output_body and output_body["images"]:
                base64_output_image = output_body["images"][0]
            elif "artifacts" in output_body and output_body["artifacts"]:
                base64_output_image = output_body["artifacts"][0].get("base64")
            elif "result" in output_body:
                base64_output_image = output_body["result"]
            else:
                logger.error(f"Unexpected response format: {output_body}")
                raise Exception(f"Unexpected response format. Available keys: {list(output_body.keys())}")
            
            if not base64_output_image:
                raise Exception("No image data found in the response")
                
            image_data = base64.b64decode(base64_output_image)
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            logger.error(f"Stable Diffusion error: {str(e)}")
            raise SophiaNetException(f"Stable Diffusion error: {str(e)}", sys)
    
    def generate_response(self, prompt: str, session_history: list, files: list) -> str:
        try:
            self._ingest_files(files)
            context = self._retrieve_context(prompt)
            history = session_history or []

            prompt_length = len(prompt)
            if prompt_length > self.max_tokens:
                prompt = prompt[0:self.max_tokens]
                prompt_length = len(prompt)

            context_length = (self.max_tokens - prompt_length) // 2

            enhanced_prompt = self.prompt_template.format_prompt(
                history=history[0:context_length] if history else [],
                input=prompt,
                context=context[0:context_length] if context else "No relevant context found."
            ).to_string()

            if len(enhanced_prompt) > self.max_tokens:
                enhanced_prompt = enhanced_prompt[:self.max_tokens]
                logger.warning(f"Enhanced prompt truncated to {self.max_tokens} tokens")

            image = self.generate_image(enhanced_prompt)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            s3_url = self.upload_file(img_byte_arr, content_type="image/png")
            return s3_url
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            raise SophiaNetException(f"Error in generate_response: {str(e)}", sys)