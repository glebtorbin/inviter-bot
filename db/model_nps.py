import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, String, Text, Integer)

from db.base import Base


class Nps(Base):
    __tablename__ = 'nps'
    __table_args__ = {"comment": "nps клиентов"}

    id = Column(Integer, primary_key=True)
    service = Column(String(100), nullable=False)
    user_id = Column(String(20), ForeignKey('users.id'), nullable=False)
    username = Column(String(500), nullable=True)
    mark = Column(String(5), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)

