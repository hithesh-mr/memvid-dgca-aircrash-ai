#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv
import openai

from memvid import MemvidChat

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in environment")
openai.api_key = OPENAI_API_KEY

# Default memory files location
DATA_DIR = Path(__file__).parent.parent / "data" / "current"
VIDEO_FILE = DATA_DIR / "encoded_memory.mkv"
INDEX_JSON = DATA_DIR / "encoded_memory_index.json"

def search(query: str, provider: str = "openai", model: str = None) -> str:
    """Search the memory for the given query and return an answer."""
    if not VIDEO_FILE.exists():
        raise FileNotFoundError(f"Video file not found: {VIDEO_FILE}")
    if not INDEX_JSON.exists():
        raise FileNotFoundError(f"Index file not found: {INDEX_JSON}")

    chat = MemvidChat(
        video_file=str(VIDEO_FILE),
        index_file=str(INDEX_JSON),
        llm_provider=provider,
        llm_model=model
    )
    # Non-streaming mode for API
    response = chat.chat(query, stream=False)
    return response