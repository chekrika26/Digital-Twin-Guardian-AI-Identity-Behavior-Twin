"""SQLite engine/session setup. The DB file is created automatically on first run."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("GUARDIAN_DB_PATH", "data/guardian.db"))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def reset_db():
    Base.metadata.drop_all(engine)
    init_db()
