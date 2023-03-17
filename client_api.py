import re
import random
import asyncio
from googletrans import Translator
import logging
import logging.handlers as loghandlers
import xlsxwriter
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsBots
from contextvars import ContextVar
from datetime import datetime
from typing import Any, List
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPhoneContact, PeerChannel
from telethon.tl.functions.contacts import ImportContactsRequest
from transliterate import translit
import python_socks
from telethon import utils
from aiogram import types
from telethon.tl.types import ChannelParticipantsSearch
from telethon.errors.rpcerrorlist import (PeerFloodError,
                                          UserAlreadyParticipantError,
                                          UserPrivacyRestrictedError,
                                          UserDeactivatedBanError,
                                          PhoneNumberBannedError,
                                          SessionRevokedError,
                                          ChatAdminRequiredError, AuthKeyUnregisteredError)
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantsRequest, JoinChannelRequest, \
    LeaveChannelRequest
from telethon.tl.functions.messages import (AddChatUserRequest,
                                            GetDialogsRequest, ImportChatInviteRequest, CheckChatInviteRequest)
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import InputPeerChat, InputPeerEmpty, InputPeerChannel, ChannelParticipantsSearch
from telethon.tl.types import PeerUser, PeerChat, PeerChannel

from keyboards import get_inline_invite_stop_markup, error_add_channel
from repositories.getRepo import get_proxy_repo, get_client_repo, get_member_repo, get_channel_repo, get_report_repo, \
    get_channel_client_repo, get_source_repo

# logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.DEBUG)

LOGGER = logging.getLogger('tg_client_log')
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s  %(filename)s  %(funcName)s  %(lineno)d  %(name)s  %(levelname)s: %(message)s')
log_handler = loghandlers.RotatingFileHandler(
    './logs/tg_api_logs.log',
    maxBytes=1000000,
    encoding='utf-8',
    backupCount=50
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(formatter)
LOGGER.addHandler(log_handler)

clients_context = ContextVar('clients', default=dict())
stop_invite = False
stop_invite_prof = False


async def get_client(client_data) -> TelegramClient:
    try:
        clients = clients_context.get()
        phone = client_data.phone
        if phone in clients:
            if 'client' in clients[phone]:
                return clients[phone]['client']
        else:
            client = await connect(client_data)
            _add_client_to_context(phone, client)
            return client
    except Exception as err:
        LOGGER.error(err)


async def client_is_authorized(client_data) -> bool:
    client = await get_client(client_data)
    b = await client.is_user_authorized()
    await client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=1,
        hash=0
    ))
    return b

async def check_ban_accs(accounts):
    active_acc = []
    for client_data in accounts:
        try:
            client = await get_client(client_data)
            b = await client.is_user_authorized()
            await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=1,
                hash=0
            ))
            active_acc.append(client_data)
        except (UserDeactivatedBanError, AuthKeyUnregisteredError, SessionRevokedError) as e:
            c_repo = get_client_repo()
            LOGGER.error(e, f"{client_data[7]}")
            await c_repo.banned(client_data[0])
            user_id = client_data[9]
            chat_id = client_data[10]
            res = await c_repo.get_next_reserve()
            await c_repo.update(res[0], status_id=1, user_id=user_id, channel_id=chat_id)
            await c_repo.update(client_data[0], status_id=3, user_id=None, channel_id=None)
            r_repo = get_report_repo()
            await r_repo.add_ban_acc(1)
            continue
        except Exception as e:
            LOGGER.error(e)
            continue
    if active_acc:
        return active_acc
    else:
        return None


def _get_client_context(phone, key) -> Any:
    try:
        clients = clients_context.get()
        if phone in clients:
            return clients[phone][key]
    except Exception as err:
        LOGGER.error(err)


def _update_client_context(phone, key, value) -> None:
    try:
        clients = clients_context.get()
        if phone in clients:
            clients[phone].update({key: value})
        clients_context.set(clients)
    except Exception as err:
        LOGGER.error(err)


def _add_client_to_context(phone, client) -> None:
    try:
        clients = clients_context.get()
        if phone in clients:
            clients[phone].update({'client': client})
        else:
            clients[phone] = {'client': client}
        clients_context.set(clients)
    except Exception as err:
        LOGGER.error(err)


def _delete_client_from_context(phone) -> None:
    try:
        clients = clients_context.get()
        del clients[phone]
        clients_context.set(clients)
    except Exception as err:
        LOGGER.error(err)


