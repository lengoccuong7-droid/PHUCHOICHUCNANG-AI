"""Đọc bộ dữ liệu tri thức JSON đi kèm ứng dụng, không cần API."""
import json
from pathlib import Path

KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "knowledge"

def load_knowledge(relative_path):
    path = (KNOWLEDGE_ROOT / relative_path).resolve()
    if KNOWLEDGE_ROOT.resolve() not in path.parents:
        raise ValueError("Đường dẫn dữ liệu tri thức không hợp lệ")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
