import unittest

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError

from agents.graph import build_agent


@tool
def lookup(topic: str) -> str:
    """Look up a topic in the test source."""
    return f"Evidence about {topic}"


class ScriptedModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []
        self.tools = []

    def bind_tools(self, tools):
        self.tools = list(tools)
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        return next(self.responses)


class AgentTests(unittest.TestCase):
    def test_tool_results_return_to_model(self):
        model = ScriptedModel([
            AIMessage(content="", tool_calls=[{"name": "lookup", "args": {"topic": "graphs"}, "id": "call_1"}]),
            AIMessage(content="Graphs connect nodes."),
        ])
        agent = build_agent(model, SystemMessage(content="Use evidence."), [lookup])
        result = agent.invoke({"messages": [HumanMessage(content="Explain graphs")]})
        self.assertEqual(result["messages"][-1].content, "Graphs connect nodes.")
        self.assertEqual(model.tools, [lookup])
        self.assertIsInstance(model.calls[1][-1], ToolMessage)
        self.assertEqual(model.calls[1][-1].content, "Evidence about graphs")

    def test_tool_failure_is_returned_to_agent(self):
        model = ScriptedModel([
            AIMessage(content="", tool_calls=[{"name": "lookup", "args": {}, "id": "bad"}]),
            AIMessage(content="Verification unavailable."),
        ])
        agent = build_agent(model, SystemMessage(content="Use evidence."), [lookup])
        agent.invoke({"messages": [HumanMessage(content="Explain graphs")]})
        self.assertEqual(model.calls[1][-1].status, "error")

    def test_specialist_has_no_tools_and_no_shared_history(self):
        model = ScriptedModel([AIMessage(content="first"), AIMessage(content="second")])
        agent = build_agent(model, SystemMessage(content="Return Mermaid."))
        for prompt in ["first user", "second user"]:
            agent.invoke({"messages": [HumanMessage(content=prompt)]})
        self.assertEqual(len(model.calls[1]), 2)
        self.assertEqual(model.calls[1][-1].content, "second user")
        self.assertFalse(model.tools)

    def test_tool_loop_is_bounded(self):
        model = ScriptedModel([
            AIMessage(content="", tool_calls=[{"name": "lookup", "args": {"topic": "graphs"}, "id": str(i)}])
            for i in range(5)
        ])
        agent = build_agent(model, SystemMessage(content="Use evidence."), [lookup])
        with self.assertRaises(GraphRecursionError):
            agent.invoke({"messages": [HumanMessage(content="Loop")]}, {"recursion_limit": 3})


if __name__ == "__main__":
    unittest.main()
