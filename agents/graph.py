from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


def build_agent(model, system_prompt: SystemMessage, tools=()):
    """Compile a model -> tools -> model loop with per-invocation message state."""
    bound_model = model.bind_tools(tools) if tools else model

    def respond(state: MessagesState):
        return {"messages": [bound_model.invoke([system_prompt, *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", respond)
    graph.add_edge(START, "agent")
    if tools:
        graph.add_node("tools", ToolNode(tools, handle_tool_errors="Tool failed. Try another source or explain that verification is unavailable."))
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_edge("tools", "agent")
    else:
        graph.add_edge("agent", END)
    return graph.compile()
