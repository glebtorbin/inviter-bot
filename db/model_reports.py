from sqlalchemy import Column, Integer, String, BigInteger

from db.base import Base


class ReportsTable(Base):
    __tablename__ = 'reports'
    __table_args__ = {"comment": "Отчеты по работе"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(String(50), nullable=False, unique=True)
    ban_acc = Column(Integer)
    ban_proxy = Column(Integer)
    ban_groups = Column(Integer)
    count_tg = Column(Integer)
    count_wa = Column(Integer)
    count_tel = Column(Integer)
    count_email = Column(Integer)
    new_users = Column(Integer)
    new_orders = Column(Integer)