async def get_user_group_id(client_data, group, hash):
    client = await get_client(client_data)
    try:
        chat = await client.get_entity(group)
    except Exception as err:
        LOGGER.debug(err)
        await client(ImportChatInviteRequest(hash))
        chat = await client.get_entity(group)
    group_id = utils.get_peer_id(PeerChannel(chat.id))
    return group_id


async def send_tg_code(client_data, phone):
    try:
        client = await get_client(client_data)
        contact = InputPhoneContact(client_id=0, phone=phone, first_name=f"{phone}", last_name="inv")
        result = await client(ImportContactsRequest([contact]))
        contact_info = await client.get_entity(phone)
        LOGGER.info(contact_info.username)
        code = random.randint(1000, 9999)
        await client.send_message(contact_info.id, f'Ваш код для авторизации: {code}')
        return str(code)
    except Exception as err:
        LOGGER.error(err)


async def send_phone_hash_code(client_data):
    client = await get_client(client_data)
    try:
        sent = await client.send_code_request(client_data.phone)
        _update_client_context(client_data.phone, 'phone_code_hash', sent.phone_code_hash)
    except PhoneNumberBannedError as e:
        c = get_client_repo()
        LOGGER.debug(e, f"{client}")
        await c.bannedByPhone(client_data.phone)
        return -1


async def authorize(client_data, code) -> None:
    try:
        print(client_data)
        phone = client_data.phone
        client = await get_client(client_data)
        phone_code_hash = _get_client_context(phone, 'phone_code_hash')
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except Exception as err:
        LOGGER.error(err)


async def connect(client_data) -> TelegramClient:
    #typesProxy = [python_socks.ProxyType.HTTP, python_socks.ProxyType.SOCKS4, python_socks.ProxyType.SOCKS5]
    try:
        proxy = await get_proxy_repo().getProxyByPhone(client_data.phone)
        prox = proxy.replace('@', ':')
        dataProxy = prox.split(':')
        if await get_proxy_repo().testProxy(await get_proxy_repo().getProxyByIdClient(
                await get_proxy_repo().getClientIdByPhone(client_data.phone))):
            if len(dataProxy) == 2:
                try:
                    proxy = {
                        'proxy_type': python_socks.ProxyType.HTTP,
                        'addr': dataProxy[0],
                        'port': int(dataProxy[1]),
                        'rdns': True
                    }
                    client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash,
                                            proxy=proxy)
                    await client.connect()
                    print(1)
                    return client
                except:
                    await get_proxy_repo().setERRORProxy(await get_proxy_repo().getClientIdByPhone(client_data.phone))
                    client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash)
                    await client.connect()
                    print(3)
                    r_repo = get_report_repo()
                    await r_repo.add_ban_proxy(1)
                    return client
            elif len(dataProxy) == 4:
                print(dataProxy)
                try:
                    proxy = {
                        'proxy_type': python_socks.ProxyType.HTTP,
                        'addr': dataProxy[2],
                        'port': int(dataProxy[3]),
                        'username': dataProxy[0],
                        'password': dataProxy[1],
                        'rdns': True
                    }
                    client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash,
                                            proxy=proxy)
                    await client.connect()
                    print(2)
                    return client
                except:
                    await get_proxy_repo().setERRORProxy(await get_proxy_repo().getClientIdByPhone(client_data.phone))
                    client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash)
                    await client.connect()
                    print(3)
                    r_repo = get_report_repo()
                    await r_repo.add_ban_proxy(1)
                    return client
            else:
                client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash)
                await client.connect()
                print(4)
                return client
        else:
            await get_proxy_repo().setERRORProxy(await get_proxy_repo().getClientIdByPhone(client_data.phone))
            client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash)
            await client.connect()
            print(3)
            r_repo = get_report_repo()
            await r_repo.add_ban_proxy(1)
            return client
    except Exception as err:
        LOGGER.error(err)
        client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash)
        await client.connect()
        print(1)
        return client
    

