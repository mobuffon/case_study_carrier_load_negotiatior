from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    provided: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if not provided or provided != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
