from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.engine import Row

from db.model_member import Member

from .baseRepo import BaseRepo


class MemberRepo(BaseRepo):
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `chat_id`, `created_at` """

    async def get_all(self, skip: int = 0) -> List[Row]:
        query = sa.select(Member).offset(skip)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: str) -> Optional[Row]:
        query = sa.select(Member).where(Member.id == id)
        return await self.database.fetch_one(query)
    
    async def get_with_phone_WA(self):
        query = sa.select(Member).limit(3).filter(Member.phone != None, Member.WA == None)
        return await self.database.fetch_all(query)
    
    async def get_by_username(self, username: str) -> Optional[Row]:
        query = sa.select(Member).where(Member.username == username)
        return await self.database.fetch_one(query)

    async def create(self, id: str,
                     first_name: Optional[str],
                     last_name: Optional[str],
                     username: Optional[str],
                     phone: str,
                     chat_id: str,
                     client_id: str) -> int:
        """`return`  id: `int`"""
        user = await self.get_by_id(id)
        if not user:
            user = {
            'id': id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'phone': phone or '',
            'chat_id': chat_id,
            'client_id': client_id,
            'created_at': datetime.now(),
            }
        # if user['username'] == None:
        #     return -1
            query = sa.insert(Member).values(**user)
            return await self.database.execute(query)


    async def update(self, id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(Member).where(Member.id == id).values(**kwargs)
        return await self.database.execute(query)

    async def updateRestricted(self, id: str, val: int):
        query = sa.update(Member).where(Member.id == id).values(invite_restricted=val)
        return await self.database.execute(query)

    async def getRestricted(self, id:str):
        query = sa.select(Member).where(Member.id == id)
        res = await self.database.fetch_one(query)
        return res[4]

    async def get_all_by_user_id(self, user_id):
        query = sa.select(Member).where(Member.client_id == user_id)
        return await self.database.fetch_all(query)

    async def get_all_by_id_source(self, source_id):
        query = sa.select(Member).where(Member.chat_id == source_id, Member.invite_restricted == None)
        return await self.database.fetch_all(query)

    async def get_all_with_username(self):
        query = sa.select(Member).where(Member.username != None)
        res = await self.database.fetch_all(query)
        if res:
            return len(res)
        else:
            return 0
    async def get_all_with_phone(self):
        query = sa.select(Member).where(Member.phone != '')
        res = await self.database.fetch_all(query)
        if res:
            return len(res)
        else:
            return 0



# class Member(Base):
#     __tablename__ = 'members'
#     __table_args__ = {"comment": "Спарсенные участники групп"}

#     id = Column(BigInteger, primary_key=True)
#     first_name = Column(String(50))
#     last_name = Column(String(50))
#     username = Column(String(50))
#     invite_restricted = Column(Boolean, comment='Заблокирован ли у юзера приём инвайтов (1 - да)') TODO я не чекаю запрещено инвайтить или нет
#     chat_id = Column(BigInteger)
#     created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