async def get_chats(client_data):
    client_id = await get_proxy_repo().getClientIdByPhone(client_data.phone)
    statusProxy = await get_proxy_repo().getStatusProxy(client_id)
    if statusProxy == 1:
        client = await get_client(client_data)
        try:
            dialogs = await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))

            chats = []
            for chat in dialogs.chats:
                if hasattr(chat, "participants_count") and chat.participants_count and chat.participants_count > 0:
                    chats.append(chat)
            return chats
        except UserDeactivatedBanError as e:
            c = get_client_repo()
            LOGGER.debug(e, f"Забанен {client}")
            await c.banned(client_id)
        except SessionRevokedError as e:
            c = get_client_repo()
            LOGGER.debug(e, f"Забанен {client}")
            await c.banned(client_id)


async def get_members(client, chat_id, user_id) -> List[dict] or None:
    members = []
    try:
        chat = await client.get_entity(chat_id)
        participants = await client.get_participants(chat, aggressive=True)
    except (ChatAdminRequiredError) as e:
        LOGGER.error(e)
        return None
    except (UserDeactivatedBanError) as e:
        LOGGER.error(e)
        return None
    for prt in participants:
        members.append({
            'id': prt.id,
            'first_name': prt.first_name or None,
            'last_name': prt.last_name or None,
            'username': prt.username or None,
            'chat_id': chat_id,
            'client_id': str(user_id)
        })

    return members


async def hascyr(s):
    lower = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    return lower.intersection(s.lower()) != set()


async def search_by_keyw(message: types.Message, client_data, keywords: str, lang: str):
    RESULT_LIST = []
    client = await get_client(client_data)
    await message.answer(f'Идет поиск по ключевым словам ({keywords})...')
    await message.answer('Поиск может занять от 1 до 2 минут')
    if lang == 'ru':
        help_search = ['Россия', 'rus', 'чат', 'группа']
    elif lang == 'en':
        help_search = ['en', 'USA', 'America', 'chat', 'england']
    word_list = []
    sample_list = []
    try:
        for i in range(7):
            s = random.sample(keywords.split(' '), 2)
            sample_list.append(str(s[0]+' '+ s[1]))
    except Exception as er:
        LOGGER.error(er)
    try:
        for i in keywords.split(' '):
            translator = Translator()
            translated = translator.translate(i)
            word_list.append(translated.text)
    except Exception as er:
        LOGGER.error(er)
    for i in keywords.split(' '):
        word_list.append(i)
    # if lang == 'ru':
    #     try:
    #         for i in keywords.split(' '):
    #             word_list.append(translit(i, reversed=True))
    #     except Exception as er:
    #         print(er)
    for i in word_list:
        if i == '':
            word_list.remove(i)
    word_list = list(set(word_list))
    LOGGER.info(word_list)
    channel = get_channel_repo()
    for w in word_list:
        await channel.add_new_keyword(w)
        for h in help_search:
            print(f'{w} {h}')
            result = await client(SearchRequest(
                q = f'{w} {h}',
                limit=100
            ))
            for i in result.chats:
                if i.broadcast==False:
                    if i.participants_count >= 500:
                        try:
                            users = await client(
                                GetParticipantsRequest(
                                    channel=i.username,filter=ChannelParticipantsSearch(''), limit=39,
                                    offset=0, hash=0
                                )
                            )
                            if len(users.users) > 38:
                                history = await client(GetHistoryRequest(
			                           peer=i.username,
			                           offset_id=0,
			                           offset_date=None, add_offset=0,
			                           limit=5, max_id=0, min_id=0,
			                           hash=0))
                                s = ''
                                for mes in history.messages:
                                    s = s + mes.message
                                if lang == 'ru':
                                    if await hascyr(s) or await hascyr(i.title):
                                        await channel.add_new_channel(
                                            i.id, i.title, i.access_hash,
                                            i.username, i.participants_count, w, lang
                                        )
                                        if i.username not in RESULT_LIST:
                                            RESULT_LIST.append(i.username)
                                elif lang == 'en':
                                    if not await hascyr(s):
                                        await channel.add_new_channel(
                                            i.id, i.title, i.access_hash,
                                            i.username, i.participants_count, w, lang
                                        )
                                        if i.username not in RESULT_LIST:
                                            RESULT_LIST.append(i.username)
                        except Exception as err:
                            LOGGER.debug(err)
                            continue
    for w in keywords.split(' ')+list(set(sample_list)):
        result = await client(SearchRequest(
                q = w,
                limit=100
            ))
        for i in result.chats:
            if i.broadcast==False:
                if i.participants_count >= 500:
                    try:
                        users = await client(
                            GetParticipantsRequest(
                                channel=i.username,filter=ChannelParticipantsSearch(''), limit=39,
                                offset=0, hash=0
                            )
                        )
                        if len(users.users) > 38:
                            history = await client(GetHistoryRequest(
			                        peer=i.username,
			                        offset_id=0,
			                        offset_date=None, add_offset=0,
			                        limit=5, max_id=0, min_id=0,
			                        hash=0))
                            s = ''
                            for mes in history.messages:
                                s = s + mes.message
                            if lang == 'ru':
                                print('ok')
                                if await hascyr(s) or await hascyr(i.title):
                                    await channel.add_new_channel(
                                        i.id, i.title, i.access_hash, i.username, i.participants_count, w, lang
                                    )
                                    if i.username not in RESULT_LIST:
                                        RESULT_LIST.append(i.username)
                            elif lang == 'en':
                                if not await hascyr(s):
                                    await channel.add_new_channel(
                                        i.id, i.title, i.access_hash,
                                        i.username, i.participants_count, w, lang
                                    )
                                    if i.username not in RESULT_LIST:
                                        RESULT_LIST.append(i.username)
                    except Exception as err:
                        LOGGER.error(err)
                        continue
    return RESULT_LIST


