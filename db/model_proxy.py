from sqlalchemy import Column, Integer, String

from db.base import Base


class ProxyTable(Base):
    __tablename__ = 'proxy'
    __table_args__ = {"comment": "Все прокси"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy = Column(String(100), nullable=False)
    valid = Column(Integer, nullable=False)
