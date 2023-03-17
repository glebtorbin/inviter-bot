"""Модели WA рассылки (проверка номеров, рассылка)"""
import datetime

from sqlalchemy import (Column, DateTime, ForeignKey,
                        Integer, String, Boolean, Text)

from db.base import Base
from enums import WA_Mailing_statuses


class WA_Mailing(Base):
    __tablename__ = 'wa_mailing'
    __table_args__ = {"comment": "рассылки whatsapp"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator = Column(String(20), ForeignKey('users.id'), nullable=False)
    status_id = Column(
        Integer, ForeignKey('wa_mailing_statuses.id'),
        default=WA_Mailing_statuses.UNWORKING.value['id'], nullable=False
    )
    text = Column(Text)
    send = Column(Integer, nullable=False, comment='сколько сообщений отправлено')
    for_sending = Column(Integer, nullable=False, comment='сколько надо отправить')
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)


class WA_Mailing_status(Base):
    __tablename__ = 'wa_mailing_statuses'
    __table_args__ = {"comment": "статус wa рассылки"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class MailingPhones(Base):
    __tablename__ = 'wa_mailing_phones'
    __table_args__ = {"comment": "номера для рассылок"}

    id = Column(Integer, primary_key=True)
    mailing_id = Column(Integer, ForeignKey('wa_mailing.id'), nullable=False)
    phone = Column(String(50), nullable=False)
    is_send = Column(Boolean, nullable=False)