async def send_search_history(user_id):
    try:
        channel_repo = get_channel_repo()
        result = await channel_repo.get_user_searches(user_id)
        workbook = xlsxwriter.Workbook(F'history/search_history_{user_id}.xlsx')
        worksheet = workbook.add_worksheet('first_sheet')
        worksheet.write(0, 0, 'ключевые слова')
        worksheet.write(0, 1, 'найденные чаты')
        col = 0
        for r in result:
            worksheet.write(col+1, 0, r)
            worksheet.write(col+1, 1, '\n'.join(result[r]))
            col+=1
        workbook.close()
        return len(result)
    except Exception as err:
        LOGGER.error(err)


async def mem_scraping(message: types.Message, client_data, lang, groups: list, uname):
    member_repo = get_member_repo()
    client = await get_client(client_data)
    phone_start_list = [
        '994', '373', '374', '7', '375', '992',
        '993', '996', '380', '371', '998', '370', '372', 
        '995'
    ]
    await message.answer('Идет подсчет участников, к которым можно получить доступ...')
    count_mem = 0
    user_count = 0 
    workbook = xlsxwriter.Workbook(F'members/members_contacts_{uname}.xlsx')
    worksheet = workbook.add_worksheet('first_sheet')
    worksheet.write(0, 0, 'user_id')
    worksheet.write(0, 1, 'username')
    worksheet.write(0, 2, 'name')
    worksheet.write(0, 3, 'phone')
    worksheet.write(0, 4, 'group')
    col = 0
    for gr in groups:
        go_chat = await client.get_entity(gr)
        participants = await client.get_participants(go_chat, aggressive=True)
        for user in participants:
            user_count+=1
            if user.phone:
                if lang == 'ru':
                    if str(user.phone).startswith(tuple(i for i in phone_start_list)):
                        user_id = user.id or ''
                        username = user.username or ''
                        first_name = user.first_name or ''
                        last_name = user.last_name or ''
                        phone = user.phone
                        name= (first_name + ' ' + last_name).strip()
                        worksheet.write(col+1, 0, user_id)
                        worksheet.write(col+1, 1, username)
                        worksheet.write(col+1, 2, name)
                        worksheet.write(col+1, 3, phone)
                        worksheet.write(col+1, 4, gr)
                        col = col + 1
                        count_mem += 1
                elif lang == 'en':
                    if not str(user.phone).startswith(tuple(i for i in phone_start_list)):
                        user_id = user.id or ''
                        username = user.username or ''
                        first_name = user.first_name or ''
                        last_name = user.last_name or ''
                        phone = user.phone
                        name= (first_name + ' ' + last_name).strip()
                        worksheet.write(col+1, 0, user_id)
                        worksheet.write(col+1, 1, username)
                        worksheet.write(col+1, 2, name)
                        worksheet.write(col+1, 3, phone)
                        worksheet.write(col+1, 4, gr)
                        col = col + 1
                        count_mem += 1
                await member_repo.create(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                    phone=user.phone,
                    chat_id=go_chat.id,
                    client_id=uname
                )
        await asyncio.sleep(1)
    workbook.close()
    await message.answer('Идет подсчет участников, к которым можно получить доступ...')
    print(user_count)
    report_repo = get_report_repo()
    await report_repo.add_count_tel(count_mem)
    return count_mem
        # db.db_users.add_new_user(prt.id, prt.first_name, prt.last_name, prt.username, chat_id, prt.phone)


