from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey

from db.base import Base


class SystemStatusTable(Base):
    __tablename__ = 'system_status'
    __table_args__ = {"comment": "Статус системы"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)


class StatusPlanTable(Base):
    __tablename__ = 'plan_status'
    __table_args__ = {"comment": "Статус плана"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)


class PlanTable(Base):
    __tablename__ = 'plans'
    __table_args__ = {"comment": "Отчеты по планам"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(String(50), nullable=False, unique=True)
    system_status = Column(Integer, ForeignKey('system_status.id'))
    active_acc = Column(Integer)
    active_proxy = Column(Integer)
    active_users = Column(Integer)
    active_groups = Column(Integer)
    plan_inv = Column(Integer)
    status_plan = Column(Integer, ForeignKey('plan_status.id'))
