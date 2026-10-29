def text_response(result: dict) -> dict:
    return {
        "status": 200,
        "model": "nvidia",
        "response": result["text"],
        "performance_metrics": result["performance_metrics"],
    }
