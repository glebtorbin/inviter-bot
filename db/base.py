"""Основа для моделей"""
from databases import Database
from sqlalchemy.ext.declarative import declarative_base

from config import get_database_url

DATABASE_URL = get_database_url()

Base = declarative_base()
database = Database(DATABASE_URL)
