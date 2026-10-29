from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchResults
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper, DuckDuckGoSearchAPIWrapper

class GenericTools:
    # Retain the constructor argument used by the inactive Llama implementation.
    def __init__(self, langchain_hub_name: str = "hwchase17/openai-functions-agent"):
        self.langchain_hub_name = langchain_hub_name

    def get_wikipedia_tool(self, top_k: int, doc_content_chars_max: int) -> WikipediaQueryRun:
        wikipedia_api_wrapper = WikipediaAPIWrapper(
            top_k_results=top_k,
            doc_content_chars_max=doc_content_chars_max
        )
        wikipedia_api_wrapper.wiki_client.set_user_agent("SophiaNet/1.0 (educational research assistant)")
        # wikipedia 1.4 defaults to HTTP; use the HTTPS API.
        client = wikipedia_api_wrapper.wiki_client.wikipedia
        client.API_URL = client.API_URL.replace("http://", "https://", 1)
        wiki = WikipediaQueryRun(api_wrapper=wikipedia_api_wrapper)
        return wiki

    def get_arxiv_tool(self, top_k: int, doc_content_chars_max: int) -> ArxivQueryRun:
        arxiv_api_wrapper = ArxivAPIWrapper(
            top_k_results=top_k,
            doc_content_chars_max=doc_content_chars_max
        )
        arxiv = ArxivQueryRun(api_wrapper=arxiv_api_wrapper)
        return arxiv

    def get_duckduckgo_tool(self, max_results: int) -> DuckDuckGoSearchResults:
        duckduckgo_api_wrapper = DuckDuckGoSearchAPIWrapper(
            max_results=max_results,
        )
        duckduckgo = DuckDuckGoSearchResults(api_wrapper=duckduckgo_api_wrapper)
        return duckduckgo

    def get_generic_tools(self, top_k: int = 3, doc_content_chars_max: int = 1000, max_results: int = 3) -> list:
        wikipedia_tool = self.get_wikipedia_tool(top_k, doc_content_chars_max)
        arxiv_tool = self.get_arxiv_tool(top_k, doc_content_chars_max)
        duckduckgo_tool = self.get_duckduckgo_tool(max_results)

        tools = [wikipedia_tool, arxiv_tool, duckduckgo_tool]
        return tools
