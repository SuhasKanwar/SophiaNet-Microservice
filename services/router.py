class ModelRouter:
    def __init__(self, router_model):
        self.router_model = router_model

    def route_request(self, prompt: str) -> str:
        # Logic to route request based on prompt
        return "image" # or "image"