import os
from pathlib import Path

DATA_DIR = Path(os.getenv("INVENTORY_APP_DATA", "~/.inventory_app")).expanduser()
QUEUE_FILE = DATA_DIR / "queue.jsonl"
MAX_BYTES = int(os.getenv("QUEUE_MAX_BYTES", 5 * 1024 * 1024))
