import sys
import os

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from dotenv import load_dotenv

from config.custom_tools import SCRAPE_WEBSITE_TOOL
from utils.logger import logger
from utils.exception import SophiaNetException

load_dotenv()
os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACE_ACCESS_TOKEN")

class CustomTools():
    def get_scrape_website_tool(self, url: str) -> str:
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vectorstore = FAISS.from_documents(chunks, embeddings)
            retriever = vectorstore.as_retriever()
            tool = create_retriever_tool(
                retriever,
                SCRAPE_WEBSITE_TOOL["name"],
                SCRAPE_WEBSITE_TOOL["description"]
            )
            return tool
        except Exception as e:
            logger.error(f"{SCRAPE_WEBSITE_TOOL['name']} tool error: {str(e)}")
            raise SophiaNetException(f"{SCRAPE_WEBSITE_TOOL['name']} tool error: {str(e)}", sys)