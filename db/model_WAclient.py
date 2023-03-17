"""Модели WA клиента (проверка номеров, рассылка)"""
import datetime

from sqlalchemy import (Column, DateTime, ForeignKey,
                        Integer, String)

from db.base import Base
from enums import WA_CWorkes, WA_CStatuses


class WA_Client(Base):
    __tablename__ = 'wa_client_accounts'
    __table_args__ = {"comment": "Аккаунты whatsapp"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('wa_client_workes.id'), nullable=False, default=WA_CWorkes.UNWORKING.value['id'])
    status_id = Column(Integer, ForeignKey('wa_client_statuses.id'), nullable=False, default=WA_CStatuses.WAITING_AUTHORIZATION.value['id'])
    id_instance = Column(String(100), nullable=False)
    api_token = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    count_check = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)


class WA_ClientWork(Base):
    __tablename__ = 'wa_client_workes'
    __table_args__ = {"comment": "Чем занят аккаунт WA"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class WA_ClientStatus(Base):
    __tablename__ = 'wa_client_statuses'
    __table_args__ = {"comment": "Статус аккаунта WA"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