async def _send_invite(client: TelegramClient, target_chat, member):
    target_chat_entity = await client.get_input_entity(int(target_chat))
    await client.get_dialogs()
    member_entity = await client.get_input_entity(member.username)
    LOGGER.info(member_entity)
    tChat = None
    try:
        hash = target_chat_entity.access_hash
        tChat = 1
    except Exception as e:
        LOGGER.error(e)
        hash = target_chat_entity.chat_id
        tChat = 0

    if tChat == 1:
        LOGGER.info(hash)
        LOGGER.info('Ждем 1 минуту CHANNEL')
        await asyncio.sleep(60)
        await client(InviteToChannelRequest(target_chat_entity, [member_entity]))
    else:
        LOGGER.info(hash)
        LOGGER.info('Ждем 1 минуту CHAT')
        await asyncio.sleep(60)
        await client(AddChatUserRequest(int(target_chat), member_entity, 100))


async def new_inviting(client, member, target_chat, active_accs):
    try:
        c_repo = get_client_repo()
        #r_repo = get_report_repo()
        clientID = await c_repo.get_id_by_api_id(client.api_id)
        await c_repo.plus_count_invite(clientID, 1)
        if await c_repo.get_data_paused_invite(clientID) == None:
            await c_repo.set_data_paused_invite(clientID)
        await _send_invite(client, target_chat, member)
        #await r_repo.add_count_tg(1)
    except Exception as err:
        LOGGER.error(err)


async def pre_inviting(mes: types.Message, active_accs, target_chat, members):
    m_repo = get_member_repo()
    c_repo = get_client_repo()
    error_count = 0
    active_accs = await check_ban_accs(active_accs)
    first_client = await get_client(active_accs[0])
    users_chat = [user.id for user in await first_client.get_participants(int(target_chat), aggressive=True)]
    new_memb_list_id = []
    # clients = cicle([await get_client(acc) for acc in active_accs])
    clients = [await get_client(acc) for acc in active_accs]
    members = cicle(members)
    curr_count = 0
    try:
        while not new_memb_list_id in users_chat:
            for client in clients:
                clientID = await c_repo.get_id_by_api_id(client.api_id)
                cl = await c_repo.get_by_id(clientID)
                await c_repo.check_end_pause(clientID)
                if await c_repo.get_count_invite(clientID) >= 30:
                    LOGGER.info(f'Аккаунт {cl.phone} на паузе!')
                    await c_repo.check_valid_all_acc()
                    continue
                if await c_repo.get_status_id(clientID) == 3:
                    LOGGER.info(f'Аккаунт {cl.phone} заблокирован!')
                    await c_repo.check_valid_all_acc()
                    continue
                member = next(members)
                flag = True
                if stop_invite_prof:
                    return
                while flag:
                    print(member)
                    if int(member[0]) in users_chat:
                        LOGGER.info(f'User {member[0]} уже есть в чате!')
                        member = next(members)
                        continue
                    if await m_repo.getRestricted(member[0]) == 0:
                        LOGGER.info(f'У пользователя заблокирован прием инвайтов!')
                        member = next(members)
                        continue
                    flag=False
                try:
                    task = asyncio.create_task(new_inviting(client, member, target_chat, active_accs))
                    await task
                except UserAlreadyParticipantError as e:
                    LOGGER.info('Уже есть в чате')
                    error_count += 1
                    LOGGER.error(e)
                    continue
                except UserPrivacyRestrictedError as e:
                    LOGGER.info('Обновил приватность')
                    await m_repo.updateRestricted(member.id, 0)
                    error_count += 1
                    LOGGER.error(e)
                    continue
                except UserDeactivatedBanError as e:
                    c = get_client_repo()
                    LOGGER.error(e, f"{client}")
                    await c.banned(clientID)
                    r_repo = get_report_repo()
                    await r_repo.add_ban_acc(1)
                    error_count += 1
                    continue
                except SessionRevokedError as e:
                    c = get_client_repo()
                    LOGGER.error(e, f"{client}")
                    await c.banned(clientID)
                    r_repo = get_report_repo()
                    await r_repo.add_ban_acc(1)
                    continue
                # except PeerFloodError:
                #     print("Getting Flood Error from telegram. Please try again after some time.")
                #     continue
                except ValueError as e:
                    LOGGER.error(e)
                    error_count += 1
                    continue
                except Exception as e:
                    LOGGER.error(e)
                    error_count += 1
                    continue
                ch_c_repo = get_channel_client_repo()
                await ch_c_repo.add_one_success_inv(target_chat)
                await m_repo.updateRestricted(member.id, 1)
            curr_count += 1
            await asyncio.sleep(3000 / len(active_accs))
        await mes.answer('Инвайтинг завершен!')
    except SessionRevokedError as e:
        LOGGER.error(e)
        await mes.answer(f'{e}\nИнвайтинг завершен с ошибкой!')


