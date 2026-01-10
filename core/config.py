import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

@lru_cache
def load_env():
    current = Path(__file__).resolve()
    while current.name != "app":
        if current.parent == current:
            raise RuntimeError("Could not locate 'app' directory for .env")
        current = current.parent
    load_dotenv(current / ".env")

load_env()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")
