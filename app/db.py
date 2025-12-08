
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True, pool_timeout=1, connect_args={'connect_timeout': 1, "options": "-c statement_timeout=1500",}, )
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

class BaseORM(DeclarativeBase):
    pass
