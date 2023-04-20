import datetime
from typing import List, Optional
from sqlalchemy import desc
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.engine import Row

from db.model_channels import Channel, Keyword, Search, SearchChats
from .baseRepo import BaseRepo


class ChannelRepo(BaseRepo):
    
    async def get_keyword_by_id(self, id: int):
        query = sa.select(Keyword).where(Keyword.id == id)
        return await self.database.fetch_one(query)


    async def add_new_keyword(self, tag: str):
        stmt = select(Keyword).where(Keyword.tag == tag)
        keyw = await self.database.fetch_one(stmt)
        if not keyw:
            keyword = {
                'tag': tag
            }
            query = sa.insert(Keyword).values(**keyword)
            return await self.database.execute(query)


    async def get_user_searches(self, user_id):
        result = {}
        searches = await self.database.fetch_all(
            sa.select(Search).where(Search.user_id == user_id)
        )
        unames = []
        for search in searches:
            channels = await self.database.fetch_all(
                sa.select(SearchChats).where(SearchChats.search_id == search.id)
            )
            for ch in channels:
                x = (await self.database.fetch_one(sa.select(Channel).where(Channel.id == ch.channel_id))).username
                unames.append(f'@{x}')
                result[search.keywords] = unames
            unames=[]
        return result

   

    async def add_new_search(self, user_id, keyw, groups):
            search = {
                'user_id': user_id,
                'keywords': keyw,
                'created_at': datetime.datetime.now()
            }
            query = sa.insert(Search).values(**search)
            search = await self.database.execute(query)
            ch = sa.select(Channel).where(Channel.id.in_(groups))
            channels = await self.database.fetch_all(ch)
            for c in channels:
                ch_search = {
                    'search_id': search,
                    'channel_id': c.id
                }
                query = sa.insert(SearchChats).values(**ch_search)
                await self.database.execute(query)



    async def add_new_channel(self, ch_id: int, title: str, access_hash: int, username: str, participants: int, keyword: str, aud: str):

        stmt = select(Keyword).where(Keyword.tag == keyword)
        key = await self.database.fetch_one(stmt)
        ch = await self.database.fetch_one(sa.select(Channel).where(Channel.id==ch_id))

        # if ch and aud =='ru' and ch.audience == 'en':
        #     query = sa.update(ch).values(
        #     title = title,
        #     access_hash = access_hash,
        #     username = username,
        #     participants_count = participants,
        #     audience = aud,
        #     )
        #     if await self.database.fetch_one(select(key_ch_association_tb).where(
        #         keyw_id==key.id
        #         'ch_id': ch_id
        #     ))

        # elif ch and ch.audience == aud:
        #     query = sa.update(ch).values(
        #     title = title,
        #     access_hash = access_hash,
        #     username = username,
        #     participants_count = participants,
        #     audience = aud,
        #     )
        #     if key not in ch.keywords:
        #         ch.keywords.append(key)

        if not ch:
            ch = {
                'id': ch_id,
                'title': title,
                'access_hash': access_hash,
                'username': username,
                'participants_count': participants,
                'keyword_id': key.id,
                'audience': aud,
                'created_at': datetime.datetime.now()
            }
            query = sa.insert(Channel).values(**ch)
            await self.database.execute(query)

    async def add_new_channel_by_pars(self, ch_id: int, title: str, access_hash: int, username: str, participants: int):
        q = sa.select(Channel).where(Channel.id==ch_id)
        res = await self.database.fetch_one(q)
        if not res:
            ch = {
                'id': ch_id,
                'title': title,
                'access_hash': access_hash,
                'username': username,
                'participants_count': participants,
                'keyword_id': -1,
                'created_at': datetime.datetime.now()
            }
            query = sa.insert(Channel).values(**ch)
            return await self.database.execute(query)
        else:
            return res

    async def get_name_by_id_or_username(self, id_channel):
        if isinstance(id_channel, int):
            query = sa.select(Channel).where(Channel.id==id_channel)
            res = await self.database.fetch_one(query)
        else:
            query = sa.select(Channel).where(Channel.username == id_channel)
            res = await self.database.fetch_one(query)
        if res:
            return res[1]
        else:
            return None

    async def get_username_by_id(self, id_channel):
        if isinstance(id_channel, int):
            query = sa.select(Channel).where(Channel.id == id_channel)
            res = await self.database.fetch_one(query)
        else:
            res = None
        if res:
            return res[3]
        else:
            return None

    async def get_participants_count_by_id(self, id_channel):
        if isinstance(id_channel, int):
            query = sa.select(Channel).where(Channel.id == id_channel)
            res = await self.database.fetch_one(query)
        else:
            query = sa.select(Channel).where(Channel.username == id_channel)
            res = await self.database.fetch_one(query)
        if res:
            return res[4]
        else:
            return None



    async def get_channels_by_username(self, user_id, unames):
        searches = await self.database.fetch_all(
            sa.select(Search).where(Search.user_id == user_id)
        )
        ids = []
        for search in searches:
            channels = await self.database.fetch_all(
                sa.select(SearchChats).where(SearchChats.search_id == search.id)
            )
            for ch in channels:
                ids.append(ch.channel_id)
        ch = sa.select(Channel).order_by(
            desc(Channel.participants_count)
        ).limit(30).where(
            Channel.username.in_(unames)
        ).filter((Channel.id.notin_(ids)))
        return await self.database.fetch_all(ch)

    async def get_id_by_username(self, username):
        query = sa.select(Channel).where(Channel.username == username)
        res = await self.database.fetch_one(query)
        if res:
            return res[0]
        else:
            return None


