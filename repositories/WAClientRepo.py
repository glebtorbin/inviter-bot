from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.engine import Row

from db.model_WAclient import WA_Client
from db.model_channelClient import ChannelClientTable
from db.model_WAmailing import WA_Mailing, MailingPhones

from enums import WA_CWorkes, WA_CStatuses
from telethon.errors import UserDeactivatedBanError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

from .baseRepo import BaseRepo, LOGGER


#from .getRepo import get_channel_client_repo


class WaClientRepo(BaseRepo):
    """ `Row` filds: `id`, `work_id`, `status_id`, `api_id`, `api_hash`, `phone`, `created_at`"""

    async def get_all(self, limit: int = 100, skip: int = 0) -> List[Row]:
        try:
            query = sa.select(WA_Client).limit(limit).offset(skip)
            return await self.database.fetch_all(query)
        except Exception as err:
            await self.database.disconnect()
            await self.database.connect()
            LOGGER.critical(err)
    
    async def get_5(self, limit: int = 5, skip: int = 0) -> List[Row]:
        query = sa.select(WA_Client).limit(limit).offset(skip).where(WA_Client.status_id==1, WA_Client.work_id==1)
        return await self.database.fetch_all(query)

    async def get_by_id(self, id: str) -> Optional[Row]:
        query = sa.select(WA_Client).where(WA_Client.id == id)
        return await self.database.fetch_one(query)


    async def get_by_phone(self, phone: str) -> Optional[Row]:
        query = sa.select(WA_Client).where(WA_Client.phone == phone)
        return await self.database.fetch_one(query)


    async def create(self, work_id: int,
                     status_id: int,
                     instance: int,
                     token: str,
                     phone: str,
                     ) -> int:
        """`return`  id: `int`"""
        client_acc = {
            'work_id': work_id,
            'status_id': status_id,
            'id_instance': instance,
            'api_token': token,
            'phone': phone,
            'count_check': 0,
            'created_at': datetime.now(),
        }

        query = sa.insert(WA_Client).values(**client_acc)
        return await self.database.execute(query)

    async def update(self, id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(WA_Client).where(WA_Client.id == id).values(**kwargs)
        return await self.database.execute(query)

    async def delete(self, id: str):
        query = sa.delete(WA_Client).where(WA_Client.id == id)
        return await self.database.execute(query)
    
    async def create_mailing(self, creator, status_id, for_sending, text, phones):
        mailing = {
            'creator': creator,
            'status_id': status_id,
            'send': 0,
            'text': text,
            'for_sending': for_sending,
            'created_at': datetime.now(),
        }

        query = sa.insert(WA_Mailing).values(**mailing)
        new_mailing = await self.database.execute(query)

        for ph in phones:
            mailing_ph = {
                'mailing_id': new_mailing,
                'phone': ph, 
                'is_send': False
            }
            await self.database.execute(sa.insert(MailingPhones).values(**mailing_ph))
    
    async def update_mailing_contacts(self, id, for_send, phones):
        query = sa.select(WA_Mailing).where(WA_Mailing.id == id)
        mailing = await self.database.fetch_one(query)
        m_for_sending = mailing.for_sending
        query = sa.update(WA_Mailing).where(WA_Mailing.id == id).values(for_sending=m_for_sending+for_send)
        await self.database.execute(query)
        for ph in phones:
            mailing_ph = {
                'mailing_id': id,
                'phone': ph, 
                'is_send': False
            }
            await self.database.execute(sa.insert(MailingPhones).values(**mailing_ph))
    

    async def get_all_mailing(self, limit: int = 100) -> List[Row]:
        query = sa.select(WA_Mailing).limit(limit)
        return await self.database.fetch_all(query)
    
    async def get_mailing_by_id(self, id):
        query = sa.select(WA_Mailing).where(WA_Mailing.id == id)
        return await self.database.fetch_one(query)


    async def mailing_delete(self, id):
        query = sa.delete(WA_Mailing).where(WA_Mailing.id == id)
        return await self.database.execute(query)

    async def mailing_update(self, id: str, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(WA_Mailing).where(WA_Mailing.id == id).values(**kwargs)
        return await self.database.execute(query)

    async def mailing_send_update(self, id: str, c_send) -> int:
        """`return`  id: `int`"""
        query = sa.select(WA_Mailing).where(WA_Mailing.id == id)
        mailing = await self.database.fetch_one(query)
        mailing_send = mailing.send
        query = sa.update(WA_Mailing).where(WA_Mailing.id == id).values(send=mailing_send+c_send)
        return await self.database.execute(query)
    
    async def get_mailing_phones(self, mailing_id):
        query = sa.select(MailingPhones).where(MailingPhones.mailing_id==mailing_id, MailingPhones.is_send==False)
        return await self.database.fetch_all(query)
    
    async def mailing_phones_update(self, mailing_id, phone, **kwargs) -> int:
        """`return`  id: `int`"""
        query = sa.update(MailingPhones).where(MailingPhones.mailing_id == mailing_id, MailingPhones.phone == phone).values(**kwargs)
        return await self.database.execute(query)
    
    async def mailing_phones_delete(self, mailing_id) -> int:
        """`return`  id: `int`"""
        query = sa.delete(MailingPhones).where(MailingPhones.mailing_id == mailing_id)
        return await self.database.execute(query)