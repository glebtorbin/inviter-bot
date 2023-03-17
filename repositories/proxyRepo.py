import urllib.request as urllib

import sqlalchemy as sa

from db.model_client import Client
from db.model_proxy import ProxyTable

from .baseRepo import BaseRepo


class ProxyRepo(BaseRepo):
    async def testProxy(self, proxy: str):
        try:
            proxy_support = urllib.ProxyHandler({'http': proxy})
            opener = urllib.build_opener(proxy_support)
            urllib.install_opener(opener)
            try:
                urllib.urlopen("https://www.google.com/")
            except IOError:
                return False
            return True
        except Exception as e:
            print('Какая то другая ошибка\n', e)
            return False

    async def getIdProxy(self, proxy: str):
        query = sa.select(ProxyTable).where(ProxyTable.proxy == proxy)
        pList = await self.database.fetch_all(query)
        return pList[-1]

    async def getProxyById(self, id: int):
        query = sa.select(ProxyTable).where(ProxyTable.id == id)
        proxy = await self.database.fetch_one(query)
        return proxy[1]

    async def getProxyByPhone(self, phone: str):
        query = sa.select(Client).where(Client.phone == phone)
        proxyID = await self.database.fetch_one(query)
        query = sa.select(ProxyTable).where(ProxyTable.id == proxyID[3])
        proxy = await self.database.fetch_one(query)
        return proxy[1]

    async def getClientIdByPhone(self, phone: str):
        query = sa.select(Client).where(Client.phone == phone)
        idClient = await self.database.fetch_one(query)
        return idClient[0]

    async def addProxy(self, id: int, proxy: str):
        query = sa.insert(ProxyTable).values(proxy=proxy, valid=1)
        return await self.database.execute(query)

    async def updateClient(self, id: str, proxy: str):
        updateClient = sa.update(Client).where(Client.id == id).values(proxy_id=self.getIdProxy(proxy=proxy))
        await self.database.execute(updateClient)

    async def deleteProxy(self, idProxy: int):
        query = sa.delete(ProxyTable).where(ProxyTable.id == idProxy)
        return await self.database.execute(query)

    async def getIdProxyByIdClient(self, id: str):
        query = sa.select(Client).where(Client.id == id)
        idProxy = await self.database.fetch_one(query)
        return idProxy[3]

    async def getProxyByIdClient(self, id: str):
        query = sa.select(Client).where(Client.id == id)
        idProxy = await self.database.fetch_one(query)
        query = sa.select(ProxyTable).where(ProxyTable.id == idProxy[3])
        proxy = await self.database.fetch_one(query)
        return proxy[1]

    async def getStatusProxy(self, id: str):
        query = sa.select(Client).where(Client.id == id)
        idProxy = await self.database.fetch_one(query)
        return idProxy[4]

    async def getAllActiveProxy(self):
        query = sa.select(ProxyTable).where(ProxyTable.valid==1)
        res = await self.database.fetch_all(query)
        return res

    async def getAllAccWithProxy(self):
        query = sa.select(Client).where(Client.proxy_status_id == 1)
        res = await self.database.fetch_all(query)
        return res

    async def setONProxy(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(proxy_status_id=1)
        return await self.database.execute(query)

    async def setOFFProxy(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(proxy_status_id=2)
        return await self.database.execute(query)

    async def setERRORProxy(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(proxy_status_id=3)
        return await self.database.execute(query)

    async def setNONEProxy(self, id: str):
        query = sa.update(Client).where(Client.id == id).values(proxy_id=None, proxy_status_id=4)
        return await self.database.execute(query)

    async def setONProxy(self, id:str):
        query = sa.update(Client).where(Client.id == id).values(proxy_status_id=1)
        return await self.database.execute(query)
    async def setOFFProxy(self, id:str):
        query = sa.update(Client).where(Client.id == id).values(proxy_status_id=2)
        return await self.database.execute(query)
    async def setERRORProxy(self, id:str):
        query = sa.update(Client).where(Client.id == id).values(proxy_status_id=3)
        return await self.database.execute(query)
    async def setNONEProxy(self, id:str):
        query = sa.update(Client).where(Client.id == id).values(proxy_id = None,proxy_status_id=4)
        return await self.database.execute(query)