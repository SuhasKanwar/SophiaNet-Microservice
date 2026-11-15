"""Small deterministic tools for checking numerical claims and source metadata."""
import ast
import operator

import requests
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
    """Find up to three scholarly papers with DOI and publication metadata via Crossref."""
    if not query.strip() or len(query) > 500:
        raise ValueError("Supply a search query of 1–500 characters")
    response = requests.get("https://api.crossref.org/works", params={"query": query, "rows": 3}, timeout=15, headers={"User-Agent": "SophiaNet/1.0 (research assistant)"})
    response.raise_for_status()
    return "\n".join(f"{item.get('title', ['Untitled'])[0]} | {item.get('published', {}).get('date-parts', [])} | https://doi.org/{item['DOI']}" for item in response.json()["message"]["items"]) or "No papers found."
