from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from typing import Tuple

from rate_limiter import Provider, RateLimiterRegistry
from utils import get_provider_from_request, get_token_and_provider

app = FastAPI(title="Rate Limiter API")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limiter_registry = RateLimiterRegistry()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware для проверки rate limit"""
    if request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
        return await call_next(request)

    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header is missing"
            )

        token_type, token = auth_header.split()
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization type. Must be Bearer"
            )

        provider = get_provider_from_request(request)

        limiter = rate_limiter_registry.get_limiter(provider)
        is_limited, headers = limiter.check_rate_limit(token, increment=True)

        if is_limited:
            raise HTTPException(
                status_code=429,
                detail=f"Too Many Requests for provider {provider}",
                headers=headers
            )

        response = await call_next(request)

        for key, value in headers.items():
            response.headers[key] = value

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.get("/")
async def root(
        token_provider: Tuple[str, Provider] = Depends(get_token_and_provider)
):
    token, provider = token_provider
    return {
        "message": "Hello World",
        "token": token,
        "provider": provider
    }

@app.get("/rate-limit-status")
async def check_rate_limit(
        token_provider: Tuple[str, Provider] = Depends(get_token_and_provider)
):
    token, provider = token_provider
    limiter = rate_limiter_registry.get_limiter(provider)
    _, headers = limiter.check_rate_limit(token, increment=False)
    return {
        "provider": provider,
        "limit": headers["X-RateLimit-Limit"],
        "remaining": headers["X-RateLimit-Remaining"],
        "reset": headers["X-RateLimit-Reset"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)