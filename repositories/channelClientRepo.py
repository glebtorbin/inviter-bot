import sqlalchemy as sa
from db.model_channelClient import ChannelClientTable
from db.model_channelClient import ChannelSource


from .baseRepo import BaseRepo


class ChannelClientRepo(BaseRepo):
    async def addChannel(self,user_id:str,
                         channel_id,
                         name, channel_url):
        query = sa.insert(ChannelClientTable).values(client_id=user_id, ch_id_name = channel_id,
                                                     name=name, channel_url=channel_url,
                                                     status_invite = 0)
        return await self.database.execute(query)

    async def get_url_by_client_id_and_ch_id(self, client_id, chat_or_channel):
        query = sa.select(ChannelClientTable.channel_url).where(ChannelClientTable.client_id == str(client_id),
                                                                ChannelClientTable.ch_id_name==str(chat_or_channel))
        res = await self.database.fetch_one(query)
        if res:
            return res[0]
        else:
            return None

    async def get_first_channel_id_by_user_id(self, user_id):
        query = sa.select(ChannelClientTable).where(ChannelClientTable.client_id == user_id)
        return await self.database.fetch_one(query)

    async def get_channel_invite(self, user_id):
        query = sa.select(ChannelClientTable).where(ChannelClientTable.client_id==user_id)
        res = await self.database.fetch_all(query)
        return [(ch[2], ch[3], ch[4]) for ch in res]

    async def get_group_by_id_and_userId(self, chat_id, user_id):
        query = sa.select(ChannelClientTable).where(ChannelClientTable.client_id == user_id, ChannelClientTable.ch_id_name==chat_id)
        res = await self.database.fetch_one(query)
        return res
    async def set_invite_ON_status(self, chat_id):
        query = sa.update(ChannelClientTable).where(ChannelClientTable.ch_id_name==chat_id).values(status_invite=1)
        return await self.database.execute(query)

    async def set_invite_OFF_status(self, chat_id):
        query = sa.update(ChannelClientTable).where(ChannelClientTable.ch_id_name==chat_id).values(status_invite=0)
        return await self.database.execute(query)

    async def add_one_success_inv(self, target_chat):
        q = sa.select(ChannelClientTable).where(ChannelClientTable.ch_id_name == target_chat)
        inv = await self.database.fetch_one(q)
        print(inv)
        try:
            query = sa.update(ChannelClientTable).where(ChannelClientTable.ch_id_name == target_chat).values(
                success_inv=int(inv[5]) + 1)
        except:
            query = sa.update(ChannelClientTable).where(ChannelClientTable.ch_id_name == target_chat).values(
                success_inv=0)
        return await self.database.execute(query)

    async def get_count_success_inv(self, target_chat):
        q = sa.select(ChannelClientTable).where(ChannelClientTable.ch_id_name == target_chat)
        inv = await self.database.fetch_one(q)
        return inv[5]

    async def get_count_client_channel(self, user_id):
        query = sa.select(ChannelClientTable).where(ChannelClientTable.client_id == user_id)
        res = await self.database.fetch_all(query)
        return len(res)

    async def get_unic_activ_user(self):
        query = sa.select(ChannelClientTable)
        res = await self.database.fetch_all(query)
        return set([i[1] for i in res])


class ChannelSourceRepo(BaseRepo):
    async def add_source_channel(self, id_channel, id_source):
        res = await self.get_source_by_channel_id(id_channel)
        if (str(id_channel), str(id_source)) in [(i[1],i[2]) for i in res]:
            return
        query = sa.insert(ChannelSource).values(id_channel=id_channel, id_source=id_source)
        return await self.database.execute(query)

    async def add_channel_id(self, channel_id):
        query = sa.insert(ChannelSource).values(id_channel=channel_id)
        return await self.database.execute(query)

    async def get_source_by_channel_id(self, channel_id):
        query = sa.select(ChannelSource).where(ChannelSource.id_channel==channel_id)
        return await self.database.fetch_all(query)

    async def get_source_id_by_channel_id(self, channel_id):
        query = sa.select(ChannelSource).where(ChannelSource.id_channel==channel_id)
        res = await self.database.fetch_all(query)
        return [i[2]for i in res]

    async def get_source_by_source_id(self, source_id):
        query = sa.select(ChannelSource).where(ChannelSource.id_source==source_id)
        return await self.database.fetch_all(query)

    async def update_source_by_channel_id(self, channel_id, source_id):
        query = sa.update(ChannelSource).where(ChannelSource.id_channel==channel_id).values(id_source=source_id)
        return await self.database.execute(query)

    async def update_source_by_source_id(self, source_id, channel_id):
        query = sa.update(ChannelSource).where(ChannelSource.id_source == source_id).values(id_channel=channel_id)
        return await self.database.execute(query)

    async def get_list_all_sourses(self):
        query = sa.select(ChannelSource)
        res = await self.database.fetch_all(query)
        return [(i[1], i[2]) for i in res]

    async def get_all_channel(self):
        query = sa.select(ChannelSource)
        res = await self.database.fetch_all(query)
        return [i[1] for i in res]

    async def clear_group_source(self, channel_id, source_id):
        query = sa.delete(ChannelSource).where(ChannelSource.id_channel==channel_id, ChannelSource.id_source == source_id)
        return await self.database.execute(query)