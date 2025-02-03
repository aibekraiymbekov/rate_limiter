from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
from typing import Tuple
from rate_limiter import Provider

def get_provider_from_request(request: Request) -> Provider:
    provider_str = (
            request.headers.get("X-Provider") or
            request.query_params.get("provider")
    )

    if not provider_str:
        raise HTTPException(
            status_code=400,
            detail="Provider is required"
        )

    try:
        return Provider(provider_str.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider"
        )

async def get_token_and_provider(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Tuple[str, Provider]:
    provider = get_provider_from_request(request)
    return credentials.credentials, provider