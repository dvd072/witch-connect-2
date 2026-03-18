import os
import json

SHARED_FILE = "shared_data.json"

def load_shared_data():
    if os.path.exists(SHARED_FILE):
        with open(SHARED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"letters": [], "board_posts": []}

def save_shared_data(data):
    with open(SHARED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
