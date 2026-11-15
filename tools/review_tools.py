"""Small deterministic tools for checking numerical claims and source metadata."""
import ast
import operator

from langchain_core.tools import tool


@tool
def calculate(expression: str) -> str:
    """Check arithmetic using +, -, *, / and parentheses; no code execution."""
    if len(expression) > 200:
        raise ValueError("Expression exceeds 200 characters")
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float) and abs(node.value) <= 1e15:
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return -evaluate(node.operand) if isinstance(node.op, ast.USub) else evaluate(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            value = operations[type(node.op)](evaluate(node.left), evaluate(node.right))
            if abs(value) <= 1e15:
                return value
        raise ValueError("Only bounded arithmetic is supported")

    return str(evaluate(ast.parse(expression, mode="eval").body))


@tool
def search_papers(query: str) -> str:
    """Find relevant scholarly papers from Crossref and arXiv, with source links."""
    from services.papers import search_papers as search
    if not 2 <= len(query.strip()) <= 500:
        raise ValueError("Supply a search query of 2–500 characters")
    result = search(query.strip(), limit=3)
    lines = [f"{paper['title']} | {paper['year']} | {paper['url']}" for paper in result['papers']]
    return "\n".join([*lines, *result['warnings']]) or "No papers found."
