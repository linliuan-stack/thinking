import os

DB_HOST = os.getenv("DB_HOST", "111.231.145.50")
DB_PORT = os.getenv("DB_PORT", "2345")
DB_NAME = os.getenv("DB_NAME", "thinking")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tech-coffee")

SECRET_KEY = os.getenv("SECRET_KEY", "thinking-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
