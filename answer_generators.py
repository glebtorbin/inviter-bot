from typing import List

from aiogram import types
from sqlalchemy.engine import Row
from telethon.errors import UserDeactivatedBanError, SessionRevokedError, AuthKeyUnregisteredError

import client_api
from enums import CProxyStatuses, CStatuses, CWorkes, WA_CStatuses, WA_CWorkes, WA_Mailing_statuses
from keyboards import get_inline_chats_markup, get_inline_client_markup, get_inline_chats_profile, \
    get_inline_chats_profile_p_o_i, get_inline_wa_client_markup, get_inline_wa_mailing_markup
from repositories.getRepo import get_client_repo, get_proxy_repo, get_source_repo, get_channel_repo, get_user_repo


async def sendG_CAccounts(message: types.Message, CAccounts: List[Row], **kwargs) -> None:
    client_repo = get_client_repo()
    for acc in CAccounts:
        chek = await client_repo.check_end_pause(acc.id)
        #await client_repo.update(acc.id, status_id=CStatuses.AUTHORIZED.value['id'])
        work = CWorkes(acc.work_id).value
        status = CStatuses(acc.status_id).value
        status_message = f"{status['sticker']}Статус:  <i>{status['answer']}</i>\n\n"

        if acc.status_id != CStatuses.BANNED:
            if await client_repo.get_count_invite(acc.id) >= 30:
                await client_repo.update(acc.id, status_id=CStatuses.PAUSED.value['id'])
                if not chek:
                    status_message = f"{CStatuses.PAUSED.value['sticker']}Статус:" \
                                     f"  <i>{CStatuses.PAUSED.value['answer']}</i>\n\n"
                else:
                    await client_repo.update(acc.id, status_id=CStatuses.AUTHORIZED.value['id'])

        if acc.status_id == CStatuses.BANNED.value['id']:
            status_message = f"{CStatuses.BANNED.value['sticker']}Статус:" \
                             f"  <i>{CStatuses.BANNED.value['answer']}</i>\n\n"
            await client_repo.update(acc.id, status_id=CStatuses.BANNED.value['id'])

        if acc.status_id == CStatuses.AUTHORIZED.value['id']:
                try:
                    if not await client_api.client_is_authorized(acc):
                        status_message = f"{CStatuses.WAITING_AUTHORIZATION.value['sticker']}Статус:"\
                            f"  <i>{CStatuses.WAITING_AUTHORIZATION.value['answer']}</i>\n\n"

                        await client_repo.update(acc.id, status_id=CStatuses.WAITING_AUTHORIZATION.value['id'])
                    else:
                        if await client_repo.get_channel_id(acc.id) is None:
                            status_message = f"{CStatuses.RESERVE.value['sticker']}Статус:" \
                                             f"  <i>{CStatuses.RESERVE.value['answer']}</i>\n\n"
                            await client_repo.update(acc.id, status_id=CStatuses.RESERVE.value['id'])
                except (UserDeactivatedBanError,SessionRevokedError, AuthKeyUnregisteredError) as e:
                    status_message = f"{CStatuses.BANNED.value['sticker']}Статус:" \
                                     f"  <i>{CStatuses.BANNED.value['answer']}</i>\n\n"
                    await client_repo.update(acc.id, status_id=CStatuses.BANNED.value['id'])
                except Exception as e:
                    print(e)

        proxy_status_message = f"{CProxyStatuses.PROXY_NONE.value['sticker']}Proxy:" \
                               f"  <i>{CProxyStatuses.PROXY_NONE.value['answer']}</i>\n\n"
        try:
            if not await get_proxy_repo().testProxy(await get_proxy_repo().getProxyByIdClient(acc.id)):
                await get_proxy_repo().setERRORProxy(acc.id)
        except Exception as e:
            print("Пока нет прокси", e)

        if await get_proxy_repo().getStatusProxy(acc.id) == 1:
            proxy_status_message = f"{CProxyStatuses.PROXY_ON.value['sticker']}Proxy:"\
                f"  <i>{CProxyStatuses.PROXY_ON.value['answer']}</i>\n\n"
        elif await get_proxy_repo().getStatusProxy(acc.id) == 2:
            proxy_status_message = f"{CProxyStatuses.PROXY_OFF.value['sticker']}Proxy:" \
                                   f"  <i>{CProxyStatuses.PROXY_OFF.value['answer']}</i>\n\n"
        elif await get_proxy_repo().getStatusProxy(acc.id) == 3:
            proxy_status_message = f"{CProxyStatuses.PROXY_ERROR.value['sticker']}Proxy:" \
                                   f"  <i>{CProxyStatuses.PROXY_ERROR.value['answer']}</i>\n\n"

        await message.answer(
            f"Аккаунт #{acc.id}\n\n"
            f"api_id:  <i>{acc.api_id}</i>\n\n"
            f"api_hash:  <i>{acc.api_hash}</i>\n\n"
            f"телефон:  <i>{acc.phone}</i>\n\n"
            f"<i><b>{work['answer']}</b></i>\n\n"
            f"{status_message}"
            f"{proxy_status_message}", reply_markup=get_inline_client_markup(acc), parse_mode="html")

    if kwargs:
        await message.answer("Выберите действие", **kwargs)


