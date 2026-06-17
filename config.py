import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

HOME_DIR = str(Path.home())

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

ICON_SIZE = 90
WINDOW_WIDTH = 650
WINDOW_HEIGHT = 350

ALLOWED_DIRECTORIES = [
    str(Path.home() / "Documents"),
    str(Path.home() / "Desktop"),
    str(Path.home() / "Downloads"),
    str(Path.home() / "Library" / "CloudStorage"),
]
