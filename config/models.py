LLAMA = {
    "MODEL_NAME": "llama-3.3-70b-versatile",
    "CHUNK_SIZE": 1000,
    "CHUNK_OVERLAP": 150
}

STABLE_DIFFUSION = {
    "MODEL_ID": "stability.sd3-5-large-v1:0",
    "RUNTIME": "bedrock-runtime",
    "REGION": "us-west-2",
    "MAX_TOKENS": 77,
    "CHUNK_SIZE": 1000,
    "CHUNK_OVERLAP": 150
}

HUGGINGFACE_EMBEDDINGS_MODEL = {
    "MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2"
}

ROUTER_MODEL = {
    "MODEL_NAME": "meta-llama/llama-4-scout-17b-16e-instruct",
    "RESPONSE_FORMAT": {
        "type": "json_schema",
        "json_schema": {
            "name": "RouterOutput",
            "schema": {
                "type": "object",
                "properties": {
                    "classification": {
                        "type": "string",
                        "enum": ["text", "image"]
                    },
                    "image_description": {
                        "type": "string",
                        "description": "The generic description about the image in case of image model."
                    }
                },
                "required": ["classification"],
                "additionalProperties": False
            }
        }
    }
}

IMAGE_CAPTIONING_MODEL = {
    "MODEL_NAME": "Salesforce/blip-image-captioning-base",
    "TASK": "image-captioning",
    "PROCESSOR": "Salesforce/blip-image-captioning-base"
}

CLIP_MODEL = {
    "MODEL_NAME": "openai/clip-vit-base-patch32",
    "PROCESSOR": "openai/clip-vit-base-patch32",
    "EMBEDDING_DIM": 512
}