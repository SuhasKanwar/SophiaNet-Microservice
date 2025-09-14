import sys
import os

from utils.logger import logger
from utils.exception import SophiaNetException
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from utils.files import process_files

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from config.prompts import LLAMA_SYSTEM_PROMPT

from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACE_ACCESS_TOKEN")

class Llama:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.system_prompt = LLAMA_SYSTEM_PROMPT

        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None
        try:
            self.llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=self.model_name)
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