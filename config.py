import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Reads data from the .env file to be used in this project"""
    db_url:             str     = os.getenv("DB_URL")
    raw_file_path:      str     = os.getenv("RAW_FILE_PATH")
    target_table:       str     = os.getenv("TARGET_TABLE")
    target_schema:      str     = os.getenv("TARGET_SCHEMA")
    chunk_size:         int     = int(os.getenv("CHUNK_SIZE"))
    max_rejection_rate: float   = float(os.getenv("MAX_REJECTION_RATE"))