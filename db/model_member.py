"""Всякие сервисные модели для самого бота"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, String, Text)

from db.base import Base


class Member(Base):
    __tablename__ = 'members'
    __table_args__ = {"comment": "Спарсенные участники групп"}

    id = Column(String(20), primary_key=True)
    first_name = Column(String(500))
    last_name = Column(String(500))
    username = Column(String(500))
    invite_restricted = Column(Boolean, comment='Заблокирован ли у юзера приём инвайтов (1 - да)')
    source = Column(String(500), comment='Откуда участник', nullable=True)
    chat_id = Column(String(20))
    phone = Column(String(255), nullable=True)
    WA = Column(Boolean, nullable=True, comment='есть ли у юзера Whatsapp')
    client_id = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)


# class Chat(Base):
#     __tablename__ = 'chats'
#     __table_args__ = {"comment": "ID сервисных групп и каналов"}

#     id = Column(BigInteger, comment="id чата в TG")
#     name = Column(String(50), primary_key=True)
#     hyperlink = Column(String(255), comment="ссылка на чат")
