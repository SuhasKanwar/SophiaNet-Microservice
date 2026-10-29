from fastapi import APIRouter


router = APIRouter()


@router.get("/", tags=["Root"])
def root() -> dict:
    return {"status": 200, "message": "Welcome to SophiaNet. Visit /docs for API documentation."}


@router.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": 200, "message": "SophiaNet microservice is healthy and running."}
