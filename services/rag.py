import os

from utils.logger import logger
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from utils.files import process_files

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from config.models import HUGGINGFACE_EMBEDDINGS_MODEL

from dotenv import load_dotenv

load_dotenv()
os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACE_ACCESS_TOKEN")

class RAGService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        self.embeddings = HuggingFaceEmbeddings(model_name=HUGGINGFACE_EMBEDDINGS_MODEL["MODEL_NAME"])
        self.vector_store = None

    def _ingest_files(self, files: list):
        if not files:
            return
        try:
            raw_docs = process_files(files)
            if not raw_docs:
                return
            split_docs = self.splitter.split_documents(raw_docs)
            if not split_docs:
                return
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            else:
                self.vector_store.add_documents(split_docs)
        except Exception as e:
            logger.error(f"File ingestion error: {e}")
    
    def _retrieve_context(self, query: str, k: int = 4) -> str:
        if not self.vector_store:
            return "No external context."
        try:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
            docs: list[Document] = retriever.invoke(query)
            parts = []
            for d in docs:
                src = d.metadata.get("source")
                parts.append(f"[{src}] {d.page_content}")
            return "\n---\n".join(parts)
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return "Context retrieval failed."