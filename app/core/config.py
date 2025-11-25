# app/core/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_JSON_PATH = Path(os.getenv("DATABASE_JSON_PATH", str(BASE_DIR / "data" / "db.json")))
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_to_a_random_secret_in_prod")
ALGORITHM = "HS256"
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
