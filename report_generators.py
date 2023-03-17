from aiogram import types
from datetime import datetime

from enums import CStatuses
from repositories.getRepo import get_report_repo, get_client_repo, get_proxy_repo, get_member_repo, \
    get_channel_client_repo, get_source_repo

c_repo = get_client_repo()
p_repo = get_proxy_repo()

#active_accs = await c_repo.get_by_status_id(CStatuses.AUTHORIZED.value['id'])

async def gen_report():
    r_repo = get_report_repo()
    m_repo = get_member_repo()
    s_repo = get_source_repo()
    id = await r_repo.get_last_id()
    rep = await r_repo.getReport(id)
    list_s = await s_repo.get_list_all_sourses()
    total_inv = 0
    for i in list_s:
        total_inv += len(await m_repo.get_all_by_id_source(i[1]))

    report = f'Отчёт №1\n' \
         f'Result {datetime.now().date()}\n' \
             f'\n' \
         f'System:\n' \
         f'Ban accounts: {rep["ban_acc"]}\n' \
         f'Ban proxy: {rep["ban_proxy"]}\n' \
         f'Ban groups: {rep["ban_groups"]}\n' \
         f'\n' \
         f'Data:\n' \
         f'TG: {await m_repo.get_all_with_username()} \n' \
         f'WA: ?  \n' \
         f'Tel: {await m_repo.get_all_with_phone()}  \n' \
         f'E-mail: ?   \n' \
         f'Overall: {len(await m_repo.get_all())} Contacts \n' \
         f'\n' \
         f'Funnel:\n' \
         f'New users: {rep["new_users"]}\n' \
         f'New orders: {rep["new_orders"]} \n' \
         f'TOT Invites: {total_inv} \n'
    return report

async def gen_plan():
    s_repo = get_source_repo()
    ch_repo = get_channel_client_repo()
    a_user = await ch_repo.get_unic_activ_user()
    a_groups = await s_repo.get_all_channel()
    plan = f'Отчёт №2\n' \
          f'Plan for {datetime.now().date()}\n' \
           f'\n' \
          f'System:\n' \
          f'Status system- Active/Non \n' \
          f'Active accounts - {len(await c_repo.get_by_status_id(CStatuses.AUTHORIZED.value["id"]))}\n' \
           f'Reserve accounts - {len(await c_repo.get_by_status_id(CStatuses.RESERVE.value["id"]))}\n' \
          f'Inactive accounts - {len(await c_repo.get_all()) - len(await c_repo.get_by_status_id(CStatuses.AUTHORIZED.value["id"])) - len(await c_repo.get_by_status_id(CStatuses.RESERVE.value["id"]))}\n' \
          f'Active proxy - {len(await p_repo.getAllActiveProxy())}\n' \
          f'\n' \
          f'Users:\n' \
          f'Active users - {len(a_user)}\n' \
          f'Active groups - {len(a_groups)}\n' \
          f'\n' \
          f'Invites:\n' \
          f'Plan Invites - 12 000 \n' \
          f'Status of plan: Good/Ok/Not real\n' \
          f'Comment: - / Need to add 44 "Proxy/Accounts"\n'
    return plan