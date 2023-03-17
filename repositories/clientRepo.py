from datetime import datetime
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.engine import Row
from db.model_client import Client
from .baseRepo import BaseRepo, LOGGER




class ClientRepo(BaseRepo):
    """ `Row` filds: `id`, `work_id`, `status_id`, `api_id`, `api_hash`, `phone`, `created_at`"""

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        try:
            query = sa.select(Client).limit(limit).offset(skip)
            return await self.database.fetch_all(query)
        except Exception as err:
            LOGGER.critical(err)
        

    async def get_by_id(self, id: str) -> Optional[Row]:
        query = sa.select(Client).where(Client.id == id)
        return await self.database.fetch_one(query)

    async def get_by_phone(self, phone: str) -> Optional[Row]:
        query = sa.select(Client).where(Client.phone == phone)
        return await self.database.fetch_one(query)

    async def get_by_work_id(self, work_id: int,
                             limit: int = 100,
                             skip: int = 0
                             ) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip).where(Client.work_id == work_id)
        return await self.database.fetch_all(query)

    async def get_by_status_id(self, status_id: int,
                               limit: int = 100,
                               skip: int = 0
                               ) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip).where(Client.status_id == status_id)
        return await self.database.fetch_all(query)

    async def get_by_user_id(self, user_id):
        query = sa.select(Client).where(Client.user_id == str(user_id))
        return await self.database.fetch_all(query)

    async def get_by_user_id_and_chat_id(self, user_id, chat_id):
        query = sa.select(Client).where(Client.proxy_status_id==1, Client.status_id==1, Client.user_id == str(user_id), Client.channel_id==chat_id)
        return await self.database.fetch_all(query)



    async def get_reserve(self, status_id: int = 5,
                               limit: int = 10, #TODO Лимит аккаунтов на 1го пользователя
                               skip: int = 0
                               ) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip).where(Client.status_id == status_id)
        return await self.database.fetch_all(query)
    async def get_next_reserve(self,status_id: int = 5):
        query = sa.select(Client).where(Client.status_id == status_id)
        return await self.database.fetch_one(query)

    async def get_by_status_and_work_id(self, status_id: int, work_id: int,
                               limit: int = 100,
                               skip: int = 0
                               ) -> List[Row]:
        query = sa.select(Client).limit(limit).offset(skip).where(Client.status_id == status_id, Client.work_id == work_id)
        return await self.database.fetch_all(query)

    async def get_status_id(self, id:str):
        query = sa.select(Client).where(Client.id == id)
        res = await self.database.fetch_one(query)
        return res[2]

    async def set_user_and_channel_id(self, phone, user_id, channel_id):
        query = sa.update(Client).where(Client.phone==phone).values(user_id=str(user_id), channel_id=str(channel_id), status_id=1)
        return await self.database.execute(query)

    async def get_all_channel(self, user_id, channel_id):
        query = sa.select(Client).where(Client.user_id==user_id, Client.channel_id==channel_id)
        res = await self.database.fetch_all(query)
        return [i[11] for i in res]

    async def get_id_by_api_id(self, api_id):
        query = sa.select(Client).where(Client.api_id == api_id)
        res = await self.database.fetch_one(query)
        return res[0]

# Нужно будет изменить, если добавим к каждому пользователю ограниченное ко-во аккаунтов
    async def check_valid_all_acc(self):
        list_status = [status[2] for status in await self.get_all()]
        if not 1 in list_status:
            raise Exception('Все аккаунты неактивны!')

    async def create(self, work_id: int,
                     status_id: int,
                     proxy_status_id: int,
                     api_id: int,
                     api_hash: str,
                     phone: str,
                     ) -> int:
        """`return`  id: `int`"""
        client_acc = {
            'work_id': work_id,
            'status_id': status_id,
            'proxy_status_id': proxy_status_id,
            'api_id': api_id,
            'api_hash': api_hash,
            'phone': phone,
            'count_invite': 0,
            'created_at': datetime.now(),
        }

        query = sa.insert(Client).values(**client_acc)
        return await self.database.execute(query)

    async def update(self, id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(Client).where(Client.id == id).values(**kwargs)
        return await self.database.execute(query)

    async def delete(self, id: str):
        query = sa.delete(Client).where(Client.id == id)
        return await self.database.execute(query)

    async def checkBan(self, id:str):
        query = sa.select(Client).where(Client.id == id)
        res = await self.database.fetch_one(query)
        if res[2] == 3:
            return True
        else:
            return False

    async def banned(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(status_id=3)
        return await self.database.execute(query)

    async def bannedByPhone(self, phone: str):
        query = sa.update(Client).where(Client.phone == phone).values(status_id=3)
        return await self.database.execute(query)

    async def bannedByApiId(self, api_id):
        query = sa.update(Client).where(Client.api_id == api_id).values(status_id=3)
        return await self.database.execute(query)

    async def get_count_invite(self, id: str):
        query = sa.select(Client).where(Client.id == id)
        res = await self.database.fetch_one(query)
        if res[8] == None:
            await self.set_count_invite(id, 0)
            return 0
        else:
            return res[8]

    async def set_count_invite(self, id: str, val: int):
        query = sa.update(Client).where(Client.id == id).values(count_invite=val)
        return await self.database.execute(query)

    async def plus_count_invite(self, id:str, val:int):
        count = await self.get_count_invite(id)
        query = sa.update(Client).where(Client.id == id).values(count_invite=count+1)
        return await self.database.execute(query)


    async def set_data_paused_invite(self, id:str):
        query = sa.update(Client).where(Client.id == id).values(data_paused=datetime.now())
        return await self.database.execute(query)

    async def get_data_paused_invite(self, id:str):
        query = sa.select(Client).where(Client.id == id)
        res = await self.database.fetch_one(query)
        return res[9]

    async def set_none_date_paused_invite(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(data_paused=None)
        return await self.database.execute(query)

    async def set_unPaused_invite(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(status_id=1)
        return await self.database.execute(query)

    async def check_end_pause(self, id:str):
        try:
            if (datetime.now() - datetime.strptime(str(await self.get_data_paused_invite(id)),
                                                   "%Y-%m-%d %H:%M:%S")).total_seconds() // 60 > 1439:
                await self.set_none_date_paused_invite(id)
                await self.set_count_invite(id, 0)
                await self.set_unPaused_invite(id)
                return True
            else:
                return False
        except:
            return False

    async def get_channel_id(self, id:int):
        query = sa.select(Client).where(Client.id == id)
        res = await self.database.fetch_one(query)
        if res[10]:
            return res[10]
        else:
            return None


# class Client(Base):
#     __tablename__ = 'client_accounts'
#     __table_args__ = {"comment": "Аккаунты парсеры"}

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     work_id = Column(Integer, ForeignKey('client_workes.id'),nullable=False, default=CWorkes.UNWORKING.value['id'])
#     status_id = Column(Integer, ForeignKey('client_statuses.id'),nullable=False, default=CStatuses.WAITING_AUTHORIZATION.value['id'])
#     api_id = Column(Integer, nullable=False)
#     api_hash = Column(String(50), nullable=False)
#     phone = Column(String(16), nullable=False)
#     created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
