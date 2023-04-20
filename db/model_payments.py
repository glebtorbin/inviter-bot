from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
import datetime

from db.base import Base


class Payments(Base):
    __tablename__ = 'payments'
    __table_args__ = {"comment": "платежи"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String(20), ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)
    service = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())