async def inviting(mes: types.Message, active_accs, target_chat, members):
    m_repo = get_member_repo()
    c_repo = get_client_repo()
    error_count = 0
    active_accs = await check_ban_accs(active_accs)
    first_client = await get_client(active_accs[0])
    users_chat = [user.id for user in await first_client.get_participants(int(target_chat), aggressive=True)]
    new_memb_list_id = []
    # clients = cicle([await get_client(acc) for acc in active_accs])
    clients = [await get_client(acc) for acc in active_accs]
    members = cicle(members)
    curr_count = 0
    try:
        while not new_memb_list_id in users_chat:
            for client in clients:
                clientID = await c_repo.get_id_by_api_id(client.api_id)
                cl = await c_repo.get_by_id(clientID)
                await c_repo.check_end_pause(clientID)
                if await c_repo.get_count_invite(clientID) >= 30:
                    LOGGER.info(f'Аккаунт {cl.phone} на паузе!')
                    await c_repo.check_valid_all_acc()
                    continue
                if await c_repo.get_status_id(clientID) == 3:
                    LOGGER.info(f'Аккаунт {cl.phone} заблокирован!')
                    await c_repo.check_valid_all_acc()
                    continue
                member = next(members)
                flag = True
                if stop_invite_prof:
                    return
                while flag:
                    LOGGER.info(member)
                    if int(member[0]) in users_chat:
                        LOGGER.info(f'User {member[0]} уже есть в чате!')
                        member = next(members)
                        continue
                    if await m_repo.getRestricted(member[0]) == 0:
                        LOGGER.info(f'У пользователя заблокирован прием инвайтов!')
                        member = next(members)
                        continue
                    flag = False
                try:
                    task = asyncio.create_task(new_inviting(client, member, target_chat, active_accs))
                    await task
                except UserAlreadyParticipantError as e:
                    LOGGER.info('Уже есть в чате')
                    error_count += 1
                    LOGGER.error(e)
                    continue
                except UserPrivacyRestrictedError as e:
                    LOGGER.info('Обновил приватность')
                    await m_repo.updateRestricted(member.id, 0)
                    error_count += 1
                    LOGGER.error(e)
                    continue
                except UserDeactivatedBanError as e:
                    c = get_client_repo()
                    LOGGER.info(e, f"{client}")
                    LOGGER.error(e)
                    await c.banned(clientID)
                    r_repo = get_report_repo()
                    await r_repo.add_ban_acc(1)
                    error_count += 1
                    continue
                except SessionRevokedError as e:
                    c = get_client_repo()
                    LOGGER.info(e, f"{client}")
                    await c.banned(clientID)
                    r_repo = get_report_repo()
                    await r_repo.add_ban_acc(1)
                    continue
                # except PeerFloodError:
                #     print("Getting Flood Error from telegram. Please try again after some time.")
                #     continue
                except ValueError as e:
                    LOGGER.error(e)
                    error_count += 1
                    continue
                except Exception as e:
                    LOGGER.error(e)
                    error_count += 1
                    continue
                ch_c_repo = get_channel_client_repo()
                await m_repo.updateRestricted(member.id, 1)
            curr_count += 1
            await asyncio.sleep(3000 / len(active_accs))
        await mes.answer('Инвайтинг завершен!')
    except SessionRevokedError as e:
        await mes.answer(f'{e}\nИнвайтинг завершен с ошибкой!')


