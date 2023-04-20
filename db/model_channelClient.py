from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey

from db.base import Base

class ChannelClientTable(Base):
    __tablename__ = 'channel_client'
    __table_args__ = {"comment": "Таблица для хранения чатов и каналов клиента, куда инвайтить"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), nullable=False)
    ch_id_name = Column(String(100), nullable=False)
    name = Column(String(100))
    status_invite = Column(Integer, nullable=False)
    success_inv = Column(Integer, default=0)
    channel_url = Column(String(255), nullable=False)

class ChannelSource(Base):
    __tablename__ = 'channel_source'
    __table_args__ = {"comment": "Таблица для хранения чатов источников"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    id_channel = Column(Integer, ForeignKey("channel_client.id"), nullable=False)
    id_source = Column(BigInteger, ForeignKey("channels.id"),   nullable=False)