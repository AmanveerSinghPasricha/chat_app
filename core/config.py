import os
from dotenv import load_dotenv

# Load .env ONLY if it exists (local dev)
load_dotenv(override=False)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
)

DATABASE_URL = os.getenv("DATABASE_URL")

DB_ENABLED = os.getenv("DB_ENABLED", "true").lower() == "true"


# Fail fast ONLY for things that must exist everywhere
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")
