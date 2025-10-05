from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchResults
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper, DuckDuckGoSearchAPIWrapper
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain import hub

class GenericTools:
    def __init__(self, langchain_hub_name: str):
        self.langchain_hub_name = langchain_hub_name
        self.prompt = hub.pull(self.langchain_hub_name)

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
    
    # Not using the agent executor for now, using direct tool binding and chain invocation
    def get_agent_executor(self, llm) -> AgentExecutor:
        tools = self.get_generic_tools()
        agent = create_openai_tools_agent(llm, tools, self.prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )
        return agent_executor