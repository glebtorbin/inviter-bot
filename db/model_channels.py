import datetime


from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String, Table, Text)
from sqlalchemy.orm import relationship

from db.base import Base




class Channel(Base):
    __tablename__ = "channels"
    id = Column(BigInteger, primary_key=True)
    title = Column(String(400), nullable=True, comment="название")
    access_hash = Column(String(255), nullable=True, comment="access_hash")
    username = Column(String(255), nullable=True, comment="username")
    participants_count = Column(Integer, nullable=True, comment="кол-во участников")
    audience = Column(String(255), nullable=True, comment="аудитория")
    keyword_id = Column(Integer, ForeignKey('keyword.id'), nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=datetime.datetime.now,
        comment="время создания канала в бд"
    )

class Keyword(Base):
    __tablename__ = "keyword"
    id = Column(Integer, primary_key=True)
    tag = Column(String(255), nullable=False, unique=True, comment="тег")


class Search(Base):
    __tablename__ = "search"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(20), ForeignKey('users.id'), nullable=False)
    keywords = Column(Text)
    created_at = Column(
        DateTime, nullable=False, default=datetime.datetime.now
    )


class SearchChats(Base):
    __tablename__ = 'search_chats'

    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey('search.id'), nullable=False)
    channel_id = Column(BigInteger, ForeignKey('channels.id'), nullable=False)

