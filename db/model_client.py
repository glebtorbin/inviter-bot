"""Модели клиента (парсер, инвайтер)"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String)

from db.base import Base
from enums import CProxyStatuses, CStatuses, CWorkes


class Client(Base):
    __tablename__ = 'client_accounts'
    __table_args__ = {"comment": "Аккаунты парсеры"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_id = Column(Integer, ForeignKey('client_workes.id'), nullable=False, default=CWorkes.UNWORKING.value['id'])
    status_id = Column(Integer, ForeignKey('client_statuses.id'), nullable=False, default=CStatuses.WAITING_AUTHORIZATION.value['id'])
    proxy_id = Column(Integer, ForeignKey('proxy.id'))
    proxy_status_id = Column(Integer, ForeignKey('client_proxy_statuses.id'), nullable=False, default=CProxyStatuses.PROXY_NONE.value['id'])
    api_id = Column(Integer, nullable=False)
    api_hash = Column(String(50), nullable=False)
    phone = Column(String(16), nullable=False)
    count_invite = Column(Integer, default=0)
    data_paused = Column(DateTime, default=None)
    user_id = Column(String(50), ForeignKey('users.id'))
    channel_id = Column(BigInteger, ForeignKey('channels.id'), default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)


class ClientWork(Base):
    __tablename__ = 'client_workes'
    __table_args__ = {"comment": "Чем занят аккаунт"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class ClientStatus(Base):
    __tablename__ = 'client_statuses'
    __table_args__ = {"comment": "Статус аккаунта"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class ClientProxyStatus(Base):
    __tablename__ = 'client_proxy_statuses'
    __table_args__ = {"comment": "Статус прокси на аккаунте"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
