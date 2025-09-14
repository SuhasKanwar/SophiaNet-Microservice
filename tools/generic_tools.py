from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper

class GenericTools:
    def get_wikipedia_tool(self, top_k: int, doc_content_chars_max: int) -> WikipediaQueryRun:
        wikipedia_api_wrapper = WikipediaAPIWrapper(
            top_k_results=top_k,
            doc_content_chars_max=doc_content_chars_max
        )
        wiki = WikipediaQueryRun(api_wrapper=wikipedia_api_wrapper)
        return wiki
    
    def get_arxiv_tool(self, top_k: int, doc_content_chars_max: int) -> ArxivQueryRun:
        arxiv_api_wrapper = ArxivAPIWrapper(
            top_k_results=top_k,
            doc_content_chars_max=doc_content_chars_max
        )
        arxiv = ArxivQueryRun(api_wrapper=arxiv_api_wrapper)
        return arxiv
    
    def get_generic_tools(self, top_k: int = 3, doc_content_chars_max: int = 1000):
        wikipedia_tool = self.get_wikipedia_tool(top_k, doc_content_chars_max)
        arxiv_tool = self.get_arxiv_tool(top_k, doc_content_chars_max)

        tools = [wikipedia_tool, arxiv_tool]
        return tools