async def send_WA_accs(message: types.Message, WA_accounts: List[Row], **kwargs) -> None:
    # wa_client_repo = get_wa_client_repo()
    for acc in WA_accounts:
        work = WA_CWorkes(acc.work_id).value
        status = WA_CStatuses(acc.status_id).value
        status_message = f"{status['sticker']}Статус:  <i>{status['answer']}</i>\n\n"
        await message.answer(
            f"Аккаунт #{acc.id}\n\n"
            f"id_instance:  <i>{acc.id_instance}</i>\n\n"
            f"api_token:  <i>{acc.api_token}</i>\n\n"
            f"Идентификатор:  <i>{acc.phone}</i>\n\n"
            f"<i><b>{work['answer']}</b></i>\n\n"
            f"{status_message}", reply_markup=get_inline_wa_client_markup(acc), parse_mode="html")

    if kwargs:
        await message.answer("Выберите действие", **kwargs)

async def send_WA_mailing(message: types.Message, WA_mailings: List[Row], **kwargs) -> None:
    user_repo = get_user_repo()
    for mai in WA_mailings:
        status = WA_Mailing_statuses(mai.status_id).value
        status_message = f"Статус:  <i>{status['answer']}</i>\n\n"
        creator = await user_repo.get_by_id(mai.creator)
        await message.answer(
            f"Рассылка #{mai.id}\n\n"
            f"Создатель: {creator.username}\n\n"
            f"Отправлено:  <i>{mai.send}</i>\n"
            f"Всего сообщений:  <i>{mai.for_sending}</i>\n"
            f"Текст: <i>{mai.text}</i>\n\n"
            f"{status_message}", reply_markup=get_inline_wa_mailing_markup(mai), parse_mode="html")

    if kwargs:
        await message.answer("Выберите действие", **kwargs)


async def sendG_chats(message: types.Message, client, chats, **kwargs) -> None:
    for chat in chats:
        try:
            await message.answer(
                f"Группа: <b>{chat.title}</b>\n\n"
                f"Количество участников: <i>{chat.participants_count}</i>\n\n"
                f"Права администратора: <i>{('Есть' if chat.admin_rights or chat.creator else 'Нет')}</i>\n\n", reply_markup=get_inline_chats_markup(client, chat), parse_mode="html")
        except Exception as e:
            print(f"Группа: <b>{chat.title}</b>\n\nОшибка: {e}")
            continue
    if kwargs:
        await message.answer("Выберите действие", **kwargs)

async def choice_chats_for_invite(mes:types.Message, user_id, chat_info):
    #chat_info = ['id_chat', name, status_invite]
    c_repo = get_source_repo()
    ch_repo = get_channel_repo()
    message = f"Группа: <b>{chat_info[1]}</b>\n\n" \
              f"Источники - <b>"
    ch = await c_repo.get_source_by_channel_id(chat_info[0])
    if ch:
        for i in ch:
            message +=f'\n{await ch_repo.get_name_by_id_or_username(i[2])}'
    else:
        message+='Нет'
    message += f"</b>\n \nСтатус инвайта - {'Вкл.' if chat_info[2] == 1 else 'Выкл.'}"

    await mes.answer(message, reply_markup=get_inline_chats_profile(user_id, chat_info[0]), parse_mode="html")

async def choice_chats_for_invite_p_o_i(mes:types.Message, user_id, chat_info):
    #chat_info = ['id_chat', name, status_invite]
    c_repo = get_source_repo()
    ch_repo = get_channel_repo()
    message = f"Группа: <b>{chat_info[1]}</b>\n\n" \
              f"Источники - <b>"
    ch = await c_repo.get_source_by_channel_id(chat_info[0])
    if ch:
        for i in ch:
            message +=f'\n{await ch_repo.get_name_by_id_or_username(i[2])}'
    else:
        message+='Нет'
    message += f"</b>\n \nСтатус инвайта - {'Вкл.' if chat_info[2] == 1 else 'Выкл.'}"

    await mes.answer(message, reply_markup=get_inline_chats_profile_p_o_i(user_id, chat_info[0]), parse_mode="html")



