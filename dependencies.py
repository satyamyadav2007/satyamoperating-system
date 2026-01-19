# dependencies.py
import sqlite3
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    # Note: In a production app, use a connection pool instead of opening/closing every time
    conn = sqlite3.connect("agent_os.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, plan FROM api_keys WHERE key = ?", (api_key,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key. Get one at dashboard.agentos.com"
        )
    return user