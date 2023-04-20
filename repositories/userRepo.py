from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.engine import Row

from db.model_users import User, UserBadWords
from db.model_nps import Nps
from db.model_payments import Payments
from .baseRepo import BaseRepo


class UserRepo(BaseRepo):
    """ `Row` filds: `id`, `first_name`, `last_name`, `username`, `role_id`, `created_at` """

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        query = sa.select(User).limit(limit).offset(skip)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: str) -> Optional[Row]:
        query = sa.select(User).where(User.id == id)
        return await self.database.fetch_one(query)

    async def get_by_username(self, username: str) -> Optional[Row]:
        query = sa.select(User).where(User.username == username)
        return await self.database.fetch_one(query)
    
    async def get_all_admins(self):
        query = sa.select(User).where(User.role_id == 10)
        return await self.database.fetch_all(query)

    async def create(self, id: str,
                     first_name: Optional[str],
                     last_name: Optional[str],
                     username: Optional[str],
                     role_id: int,
                     phone: str,
                     sphere: str,
                     job_title: str,
                     bot_usage: str,
                     where_from: str) -> int:
        """`return`  id: `int`"""
        user = {
            'id': id,
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'role_id': role_id,
            'phone': phone,
            'sphere': sphere,
            'job_title': job_title,
            'bot_usage': bot_usage,
            'where_from': where_from,
            'balance': 0,
            'created_at': datetime.now(),
        }

        query = sa.insert(User).values(**user)
        return await self.database.execute(query)
    
    async def get_triggers_by_id(self, user_id):
        query = sa.select(UserBadWords).where(UserBadWords.user_id == user_id)
        return await self.database.fetch_all(query)

    async def get_triggers_by_group_id(self, group_id):
        query = sa.select(UserBadWords).where(UserBadWords.group_id == group_id)
        return await self.database.fetch_one(query)

    async def create_triggers(self, group_id, user_id, triggers):
        trigger = {
            'group_id': group_id,
            'user_id': user_id,
            'words': triggers,
            'created_at': datetime.now()
        }
        query = sa.insert(UserBadWords).values(**trigger)
        return await self.database.execute(query)

    async def bw_update(self, group_id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(UserBadWords).where(UserBadWords.group_id == group_id).values(**kwargs)
        return await self.database.execute(query)

    async def update(self, id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(User).where(User.id == id).values(**kwargs)
        return await self.database.execute(query)
    
    async def create_nps(self, service, user_id, username, mark, comment):
        nps = {
            'user_id': user_id,
            'service': service,
            'username': username,
            'mark': mark,
            'comment': comment,
            'created_at': datetime.now()
        }
        query = sa.insert(Nps).values(**nps)
        return await self.database.execute(query)
# # class User(Base):
#     __tablename__ = 'users'
#     __table_args__ = {"comment": "Юзеры"}

#     id = Column(BigInteger, primary_key=True)
#     first_name = Column(String(50))
#     last_name = Column(String(50))
#     username = Column(String(50), nullable=False)
#     role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
#     # status_id = Column(Integer, ForeignKey('user_status.id'))
#     created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)

    async def new_payment(self, user_id, amount, ser):
        p = {
            'user': user_id,
            'service': ser,
            'amount': amount,
            'created_at': datetime.now()
        }
        query = sa.insert(Payments).values(**p)
        return await self.database.execute(query)

