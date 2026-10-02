import os
from pathlib import Path

from dotenv import load_dotenv


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")


class Settings:
    BASE_DIR = BASE_DIR
    PANEL_COUNT = int(os.getenv("PANEL_COUNT","4"))
    APP_NAME = os.getenv("APP_NAME", "ComicCraft")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    GEMINI_FLASH_MODEL = os.getenv(
        "GEMINI_FLASH_MODEL",
        "gemini-2.5-flash-lite"
    )

    GEMINI_PRO_MODEL = os.getenv(
        "GEMINI_PRO_MODEL",
        "gemini-3.1-flash-lite"
    )

    # Hugging Face
    HF_TOKEN = os.getenv("HF_TOKEN", "")

    # Directories
    TEMPLATE_DIR=BASE_DIR/ "templates"
    STATIC_DIR = BASE_DIR / "static"
    PANEL_DIR = STATIC_DIR / "panels"
    EXPORT_DIR = STATIC_DIR / "exports"

    def create_directories(self):
        self.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
        self.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        self.PANEL_DIR.mkdir(parents=True, exist_ok=True)
        self.EXPORT_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
