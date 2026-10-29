from functools import lru_cache

from utils.logger import logger
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from config.models import HUGGINGFACE_EMBEDDINGS_MODEL

@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=HUGGINGFACE_EMBEDDINGS_MODEL["MODEL_NAME"])


class RAGService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        self.embeddings = None
        self.vector_store = None

    def _ingest_files(self, files: list):
        # Reset vector store per request to prevent cross-query context leakage
        self.vector_store = None
        if not files:
            return
        try:
            from utils.files import process_files

            raw_docs = process_files(files)
            if not raw_docs:
                return
            split_docs = self.splitter.split_documents(raw_docs)
            if not split_docs:
                return
            if self.embeddings is None:
                self.embeddings = get_embeddings()
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
        except Exception as e:
            logger.error(f"File ingestion error: {e}")
            raise

    def _retrieve_context(self, query: str, k: int = 4) -> tuple[str, int]:
        """Return (context_text, chunks_retrieved)."""
        if not self.vector_store:
            return "No external context.", 0
        try:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
            docs: list[Document] = retriever.invoke(query)
            parts = []
            for d in docs:
                src = d.metadata.get("source")
                parts.append(f"[{src}] {d.page_content}")
            return "\n---\n".join(parts), len(docs)
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            raise
