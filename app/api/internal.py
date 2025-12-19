from fastapi import APIRouter, HTTPException, Header

from app.core.config import settings

router = APIRouter(prefix="/internal", tags=["internal"])

def verify_internal_token(authorization: str = Header(...)):
    try:
        scheme, token = authorization.split()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")

    if token != settings.INTERNAL_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")

    return True