async def disconnect_all() -> None:
    try:
        clients = clients_context.get()
        for cl in clients:
            await clients[cl]['client'].disconnect()
    except Exception as err:
        LOGGER.error(err)
    

# async def chek_clients_admin_role(mes,clients, hash, bot):
#     for client in clients:
#         try:
#             ent = await client.get_entity(hash)
#             print(ent)
#             b = await bot.get_me()
#             id_b = b['id']
#
#             user_status = await bot.get_chat_member(chat_id=ent.id, user_id=id_b)
#             print(user_status)
#             break
#         except Exception as e:
#             print("ВОТ ОНА", e)
#             try:
#                 ch = await client(CheckChatInviteRequest(hash))
#                 print(ch)
#                 user_id = mes.from_user.id
#                 user_status = await bot.get_chat_member(chat_id=ch.chat.id, user_id=mes.from_user.id)
#                 print(user_status)
#                 break
#             except Exception as e:
#                 print(e)
#                 break



async def add_client_in_chat(mes, clients, hash, user_id, accs, bot):
    ch_c_repo = get_channel_client_repo()
    c_repo = get_client_repo()
    phons = [i[7] for i in accs]
    ent = None
    ch = None
    k = 0
    for client in clients:
        try:
            ent = await client.get_entity(hash)
            flag = True
        except:
            try:
                ch = await client(CheckChatInviteRequest(hash))
            except Exception as e:
                LOGGER.error(e)
                await mes.answer(f'Упс... Что-то пошло не так.\n'
                                 f'Чат не удалось добавить. Проверьте каждый пункт из списка ниже и повторите попытку.\n'
                                 f'1. Ссылка-приглашение активна\n'
                                 f'2. У бота есть разрешения: удаление сообщений; блокировка пользователей; пригласительные ссылки.\n'
                                 f'Ошибка:{str(e)[:str(e).find("(")]}', reply_markup=error_add_channel())
                return False

            flag = False
        try:
            if flag:
                ent = await client.get_entity(hash)
                ids = await c_repo.get_all_channel(user_id, ent.id)
                LOGGER.info('1', ids)
                LOGGER.info('1',ent.id)
                if str(ent.id) in ids and len(ids) >= 3:
                    await mes.answer('Эта группа уже подключена!', reply_markup=error_add_channel())
                    return
                await client(JoinChannelRequest(hash))
                await c_repo.set_user_and_channel_id(phons[k], mes.from_user.id, ent.id)
                LOGGER.info(phons[k])
            else:
                try:
                    await client(ImportChatInviteRequest(hash))
                except:
                    await asyncio.sleep(5)
                    await client(ImportChatInviteRequest(hash))
                ch = await client(CheckChatInviteRequest(hash))
                ids = await c_repo.get_all_channel(user_id, ch.chat.id)
                LOGGER.info('2', ids)
                LOGGER.info('2', ch.chat.id)
                if str(ch.chat.id) in ids and len(ids) >= 3:
                    await mes.answer('Эта группа уже подключена!', reply_markup=error_add_channel())
                    await client.delete_dialog(ch.chat.id)
                    return
                await c_repo.set_user_and_channel_id(phons[k], mes.from_user.id, ch.chat.id)
                LOGGER.info(phons[k])
        except UserAlreadyParticipantError as e:
            LOGGER.error(e)
            c = await client.get_me()
            p_client = c.phone
            await mes.answer(f'Аккаунт {p_client} уже есть в этом чате!')
            continue
        except Exception as e:
            await mes.answer(f'Упс... Что-то пошло не так.\n'
                             f'Чат не удалось добавить. Проверьте каждый пункт из списка ниже и повторите попытку.\n'
                             f'1. Ссылка-приглашение активна\n'
                             f'2. У бота есть разрешения: удаление сообщений; блокировка пользователей; пригласительные ссылки.\n'
                             f'Ошибка:{str(e)[:str(e).find("(")]}', reply_markup=error_add_channel())
            LOGGER.error(e)
            return False
        k+=1
    try:
        await ch_c_repo.addChannel(user_id, ent.id, ent.title)
    except Exception as e:
        LOGGER.debug("ТУТ 1", e)
        pass
    try:
        await ch_c_repo.addChannel(user_id, ch.chat.id, ch.chat.title)
    except Exception as e:
        LOGGER.debug("ТУТ 2", e)
        pass
    return True


def cicle(l: List):
    while True:
        for i in l:
            yield i
