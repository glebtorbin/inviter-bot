from datetime import datetime

from .baseRepo import BaseRepo

import sqlalchemy as sa
from db.model_reports import ReportsTable
from db.model_plan import PlanTable

class ReportRepo(BaseRepo):
    async def createReport(self):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        date = rep['date']
        date = '10:00 '+date
        time_db = datetime.strptime(date, '%H:%M %Y-%m-%d')
        time_now = datetime.strptime(datetime.now().strftime('%H:%M %Y-%m-%d'), '%H:%M %Y-%m-%d')
        if not (time_now-time_db).total_seconds() > 86340:
            return
        report={
            'date':str(datetime.now().date()),
            'ban_acc':0,
            'ban_proxy':0,
            'ban_groups':0,
            'count_tg':0,
            'count_wa':0,
            'count_tel':0,
            'count_email':0,
            'new_users':0,
            'new_orders':0
        }
        query = sa.insert(ReportsTable).values(**report)
        return await self.database.execute(query)

    async def get_last_id(self):
        query = sa.select(ReportsTable)
        res = await self.database.fetch_all(query)
        return res[-1][0]

    async def getReport(self, id):
        query = sa.select(ReportsTable).where(ReportsTable.id == id)
        res = await self.database.fetch_one(query)
        report = {
            'date': res[1],
            'ban_acc': res[2],
            'ban_proxy': res[3],
            'ban_groups': res[4],
            'count_tg': res[5],
            'count_wa': res[6],
            'count_tel': res[7],
            'count_email': res[8],
            'new_users': res[9],
            'new_orders': res[10]
        }
        return report

    async def add_ban_acc(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['ban_acc']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(ban_acc=count + val)
        return await self.database.execute(query)

    async def add_ban_proxy(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['ban_proxy']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(ban_proxy=count + val)
        return await self.database.execute(query)

    async def add_ban_groups(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['ban_groups']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(ban_groups=count + val)
        return await self.database.execute(query)

    async def add_count_tg(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['count_tg']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(count_tg=count + val)
        return await self.database.execute(query)

    async def add_count_wa(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['count_wa']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(count_wa=count + val)
        return await self.database.execute(query)

    async def add_count_tel(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['count_tel']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(count_tel=count + val)
        return await self.database.execute(query)

    async def add_count_email(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['count_email']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(count_email=count + val)
        return await self.database.execute(query)

    async def add_new_users(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['new_users']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(new_users=count + val)
        return await self.database.execute(query)

    async def add_new_orders(self, val):
        id = await self.get_last_id()
        rep = await self.getReport(id)
        count = rep['new_orders']
        query = sa.update(ReportsTable).where(ReportsTable.id == id).values(new_orders=count + val)
        return await self.database.execute(query)


class PlanRepo(BaseRepo):
    async def createPlan(self, system_status,
                         active_acc, active_proxy, active_users,active_groups,
                         plan_inv, status_plan):
        plan = {
            'date': str(datetime.now().date()),
            'system_status': system_status,
            'active_acc': active_acc,
            'active_proxy': active_proxy,
            'active_users': active_users,
            'active_groups': active_groups,
            'plan_inv': plan_inv,
            'status_plan': status_plan,
        }
        query = sa.insert(PlanTable).values(**plan)
        return await self.database.execute(query)

    async def getPlan(self, date):
        query = sa.select(PlanTable).where(PlanTable.date == date)
        res = await self.database.fetch_one(query)
        plan = {
            'date': res[1],
            'system_status': res[2],
            'active_acc': res[3],
            'active_proxy': res[4],
            'active_users': res[5],
            'active_groups': res[6],
            'plan_inv': res[7],
            'status_plan': res[8]
        }
        return plan