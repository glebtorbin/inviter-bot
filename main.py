#!venv/bin/python
import logging
import logging.handlers as loghandlers
import random
from enum import Enum
from datetime import datetime, timedelta
import os
import re
from dirt_tongue import is_dirt
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from telethon.errors.rpcerrorlist import PhoneCodeExpiredError

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from report_generators import gen_report, gen_plan

from wapp.wa_xlsx_scrap import WA_xlsx_search
from wapp.wa_api import wa_verify, wa_check_state, wa_send_qr, wa_mailing, wa_get_acc_settings, wa_logout, wa_reboot
from filters.groups_chats import IsGroup
import client_api
from answer_generators import sendG_CAccounts, sendG_chats, choice_chats_for_invite, choice_chats_for_invite_p_o_i, send_WA_accs, send_WA_mailing
from config import get_bot_token
from db.base import database
from enums import CProxyStatuses, CStatuses, CWorkes, URoles, WA_CWorkes, WA_CStatuses, WA_Mailing_statuses
from keyboards import (
    get_admin_markup, get_inline_invite_stop_markup,
    get_services_markup, go_to_main_markup, parse_start_markup,
    lang_ch_markup, user_accept_markup, sphere_markup, work_markup,
    bot_usage_markup, get_user_markup, get_profile_markup, cur_markup,
    pay_markup, true_ans_markup, accept_bot_markup, success_add_channel, error_pars_chat, go_to_profile,
    chat_profile_card, get_inline_chats_pars, chat_pars_card, call_employee, choice_add_sour, get_inline_del_source,
    cancel_markup_profile, add_triger_markup, inline_pay_markup,
    inline_no_groups__markup, inline_apply_group_ch_markup, inline_scrap_or_invite_markup,
    send_contact_markup, cancel_markup, nps_markup, nps_markup, support_markup, wa_check_qr_markup,
    wa_save_mailing_markup, get_inline_wa_client_markup
)
from repositories.getRepo import (get_channel_repo, get_client_repo, get_member_repo,
                                  get_proxy_repo, get_user_repo, get_report_repo, get_channel_client_repo,
                                  get_source_repo, get_plan_repo, get_wa_client_repo)
from state import GlobalState, ClientState

storage = MemoryStorage()

TG_TOKEN = get_bot_token()

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()

async def create_folders():
    for folder in ['logs', 'history', 'members', 'sessions', 'qr', 'wa_mailing_contacts']:
        if not os.path.exists(folder):
            os.makedirs(folder)


LOGGER = logging.getLogger('applog')
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s  %(filename)s  %(funcName)s  %(lineno)d  %(name)s  %(levelname)s: %(message)s')
log_handler = loghandlers.RotatingFileHandler(
    './logs/botlog.log',
    maxBytes=1000000,
    encoding='utf-8',
    backupCount=50
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(formatter)
LOGGER.addHandler(log_handler)


class Bts(Enum):
    """ Надписи на кнопках """
    ACCOUNTS = 'Аккаунты'
    WA_ACCS = 'Аккаунты WA'
    GROUPS = 'Группы'
    SERVICES = 'Услуги'
    GO_TO_MAIN = '◀️На главную'
    ADD_ACCOUNT = 'Добавить аккаунт'
    ADD_WA_ACCOUNT = 'Добавить аккаунт WA'
    ADD_WA_MAILING = 'Создать WA рассылку'
    MAILING = 'Рассылка WA'
    SEARCH_OPEN_CH = 'Поиск открытых чатов'
    CANCEL = 'отмена'
    PARSE_START = 'Получить данные'
    CHANGE_GROUP = 'Изменить группы'
    SEARCH_HISTORY = 'История и результаты поиска'
    ANTI_SPAM = 'Антиспам'


class ClientBts(Enum):
    """ Надписи на кнопках для клиента"""
    ACCEPT_POLICY = 'Принять и продолжить'
    SEARCH_OP_CHATS = 'Поиск источников(чатов)'
    SET_UP_INVITE = 'Настроить инвайт'
    SEARCH_HISTORY = 'История поиска'
    QUE_AND_ANS = 'Вопросы и ответы'
    PROFILE = 'Профиль'
    GO_TO_MAIN = '◀️На главную'
    REPLENISH_BALANCE = 'Пополнить баланс'


MAIN_MARKUP = get_admin_markup((Bts.ACCOUNTS.value, Bts.GROUPS.value), (Bts.SERVICES.value, Bts.WA_ACCS.value))

MAIN_CL_MARKUP = get_user_markup((
    ClientBts.SEARCH_OP_CHATS.value, ClientBts.SET_UP_INVITE.value),
    (ClientBts.SEARCH_HISTORY.value, ClientBts.QUE_AND_ANS.value
), (ClientBts.PROFILE.value, ))


async def send_report_and_plan(dp:Dispatcher):
    try:
        report = await gen_report()
        plan = await gen_plan()
        r_repo = get_report_repo()
        p_repo = get_plan_repo()
        await dp.bot.send_message(438202772, report)
        await dp.bot.send_message(438202772, plan)
        await r_repo.createReport()
        LOGGER.info(f'Отчет отправлен')
    except Exception as err:
        LOGGER.error(f'Проблема с отчетом: {err}')


scheduler.add_job(send_report_and_plan, 'cron', day_of_week='mon-sun', hour=14, minute=44, args=(dp,))
# scheduler.add_job(wa_verify, 'cron', day_of_week='mon-sun', hour=16, minute=16)

async def on_startup(dp):
    """Соединяемся с БД при запуске бота."""
    try:
        await database.connect()
        await create_folders()
        LOGGER.info('DB is running')
        LOGGER.info('service folders created')
    except Exception as err:
        LOGGER.critical('Не подключается БД!')


# @dp.message_handler(content_types=['new_chat_members','left_chat_member'])
async def deleteServiceMes(mes: types.message):
    try:
        await bot.delete_message(mes.chat.id, mes.message_id)
    except Exception as err:
        LOGGER.error(err)


# @dp.message_handler(commands='start', state=None)
async def start(message: types.Message, state: FSMContext):
    try:
        args = message.get_args()
        async with state.proxy() as data:
            data['where_from'] = args
            data['user_id'] = message.from_user.id
        u_repo = get_user_repo()
        user = await u_repo.get_by_id(message.chat.id)
        if user is None:
            await message.answer("Ваша конфиденциальность важна для Полная информация "
                                "о собираемых данных и о порядке их обработки содержится в "
                                "нашей <a>Политика конфиденциальности</a>", parse_mode='html', reply_markup=user_accept_markup())
            r_repo = get_report_repo()
            await r_repo.add_new_users(1)
        elif user.role_id == URoles.ADMIN.value['id']:
            await GlobalState.admin.set()
            await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)
        elif user.role_id == URoles.USER.value['id']:
            await ClientState.client.set()
            await message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)  
        else:
            await message.answer("Ожидание регистрации")
    except Exception as err:
        LOGGER.error(f'Ошибка функции start: {err}')


async def reg_menu_ask_phone(message: types.Message, state: FSMContext):
    try:
        await state.set_state(ClientState.send_phone_code)
        await message.answer(
            'Для продолжения регистрации поделитесь своим номером телефона по кнопке ниже',
            reply_markup=send_contact_markup()
        )
    except Exception as err:
        LOGGER.error(err)


async def reg_menu_send_phone_code(message: types.message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['cl_phone'] = message.contact.phone_number
        await state.set_state(ClientState.about_1)
        await message.answer('Расскажите немного о себе\n'
                             'Мы настроим ваш INVITE_Bot на основе вашего выбора')
        await message.answer('Какая ваша сфера занятости?', reply_markup=sphere_markup())
    except Exception as err:
        LOGGER.error(err)


async def reg_menu_sphere_ask(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        async with state.proxy() as data:
            data['cl_sphere'] = (call.data).split(':')[1]
        await state.set_state(ClientState.about_2)
        await call.message.answer('Кем вы работаете?', reply_markup=work_markup())
    except Exception as err:
        LOGGER.error(err)


async def reg_menu_bot_usage(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        async with state.proxy() as data:
            data['cl_job_title'] = (call.data).split(':')[1]
        await state.set_state(ClientState.about_3)
        await call.message.answer('Для каких целей планируете использовать Invite_Bot?', reply_markup=bot_usage_markup())
    except Exception as err:
        LOGGER.error(err)


async def reg_menu_save_answers(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        u_repo = get_user_repo()
        async with state.proxy() as data:
            data['cl_bot_usage'] = (call.data).split(':')[1]
            await u_repo.create(
                id= str(call.from_user.id),
                first_name=call.message.chat.first_name,
                last_name=call.message.chat.last_name,
                username=call.message.chat.username,
                role_id=URoles.USER.value['id'],
                phone=data['cl_phone'],
                sphere=data['cl_sphere'],
                job_title=data['cl_job_title'],
                bot_usage=data['cl_bot_usage'],
                where_from=data['where_from']
            )
        await state.set_state(ClientState.client)
        await call.message.answer('Регистрация пройдена успешно!')
        await call.message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.critical(f'Ошибка создания профайла юзера {err}')
        await call.message.answer('Нам очень жаль, что-то пошло не так, наши разрабочики уже решают эту проблему')


async def user_profile(message: types.Message, state: FSMContext):
    try:
        user_repo = get_user_repo()
        ch_c_repo = get_channel_client_repo()
        count_channel = await ch_c_repo.get_count_client_channel(message.from_user.id)
        user = await user_repo.get_by_id(message.from_user.id)
        await message.answer(
            f'ID Profile: {user.id}\nБаланс: {user.balance}\nПодключённых групп: {count_channel}',
            reply_markup=get_profile_markup()
        )
    except Exception as err:
        LOGGER.error(err)

async def que_and_ans(message: types.Message):
    try:
        mes = (
            '• Платные сервисы бота: инвайт; поиск открытых чатов\n'
            '• Бесплатные сервисы бота: удаление спама и тех. уведомлений из чатов;\n'
            '• Аудитория – активные участники популярных телеграм чатов.\n\n'
            '• Стоимость:\n'
            'Инвайт - от 2,5₽ до 1₽ за пользователя\n'
            'Поиск чатов - 100₽ за запрос (30 чатов)\n\n'
            '• Покупать собственные аккаунты или прокси не нужно.\n'
            '• Поиск и инвайт запускаются мгновенно после оплаты.\n'
            '• Для защиты ваших групп от блокировки телеграмом, инвайт пользователей осуществляется постепенно в '
            'течение каждого дня. Не более 300 человек в день.\n\n'
            '• Подключить услуги инвайта можно к неограниченному количеству чатов.\n'
            '• Вы сможете в реальном времени наблюдать статистику приглашенных пользователей.\n'
            '• История поиска открытых чатов доступна в любой момент\n'
            '• Политика конфиденциальности и договор оферта здесь')
        await message.answer(mes, reply_markup=support_markup())
    except Exception as err:
        LOGGER.error(err)


async def replenish_balance(message: types.Message, state: FSMContext):
    await message.answer('Выберите валюту, в которой хотите оплатить. Выбирайте RUB, если Вы из России. '
                   'Во всех остальных случаях следует выбирать USD',
                   reply_markup=cur_markup())
    await state.set_state(ClientState.cur_choice)



async def amount_ask(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    async with state.proxy() as data:
        data['currancy'] = call.data.split(':')[1]
    await call.message.answer('Введите сумму для пополнения')
    await state.set_state(ClientState.paym_confirm)


async def payment_confirmation(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['amount'] = message.text
        await message.answer('Продолжая вы соглашаетесь с политикой и договором офертой\n\n'
                             'Ссылка на договор\n'
                             'Ссылка на политику', reply_markup=pay_markup())
    except:
        await state.set_state(ClientState.client)
        await message.answer('Пополнение баланса сейчас недоступно, попробуйте позже', reply_markup=MAIN_CL_MARKUP)


async def send_wa_accounts(message: types.Message):
    try:
        wa_repo = get_wa_client_repo()
        accounts = await wa_repo.get_all()
        markup = get_admin_markup((Bts.GO_TO_MAIN.value, Bts.ADD_WA_ACCOUNT.value))
        if len(accounts):
            await send_WA_accs(message=message, WA_accounts=accounts, reply_markup=markup)
        else:
            await message.answer("Аккаунтов нет. Выберите действие", reply_markup=markup)
    except Exception as err:
        await message.answer('Нам очень жаль, что-то пошло не так, наши разрабочики уже решают эту проблему')
        LOGGER.error(err)


async def send_wa_mailing(message: types.Message):
    wa_repo = get_wa_client_repo()
    try:
        mailings = await wa_repo.get_all_mailing()
        markup = get_admin_markup((Bts.GO_TO_MAIN.value, Bts.ADD_WA_MAILING.value))
        if len(mailings):
            await send_WA_mailing(message=message, WA_mailings=mailings, reply_markup=markup)
        else:
            await message.answer("Рассылок нет. Выберите действие", reply_markup=markup)
    except Exception as err:
        await message.answer('Нам очень жаль, что-то пошло не так, наши разрабочики уже решают эту проблему')
        LOGGER.error(err)


# @dp.message_handler(Text(equals=Bts.ACCOUNTS.value), state=GlobalState.admin)
async def send_accounts(message: types.Message):
    c_repo = get_client_repo()
    try:
        accounts = await c_repo.get_all()
        markup = get_admin_markup((Bts.GO_TO_MAIN.value, Bts.ADD_ACCOUNT.value))
        if len(accounts):
            await sendG_CAccounts(message, accounts, reply_markup=markup)
        else:
            await message.answer("Аккаунтов нет. Выберите действие", reply_markup=markup)
    except Exception as err:
        await message.answer('Нам очень жаль, что-то пошло не так, наши разрабочики уже решают эту проблему')
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='client:delete', state=GlobalState.admin)
async def account_delete(call: types.CallbackQuery):
    try:
        client_repo = get_client_repo()
        client_id = call.data.split(':')[-1]
        idProxy = await get_proxy_repo().getIdProxyByIdClient(client_id)
        await get_proxy_repo().deleteProxy(idProxy)
        await client_repo.delete(client_id)
        await call.answer(cache_time=60)
        await call.message.answer("Аккаунт удален.")
        await call.message.edit_reply_markup(reply_markup=None)
        LOGGER.info(f'Аккаунт {client_id} удален')
    except Exception as err:
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='client:authorization', state=GlobalState.admin)
async def send_authorization_code(call: types.CallbackQuery, state: FSMContext):
    client_repo = get_client_repo()
    client_id = call.data.split(':')[-1]
    client_data = await client_repo.get_by_id(client_id)
    async with state.proxy() as data:
        data['client_data'] = client_data
    try:
        await client_api.client_is_authorized(client_data)
        client_repo = get_client_repo()
        await client_repo.update(data['client_data'].id, status_id=CStatuses.AUTHORIZED.value['id']) #TODO Возможно нужно поменять, чтобы аккаунты добавлялись в статусе Резерв
        await call.message.answer("Аккаунт авторизован!", reply_markup=MAIN_MARKUP)
        LOGGER.info(f'Аккаунт {client_id} авторизован')
    except:
        res = await client_api.send_phone_hash_code(client_data)
        if res == -1:
            await  call.message.answer("Аккаунт заблокирован!")
            await client_repo.banned(client_id)
            return
        await GlobalState.auth_acc.set()
        await call.message.answer('Введите код: ')
        await call.message.edit_reply_markup(reply_markup=None)


# @dp.message_handler(state=GlobalState.auth_acc)
async def authorization(message: types.Message, state: FSMContext):
    client_repo = get_client_repo()
    async with state.proxy() as data:
        try:
            await client_api.authorize(data['client_data'], int(message.text))
            await client_repo.update(data['client_data'].id, status_id=CStatuses.AUTHORIZED.value['id'])
            await state.finish()
            await GlobalState.admin.set()
            await message.answer("Аккаунт успешно авторизован!", reply_markup=MAIN_MARKUP)
        except PhoneCodeExpiredError as e:
            LOGGER.critical(e)
            await message.answer("Авторизация не возможна, попробуйте другой аккаунт", reply_markup=MAIN_MARKUP)
            await state.finish()
            await GlobalState.admin.set()


# @dp.callback_query_handler(text_contains='client:addProxy', state=GlobalState.admin)
async def waitProxy(call: types.CallbackQuery, state: FSMContext):
    try:
        client_id = call.data.split(':')[-1]
        client_data = await get_client_repo().get_by_id(client_id)
        async with state.proxy() as data:
            data['client_data'] = client_data
        await GlobalState.add_proxy.set()
        await call.message.answer('Введите прокси (ip:port или user:pass@ip:port): ')
    except Exception as err:
        LOGGER.error(err)


# @dp.message_handler(state=GlobalState.add_proxy)
async def addProxy(message: types.Message, state: FSMContext):
    try:
        if await get_proxy_repo().testProxy(message.text):
            async with state.proxy() as data:
                await get_proxy_repo().addProxy(data['client_data'].id, proxy=message.text)
                idProxy = await get_proxy_repo().getIdProxy(message.text)
                await get_client_repo().update(data['client_data'].id, proxy_id=idProxy[0], proxy_status_id=2)
            await message.answer('Прокси добавлены!', reply_markup=MAIN_MARKUP)
        else:
            await message.answer('Эти прокси не валидны!', reply_markup=MAIN_MARKUP)
        await state.finish()
        await GlobalState.admin.set()
    except Exception as err:
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='client:proxyON', state=GlobalState.admin)
async def proxyON(call: types.CallbackQuery, state: FSMContext):
    try:
        client_id = call.data.split(':')[-1]
        client_data = await get_client_repo().get_by_id(client_id)
        async with state.proxy() as data:
            data['client_data'] = client_data
        if await get_proxy_repo().getStatusProxy(data['client_data'].id) == 2:
            await get_proxy_repo().setONProxy(data['client_data'].id)
        await call.message.answer('Прокси были включены!')
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception as err:
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='client:proxyOFF', state=GlobalState.admin)
async def proxyOFF(call: types.CallbackQuery, state: FSMContext):
    try:
        client_id = call.data.split(':')[-1]
        client_data = await get_client_repo().get_by_id(client_id)
        async with state.proxy() as data:
            data['client_data'] = client_data
        if await get_proxy_repo().getStatusProxy(data['client_data'].id) == 1:
            await get_proxy_repo().setOFFProxy(data['client_data'].id)
        await call.message.answer('Прокси были вылючены!')
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception as err:
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='client:ProxyDelete', state=GlobalState.admin)
async def proxyDELETE(call: types.CallbackQuery, state: FSMContext):
    try:
        client_id = call.data.split(':')[-1]
        client_data = await get_client_repo().get_by_id(client_id)
        async with state.proxy() as data:
            data['client_data'] = client_data
        await get_proxy_repo().setNONEProxy(data['client_data'].id)
        await get_proxy_repo().deleteProxy(client_data[3])
        await call.message.answer('Прокси были удалены!')
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception as err:
        LOGGER.error(err)


# @dp.message_handler(Text(equals=Bts.ADD_ACCOUNT.value), state=GlobalState.admin)
async def ehco_add_account(message: types.Message):
    await GlobalState.set_api_id.set()
    await message.answer('Введите api_id', reply_markup=types.ReplyKeyboardRemove())


# @dp.message_handler(Text(equals=Bts.CANCEL.value, ignore_case=True), commands=Bts.CANCEL.value, state='*')
async def cancel(message: types.Message, state: FSMContext):
    try:
        user_repo = get_user_repo()
        user = await user_repo.get_by_id(message.from_user.id)
        current_state = await state.get_state()
        if user.role_id == 10:
            if current_state is None or current_state == 'GlobalState:admin':
                return
            await state.finish()
            await GlobalState.admin.set()
            await message.reply('OK')
            await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)
        elif user.role_id == 2:
            if current_state is None or current_state == 'ClientState:client':
                return
            await state.finish()
            await ClientState.client.set()
            await message.reply('OK')
            await message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)     


async def WA_echo_add_account(message: types.Message):
    await GlobalState.wa_instance.set()
    await message.answer('Введите id_instance', reply_markup=types.ReplyKeyboardRemove())


async def WA_set_id_instance(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['wa_instance'] = str(message.text)
    await GlobalState.wa_token.set()
    await message.answer('Введите api_token')


async def WA_set_api_token(message: types.Message, state: FSMContext):
    try:
        wa_repo = get_wa_client_repo()
        async with state.proxy() as data:
            data['wa_token'] = message.text
            await wa_repo.create(
                work_id=WA_CWorkes.UNWORKING.value['id'],
                status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id'],
                instance=data['wa_instance'],
                token=data['wa_token'],
                phone='not authorized'
            )
        await message.answer("Аккаунт сохранен")
        await GlobalState.admin.set()
        await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)
    except Exception as err:
        LOGGER.error(err)


async def wa_auth(call: types.CallbackQuery, state: FSMContext):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        async with state.proxy() as data:
            data['wa_client_data'] = client_data
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'notAuthorized':
            await GlobalState.wa_send_qr.set()
            await wa_send_qr(client_data)
            qr = open(f'./qr/qr_{client_data.id_instance}.png', 'rb')
            await bot.send_photo(call.from_user.id, qr, reply_markup=cancel_markup())
            qr.close()
            path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./qr/qr_{client_data.id_instance}.png'
            )
            os.remove(path)
            await call.message.answer(
                'Отсканируйте QR-code в мобильном приложении Whatsapp',
                reply_markup=wa_check_qr_markup(client_data)
            )
        elif wa_acc_state == 'authorized':
            phone = await wa_get_acc_settings(client_data)
            await wa_repo.update(client_data.id, phone = phone['wid'],status_id=WA_CStatuses.AUTHORIZED.value['id'])
            await call.message.answer('Аккаунт успешно авторизован', reply_markup=MAIN_MARKUP)
        elif wa_acc_state == 'blocked':
            await wa_repo.update(client_data.id, status_id=WA_CStatuses.BANNED.value['id'])
            await call.message.answer('Аккаунт заблокирован', reply_markup=MAIN_MARKUP)
        else:
            await call.message.answer(
                'Аккаунт либо в спящем режиме, либо в процессе запуска. Попробуйте позже',
                reply_markup=MAIN_MARKUP
            )
    except Exception as err:
        LOGGER.error(err)


async def wa_check_auth(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            await GlobalState.admin.set()
            phone = await wa_get_acc_settings(client_data)
            await wa_repo.update(client_data.id, phone = phone['wid'],status_id=WA_CStatuses.AUTHORIZED.value['id'])
            await call.message.answer('Аккаунт успешно авторизован', reply_markup=MAIN_MARKUP)
        else:
            await call.message.answer(
                'Что-то пошло не так. Попробуйте еще раз',
                reply_markup=cancel_markup()
            )
    except Exception as err:
        LOGGER.error(err)


async def WA_logout(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            logout = await wa_logout(client_data)
            if logout == True:
                await wa_repo.update(
                    client_data.id, phone = 'not authorized',
                    status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id']
                )
                await call.message.answer('Аккаунт успешно разлогинен', reply_markup=MAIN_MARKUP)
            else:
                await call.message.answer(
                    'Что-то пошло не так. Попробуйте еще раз',
                    reply_markup=cancel_markup()
                )
        else:
            await call.message.answer(f'Статус аккаунта: {wa_acc_state}', reply_markup=MAIN_MARKUP)
    except Exception as err:
        LOGGER.error(err)


async def WA_reboot(call: types.CallbackQuery):
    try:
        wa_repo = get_wa_client_repo()
        client_id = call.data.split(':')[-1]
        client_data = await wa_repo.get_by_id(client_id)
        wa_acc_state = await wa_check_state(client_data)
        if wa_acc_state == 'authorized':
            reboot = await wa_reboot(client_data)
            if reboot == True:
                await call.message.answer('Аккаунт успешно перезапущен', reply_markup=MAIN_MARKUP)
            else:
                await call.message.answer(
                    'Что-то пошло не так. Попробуйте еще раз',
                    reply_markup=cancel_markup()
                )
        else:
            await call.message.answer(f'Статус аккаунта: {wa_acc_state}', reply_markup=MAIN_MARKUP)
    except Exception as err:
        LOGGER.error(err)


async def WA_mailing(message: types.Message):
    await message.answer(
        'Пришилите файл в формате "xlsx", столбец с номерами телефонов должен называться "phone"',
        reply_markup=cancel_markup()
    )
    await GlobalState.wa_mailing_file.set()


async def WA_mailing_message(message: types.Message, state: FSMContext):
    try:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        await bot.download_file(file_path, f"./wa_mailing_contacts/wa_{message.from_user.id}.xlsx")
        phones, count_phones = await WA_xlsx_search('phone', message.from_user.id)
        async with state.proxy() as data:
            data['phones'], data['count_phones'] = phones, count_phones
        path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./wa_mailing_contacts/wa_{message.chat.id}.xlsx'
        )
        # os.remove(path)
        await GlobalState.wa_mailing_message.set()
        await message.answer(f'Найдено {count_phones} номеров для рассылки')
        await message.answer('Напишите текст для отправки', reply_markup=cancel_markup())
    except Exception as err:
        LOGGER.error(err)


async def WA_mailing_info(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['wa_mailing_text'] = message.text
            count_phones = data['count_phones']
        await message.answer(
            f'Кол-во номеров телефонов для рассылки: {count_phones}\n\n'
            'текст сообщения:\n'
            f'{message.text}', 
            reply_markup=wa_save_mailing_markup()
        )
    except Exception as err:
        LOGGER.error(err)


async def WA_mailing_save(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            for_sending = data['count_phones']
            phones = data['phones']
            text = data['wa_mailing_text']
        wa_repo = get_wa_client_repo()
        await wa_repo.create_mailing(
             call.from_user.id, WA_Mailing_statuses.UNWORKING.value['id'], for_sending, text, phones
        )
        await GlobalState.admin.set()
        await call.message.answer('Рассылка успешно сохранена', reply_markup=MAIN_MARKUP)
    except Exception as err:
        LOGGER.error(err)
        await GlobalState.admin.set()
        await call.message.answer(f'Что-то пошло не так, попробуйте позже\n\n{err}', reply_markup=MAIN_MARKUP)


async def WA_mailing_start(call: types.CallbackQuery, state: FSMContext):
    try:
        mai_id = call.data.split(':')[-1]
        wa_repo = get_wa_client_repo()
        await wa_repo.mailing_update(mai_id, status_id=WA_Mailing_statuses.WORKING.value['id'])
        await wa_mailing(mai_id)
    except Exception as err:
        LOGGER.error(err)



async def set_api_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_id'] = int(message.text)
    await GlobalState.set_api_hash.set()
    await message.answer('Введите api_hash')


# @dp.message_handler(state=GlobalState.set_api_hash)
async def set_api_hash(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_hash'] = message.text
    await GlobalState.set_phone.set()
    await message.answer('Введите номер телефона в формате: +79998887766')


# @dp.message_handler(state=GlobalState.set_phone)
async def set_phone(message: types.Message, state: FSMContext):
    try:
        c_repo = get_client_repo()
        async with state.proxy() as data:
            data['phone'] = message.text
            await c_repo.create(
                work_id=CWorkes.UNWORKING.value['id'],
                status_id=CStatuses.WAITING_AUTHORIZATION.value['id'],
                proxy_status_id=CProxyStatuses.PROXY_NONE.value['id'],
                api_id=data['api_id'],
                api_hash=data['api_hash'],
                phone=data['phone']
            )
        await message.answer("Аккаунт сохранен")
        await GlobalState.admin.set()
        await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)
    except Exception as err:
        LOGGER.error(err)


# @dp.message_handler(Text(equals=Bts.GROUPS.value), state=GlobalState.admin)
async def send_chats(message: types.Message):
    try:
        client_repo = get_client_repo()
        client = await client_repo.get_by_status_id(CStatuses.AUTHORIZED.value['id'])
        if client:
            for i in range(len(client)):
                await message.answer(f"🔽Группы аккаунта: <b>{client[i][7]}</b>.", parse_mode="HTML")
                chats = await client_api.get_chats(client_data=client[i])
                if chats:
                    await sendG_chats(message, client[i], chats)
                else:
                    await message.answer(f"Групп нет. (Возможно проблема с прокси)")
        else:
            await message.answer("Нет авторизованых аккаунтов")
    except Exception as err:
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='parsing:', state=GlobalState.admin)

async def parsing(call: types.CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup(reply_markup=None)

    client_repo = get_client_repo()
    client_id, chat_id = call.data.split(':')[1:]
    client_data = await client_repo.get_by_id(client_id)
    client = await client_api.get_client(client_data)
    user_id = call.from_user.id
    members = await client_api.get_members(client, int(chat_id), user_id)
    member_repo = get_member_repo()
    await call.message.answer('Парсинг запущен!')
    new_mem_count = 0
    for mem in members:
        try:
            if mem['username'] == None:
                continue
            await member_repo.create(
                id=mem['id'],
                first_name=mem['first_name'],
                last_name=mem['last_name'],
                username=mem['username'],
                phone='',
                chat_id=mem['chat_id'],
                client_id=mem['client_id']
            )
            new_mem_count += 1
        except:
            continue
    await call.message.answer(f"Добавлено в базу <b>{new_mem_count}</b> новых пользователей", parse_mode="html")


# @dp.callback_query_handler(text_contains='inviting:', state=GlobalState.admin)
async def send_inviting_result(call: types.CallbackQuery):
    try:
        await call.answer(cache_time=60)
        await call.message.edit_reply_markup(reply_markup=None)
        chat_id = int(call.data.split(':')[-1])
        client_id = int(call.data.split(':')[-2])
        client_repo = get_client_repo()
        member_repo = get_member_repo()
        active_accs = await client_repo.get_by_status_id(CStatuses.AUTHORIZED.value['id'])
        active_accs = [acc for acc in active_accs if acc.work_id == CWorkes.UNWORKING.value['id']]
        client_api.stop_invite = False
        members = await member_repo.get_all()
        msg = await call.message.answer(f'Подготовка к отправке\nПроверка прокси...',
                                        reply_markup=get_inline_invite_stop_markup(client_id, chat_id))
        await client_api.inviting(msg,active_accs, chat_id, members)
    except Exception as err:
        LOGGER.error(err)


# @dp.callback_query_handler(text_contains='stop_inviting:', state=GlobalState.admin)
async def stop_inviting(call: types.CallbackQuery):
    client_api.stop_invite = True
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup(reply_markup=None)

async def go_to_user_main(message: types.Message):
    await message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)

# @dp.message_handler(Text(equals=Bts.GO_TO_MAIN.value), state=GlobalState.admin)
async def go_to_main(message: types.Message):
    await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)


# @dp.message_handler(Text(equals=Bts.SERVICES.value), state=GlobalState.admin)
async def ser_menu(message: types.Message):
    await message.answer('Вы в услугах', reply_markup=get_services_markup())


async def keywords_ask(message: types.Message, state: FSMContext):
    await state.set_state(GlobalState.start_ch_scrap)
    await message.answer('Напишите пять ключевых слова на русском или английском языках через '
                         'пробел максимально точно соответствующие вашей тематике/товару/услуге.'
                         'Например, если вы ищете потенциальных покупателей онлайн курсов по Excel, '
                         'то напишите: курсы Excel таблицы MicrosoftOffice powerpoint', reply_markup=cancel_markup())


async def start_chat_scraping(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_keyw'] = message.text
    await state.set_state(GlobalState.lang_choice)
    await message.answer('Выберите желаемый сегмент аудитории для поиска', reply_markup=lang_ch_markup())


@dp.message_handler(text=['Отмена', 'Вернуться в главное меню'], state=ClientState)
async def cancelClient(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)
    await state.set_state(ClientState.client)


@dp.message_handler(text=["Подключить группу", 'Подключить еще группу','Повторить попытку'],
                    state=[ClientState.client, ClientState.wait_end_add_channle,ClientState.send_client_chat,
                           ClientState.accept_client_acc])
async def send_clients_chat(mes:types.message, state: FSMContext):
    await mes.answer('Пожалуйста, добавьте наш бот (@tginv_admin_bot)  в вашу группу и выдайте ему все права администратора.',
                     reply_markup=accept_bot_markup())
    await state.set_state(ClientState.accept_bot)


@dp.message_handler(text='Подтвердить', state=ClientState.accept_bot)
async def accept_bot(mes: types.message, state: FSMContext):
    await mes.answer('Отлтчно!', reply_markup=types.ReplyKeyboardRemove())
    await mes.answer('Пришлите ссылку вашего чата ', reply_markup=cancel_markup_profile()
                     )
    await state.set_state(ClientState.send_client_chat)


@dp.message_handler(state=ClientState.send_client_chat)
async def add_acc_in_chat(mes:types.message, state: FSMContext):
    if not '/' in mes.text:
        await mes.answer("Отправьте ссылку!", reply_markup=cancel_markup_profile())
        return
    c_repo = get_client_repo()
    reserve_accs = await c_repo.get_reserve()
    clients = [await client_api.get_client(acc) for acc in reserve_accs]
    hash = list(filter(None, mes.text.split('/')))[-1].replace('+', '')
    user_id = mes.from_user.id
    fine = await client_api.add_client_in_chat(mes, clients, hash, user_id, reserve_accs, bot=bot,)
    if fine:
        await mes.answer('Отлично! Аккаунты успешно добавлены в чат!.\n'
                         'Теперь выдайте каждому аккаунту права администратора.',
                         reply_markup=accept_bot_markup())
    await state.set_state(ClientState.accept_client_acc)
        #НУЖНО БУДЕТ ДОБАВИТЬ ПРОВЕРКУ ВЫДАНЫ ЛИ ПРАВА АДМИНИСТРАТОРА АККАУНТАМ


@dp.message_handler(text='Подтвердить', state=ClientState.accept_client_acc)
async def accept_bot(mes: types.message, state: FSMContext):

    await mes.answer('Отлично! Проверка прошла успешно.\n'
                     'Ваш чат добавлен в список ваших групп для настройки инвайта.',
                     reply_markup=success_add_channel())
    await state.set_state(ClientState.wait_end_add_channle)


@dp.message_handler(text=['Управление инвайтами'],state=[ClientState.client])
async def chioce_group_set(mes: types.message, state: FSMContext):
    ch_c_repo = get_channel_client_repo()
    res = await ch_c_repo.get_channel_invite(mes.from_user.id)
    for i in res:
        await choice_chats_for_invite(mes, mes.from_user.id, i)
    await mes.answer('Выберите группу для настройки инвайта', reply_markup=cancel_markup_profile())
    await state.set_state(ClientState.choice_group_profile)


#@dp.callback_query_handlers(text_contains='invProfile:', state=ClientState.choice_group_profile)
async def send_group_info_profile(call: types.CallbackQuery, state: FSMContext):
    client_id = call.data.split(':')[-2]
    chat_id = call.data.split(':')[-1]
    await state.update_data(chat_id = chat_id, client_id = client_id)
    ch_c_repo = get_channel_client_repo()
    group = await ch_c_repo.get_group_by_id_and_userId(chat_id, client_id)

    message = f'Группа - {group[3]}\n\n' \
              f'Подключенные источники:\n\n'
    c_repo = get_source_repo()
    ch_repo = get_channel_repo()

    ch = await c_repo.get_source_by_channel_id(chat_id)
    if ch:
        k = 1
        for i in ch:
            userName = await ch_repo.get_username_by_id(i[2])
            if not userName:
                userName = i[2]

            message += f'{k}. ' \
                       f'{await ch_repo.get_name_by_id_or_username(i[2])} ' \
                       f'@{userName} ' \
                       f'{await ch_repo.get_participants_count_by_id(i[2])}\n'
            k+=1
    else:
        message += 'Нет'
    count_inv = await ch_c_repo.get_count_success_inv(chat_id)
    message+=f'\n' \
             f'Доступных: ХХХ\n' \
             f'Оплаченных: ХХХ\n' \
             f'\n' \
             f'Состоявшихся инвайтов: {count_inv}\n' \
             f'Статус: {"Вкл." if group[4] == 1 else "Выкл."}'

    await call.message.answer(message, reply_markup = chat_profile_card(group[4]))
    await state.set_state(ClientState.wait_setting_group)
    await state.update_data(id_chat=chat_id)


@dp.message_handler(text='Вкл. инвайт', state=ClientState.wait_setting_group)
async def ON_invite_profile(mes: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data['chat_id']
    client_id = data['client_id']
    client_repo = get_client_repo()
    member_repo = get_member_repo()
    ch_repo = get_channel_repo()
    ch_c_repo = get_channel_client_repo()
    user_id = mes.from_user.id
    active_accs = await client_repo.get_by_user_id_and_chat_id(user_id, chat_id)
    # active_accs = [acc for acc in active_accs if acc.work_id == CWorkes.UNWORKING.value['id']]
    client_api.stop_invite_prof = False

    s_repo = get_source_repo()
    list_sources = await s_repo.get_source_id_by_channel_id(chat_id)
    print(list_sources)
    members = []
    for soirce_id in list_sources:
        print(soirce_id)
        if soirce_id.isdigit():
            members.extend(list(await member_repo.get_all_by_id_source(soirce_id)))
        else:
            members.extend(list(await member_repo.get_all_by_id_source(await ch_repo.get_id_by_username(soirce_id))))
    await ch_c_repo.set_invite_ON_status(chat_id)
    group = await ch_c_repo.get_group_by_id_and_userId(chat_id, client_id)
    msg = await mes.answer(f'Начинаем отправлять инвайты',
                                    reply_markup=chat_profile_card(group[4]))
    await state.set_state(ClientState.wait_setting_group)
    #await client_api.inviting(msg, active_accs, chat_id, client_id, members)
    await client_api.pre_inviting(msg, active_accs, chat_id, members[:300])


@dp.message_handler(text='Выкл. инвайт', state=ClientState.wait_setting_group)
async def OFF_invite_profile(mes: types.Message, state: FSMContext):
    data = await state.get_data()
    ch_c_repo = get_channel_client_repo()
    chat_id = data['chat_id']
    client_id = data['client_id']
    client_api.stop_invite_prof = True
    await ch_c_repo.set_invite_OFF_status(chat_id)
    group = await ch_c_repo.get_group_by_id_and_userId(chat_id, client_id)
    await mes.answer('Инвайт был успешно отключен!', reply_markup=chat_profile_card(group[4]))


@dp.message_handler(text='Добавить источник', state=ClientState.wait_setting_group)
async def choice_add_source(mes: types.Message, state:FSMContext):
    await mes.answer('Выберите споcоб добавления источника', reply_markup=choice_add_sour())
    await state.set_state(ClientState.choice_source_add)


@dp.message_handler(text='Отключить источник', state=ClientState.wait_setting_group)
async def choice_delete_source(mes: types.Message, state:FSMContext):
    c_repo = get_source_repo()
    ch_repo = get_channel_repo()
    id = await state.get_data()
    chat_id = id['id_chat']
    ch = await c_repo.get_source_by_channel_id(chat_id)
    if ch:
        k = 1
        for i in ch:
            userName = await ch_repo.get_username_by_id(i[2])
            if not userName:
                userName = i[2]
            await mes.answer(f'{k}. '
                             f'{await ch_repo.get_name_by_id_or_username(i[2])} '
                             f'@{userName} '
                             f'{await ch_repo.get_participants_count_by_id(i[2])}\n',
                             reply_markup=get_inline_del_source(i[1], i[2]))
            k += 1
    await mes.answer('Выберите источник для отключения', reply_markup=cancel_markup_profile())
    await state.finish()
    await state.set_state(ClientState.choice_source_del)

#@dp.callback_query_handlers(text_contains='delSource:', state=ClientState.choice_source_del)
async def delete_source(call:types.CallbackQuery, state:FSMContext):
    id_channel = call.data.split(':')[-2]
    id_source = call.data.split(':')[-1]
    s_repo = get_source_repo()
    await s_repo.clear_group_source(id_channel, id_source)
    ch_repo = get_channel_repo()
    await call.message.answer(f'Отключение группы "{await ch_repo.get_name_by_id_or_username(id_source) }" прошло успешно.')
    await state.finish()
    await call.message.answer('Вы в главном меню', reply_markup=MAIN_CL_MARKUP)
    await state.set_state(ClientState.client)


@dp.message_handler(text=['Настроить инвайт в чат', 'Настроить инвайт', 'Повторить попытку', 'Через ссылку на чат'],
                    state=[ClientState.wait_end_add_channle, ClientState.wait_end_link_pars,
                           ClientState.client, ClientState.choice_source_add, ])
async def start_set_inviting(mes: types.message, state: FSMContext):
    await mes.answer('Отправь ссылку на открытый чат с твоей целевой аудиторией', reply_markup=cancel_markup_profile())
    await state.set_state(ClientState.wait_link_pars)


@dp.message_handler(state=[ClientState.wait_link_pars])
async def pars_channel(mes: types.message, state: FSMContext):
    if not '/' in mes.text:
        await mes.answer("Отправьте ссылку!", reply_markup=cancel_markup_profile())
        return
    c_repo = get_client_repo()
    mem_repo = get_member_repo()
    r_repo = get_report_repo()
    active_accs = await c_repo.get_by_user_id(mes.from_user.id)
    await mes.answer('Проверка аккаутов')
    active_accs = await client_api.check_ban_accs(active_accs)
    print(active_accs)
    if not active_accs:
        print('Нет активных аккаунтов!')
        await mes.answer('К сожалению, у вас нет активных аккаунтов! \nОбратитесь пожалуйста в поддержку', reply_markup=call_employee())
        return
    await mes.answer('Проверка чата')
    client = await client_api.get_client(active_accs[0])
    hash = list(filter(None, mes.text.split('/')))[-1].replace('+', '')
    ent = await client.get_entity(hash)
    await state.update_data(id_source=ent.id)
    user_id = mes.from_user.id
    members = await client_api.get_members(client,ent.id, user_id)
    if members is None:
        await mes.answer('Ошибка проверки чата! \nСкорее всего, в этом чате подписчики скрыты!',
                         reply_markup=error_pars_chat())
        await state.set_state(ClientState.wait_end_link_pars)
        return
    new_mem_count = 0
    for mem in members:
        try:
            user = await mem_repo.get_by_id(mem['id'])
            if not user:
                if mem['username'] == None:
                    continue
                await mem_repo.create(
                    id=mem['id'],
                    first_name=mem['first_name'],
                    last_name=mem['last_name'],
                    username=mem['username'],
                    phone = '',
                    chat_id=mem['chat_id'],
                    client_id=mem['client_id']
                )
                new_mem_count += 1
                await r_repo.add_new_orders(1)
        except:
            continue
    ch_c_repo = get_channel_client_repo()
    res = await ch_c_repo.get_channel_invite(mes.from_user.id)
    await state.update_data(res=res)
    await state.update_data(user_id=mes.from_user.id)
    if not res:
        await mes.answer('Группы для инвайта не настроены! \nПерейдите в профиль и добавьте свои группы.',
                         reply_markup = go_to_profile())
        await state.set_state(ClientState.client)
        return
    for i in res:
        await choice_chats_for_invite(mes, mes.from_user.id, i)
    mem_count = await mem_repo.get_all_by_id_source(ent.id)
    await mes.answer(f'Проверка чата прошла успешно! Доступных пользователей для инвайта {len(mem_count)} человек.\n'
                     f'Выбери группу в которую будет происходить инвайт', reply_markup = cancel_markup_profile())
    ch_repo = get_channel_repo()
    await ch_repo.add_new_channel_by_pars(ent.id, ent.title, ent.access_hash, ent.username, new_mem_count)
    await state.set_state(ClientState.choice_group_pars)


@dp.message_handler(text= 'Изменить группу',state=ClientState.dop_state)
async def dop_state(mes:types.message, state:FSMContext):
    res = await state.get_data()
    for i in res['res']:
        await choice_chats_for_invite(mes, mes.from_user.id, i)
    s_repo = get_source_repo()
    await s_repo.clear_group_source(res['chat_id'], res['id_source'])
    await mes.answer(f'Выбери группу в которую будет происходить инвайт', reply_markup=cancel_markup_profile())
    await state.set_state(ClientState.choice_group_pars)


#@dp.callback_query_handlers(text_contains='invProfile:', state=ClientState.choice_group_pars)
async def send_group_info_pars (call: types.CallbackQuery, state: FSMContext):
    client_id = call.data.split(':')[-2]
    chat_id = call.data.split(':')[-1]
    print(chat_id)
    ch_c_repo = get_channel_client_repo()
    group = await ch_c_repo.get_group_by_id_and_userId(chat_id, client_id)
    s_repo = get_source_repo()

    all_sourcees = await s_repo.get_list_all_sourses()
    sources = await s_repo.get_source_by_channel_id(chat_id)
    source = await state.get_data()
    id_source = source['id_source']
    if (f'{chat_id}', id_source) in all_sourcees:
        await call.message.answer(f'Эта группа уже добавлена для {group[3]}')
        return

    message = f'Выбрана группа "{group[3]}"\n\n' \
              f'Инвайт в группу будет осуществляться из расчёта 300 человек в день для избежания блокировки телеграмм вашей группы.\n' \
              f'* Обязательно проверьте наличие количество оплаченных инвайтов в личном кабинете.'
    await call.message.answer(message, reply_markup=get_inline_chats_pars(client_id, chat_id))
    await s_repo.add_source_channel(f'{chat_id}', id_source)
    await state.update_data(chat_id = f'{chat_id}')
    await call.message.answer('Выберите действие', reply_markup=chat_pars_card())
    await state.set_state(ClientState.dop_state)


#@dp.callback_query_handlers(text_contains='invProf:', state=ClientState.dop_state)
async def start_inv_settings(call: types.CallbackQuery, state: FSMContext):
    client_id = call.data.split(':')[-2]
    chat_id = call.data.split(':')[-1]
    client_repo = get_client_repo()
    member_repo = get_member_repo()
    ch_c_repo = get_channel_client_repo()
    ch_repo = get_channel_repo()
    data = await state.get_data()
    user_id = data['user_id']
    active_accs = await client_repo.get_by_user_id_and_chat_id(str(user_id), str(chat_id))
    # active_accs = [acc for acc in active_accs if acc.work_id == CWorkes.UNWORKING.value['id']]
    client_api.stop_invite_prof = False

    s_repo = get_source_repo()
    list_sources = await s_repo.get_source_id_by_channel_id(chat_id)
    print(list_sources)
    members = []
    for soirce_id in list_sources:
        print(soirce_id)
        if soirce_id.isdigit():
            members.extend(list(await member_repo.get_all_by_id_source(soirce_id)))
        else:
            members.extend(list(await member_repo.get_all_by_id_source(await ch_repo.get_id_by_username(soirce_id))))

    await ch_c_repo.set_invite_ON_status(chat_id)
    msg = await call.message.edit_text(f'Начинаем отправлять инвайты',
                           reply_markup=get_inline_invite_stop_markup(client_id, chat_id))
    await state.set_state(ClientState.dop_state)
    # await client_api.inviting(msg, active_accs, chat_id, client_id, members)
    await client_api.pre_inviting(msg, active_accs, chat_id, members[:300])


#@dp.callback_query_handlers(text_contains='stop_inviting:', state=ClientState.dop_state)
async def stop_inv_settings(call: types.CallbackQuery, state: FSMContext):
    ch_c_repo = get_channel_client_repo()
    client_id = call.data.split(':')[-2]
    chat_id = call.data.split(':')[-1]
    client_api.stop_invite_prof = True
    await ch_c_repo.set_invite_OFF_status(chat_id)
    await call.message.edit_text('Инвайт был успешно отключен!', reply_markup=get_inline_chats_pars(client_id, chat_id))
    await state.set_state(ClientState.dop_state)


# @dp.message_handler(Text(equals='Поиск открытых чатов'), state=GlobalState.admin)
async def ser_search_open_chat(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    channe_repo = get_channel_repo()
    async with state.proxy() as data:
        data['lang'] = (call.data).split(':')[1]
    client_repo = get_client_repo()
    try:
        client_datas = await client_repo.get_by_status_and_work_id(
            status_id=CStatuses.RESERVE.value['id'], work_id=CWorkes.UNWORKING.value['id']
        )
    except:
        client_datas = await client_repo.get_by_status_and_work_id(
            status_id=CStatuses.AUTHORIZED.value['id'], work_id=CWorkes.UNWORKING.value['id']
        ) 
        LOGGER.info('Взяты акки AUTHORIZED')
    try:
        client_data = random.choice(client_datas)
        async with state.proxy() as data:
            data['client_scrap_data'] = client_data
            await client_repo.update(data['client_scrap_data'].id, work_id=CWorkes.PARSING.value['id'])
            ans = await client_api.search_by_keyw(
                call.message,
                client_data, data['user_keyw'], data['lang']
            )
            groups = await channe_repo.get_channels_by_username(str(call.from_user.id), ans)
            data['groups'] = groups
            await client_repo.update(data['client_scrap_data'].id, work_id=CWorkes.UNWORKING.value['id'])
            await call.message.answer(
                'Результаты поиска\n\n'
                'Поиск чатов прошел успешно!\n'
                f'Сформирован список из {len(groups)} самых популярных чатов в соответствие с ключевыми словами.\n\n'
                'Стоимость поиска - 100 р',

                reply_markup=inline_pay_markup()
            )
    except Exception as er:
        LOGGER.critical(er)
        try:
            async with state.proxy() as data:
                await client_repo.update(data['client_scrap_data'].id, work_id=CWorkes.UNWORKING.value['id'])
        except Exception as er:
            LOGGER.critical(er)
        await state.set_state(ClientState.client)
        await call.message.answer('К сожалению, поиск сейчас не возможен, вернитесь в главное меню', reply_markup=go_to_main_markup())


async def group_list(call: types.CallbackQuery, state: FSMContext):
    try:
        ch_repo = get_channel_repo()
        async with state.proxy() as data:
            groups = data['groups']
            groups_id = []
            result_dict = {}
            num = 1
            for i in groups:
                result_dict[num] = i.username, i.participants_count
                num += 1
                groups_id.append(i.id)
            data['result'] = result_dict
            keyw = data['user_keyw']
        await ch_repo.add_new_search(user_id=call.from_user.id,keyw=keyw, groups=groups_id)
        mes = 'Результаты поиска:\n\n'
        for i in result_dict:
            mes = mes + f'{i}. @{result_dict[i][0]}  ({result_dict[i][1]} участников)\n\n'
        await call.message.answer(mes)
        await state.set_state(GlobalState.group_choice)
        await call.message.answer('Выберите подходящие для вас чаты с вашей целевой аудиторий\n\n'
                                  'Укажите их номера через пробел.\n'
                                  'Например: 1 2 3', reply_markup=inline_no_groups__markup())
    except Exception as err:
        LOGGER.error(err)


async def no_groups(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('Расскажите, что вас не устроило в результатах поиска')
    await state.set_state(ClientState.mark_nps)


async def parse_nps_ask(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['nps_comment'] = message.text
    await state.set_state(ClientState.client)
    await message.answer(
        'Оцените качество обслуживания по шкале от 1 до 5', 
        reply_markup=nps_markup('parse')
    )


async def nps_save(call: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            comment = data['nps_comment']
        user_repo = get_user_repo()
        await user_repo.create_nps(
            user_id=str(call.from_user.id),
            service=call.data.split(':')[1],
            username=call.from_user.username or '',
            mark=call.data.split(':')[2],
            comment=comment
        )
        await call.message.delete()
        await call.message.answer('Спасибо!', reply_markup=MAIN_CL_MARKUP)
    except Exception as err:
        LOGGER.error(err)


async def group_choice(message: types.Message, state: FSMContext):
    await state.update_data(user_id=message.from_user.id)
    groups = []
    try:
        async with state.proxy() as data:
            for m in message.text.split(' '):
                groups.append(data['result'][int(m)][0])
            data['groups'] = groups
        mes = 'Вы выбрали группы: \n'
        for gr in groups:
            mes = mes + f'@{gr}\n'
        await message.answer(mes, reply_markup=inline_apply_group_ch_markup())
    except Exception as err:
        LOGGER.error(err)
        await message.answer('Такого номера в списке нет\nУкажите корректные номера через пробел')


async def other_chats(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.set_state(GlobalState.group_choice)
    await call.message.answer('Укажите номера чатов')


async def parse_or_invite(call: types.CallbackQuery, state:FSMContext):
    await call.message.delete()
    await call.message.answer('Выберите вариант действий', reply_markup=inline_scrap_or_invite_markup())
    await state.set_state()

# @dp.callback_query_handlers(text=['invite'],state=[ClientState.client])
async def chioce_group_p_o_i(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    c_repo = get_client_repo()
    mem_repo = get_member_repo()
    r_repo = get_report_repo()
    active_accs = await c_repo.get_by_user_id(data['user_id'])
    await call.message.answer('Проверка аккаутов')
    active_accs = await client_api.check_ban_accs(active_accs)
    print(active_accs)
    if not active_accs:
        print('Нет активных аккаунтов!')
        await call.message.answer('К сожалению, у вас нет активных аккаунтов! \nОбратитесь пожалуйста в поддержку',
                         reply_markup=call_employee())
        return
    await call.message.answer('Проверка чата')
    client = await client_api.get_client(active_accs[0])
    for i in data['groups']:
        ent = await client.get_entity(i)
        await state.update_data(id_source=ent.id)
        members = await client_api.get_members(client, ent.id, data['user_id'])
        if members is None:
            await call.message.answer('Ошибка проверки чата! \nСкорее всего, в этом чате подписчики скрыты!',
                             reply_markup=error_pars_chat())
            await state.set_state(ClientState.wait_end_link_pars)
            return
        new_mem_count = 0
        for mem in members:
            try:
                user = await mem_repo.get_by_id(mem['id'])
                if not user:
                    if mem['username'] == None:
                        continue
                    await mem_repo.create(
                        id=mem['id'],
                        first_name=mem['first_name'],
                        last_name=mem['last_name'],
                        username=mem['username'],
                        phone='',
                        chat_id=mem['chat_id'],
                        client_id=mem['client_id']
                    )
                    new_mem_count += 1
                    await r_repo.add_new_orders(1)
            except:
                continue
    ch_c_repo = get_channel_client_repo()
    res = await ch_c_repo.get_channel_invite(data['user_id'])
    for i in res:
        await choice_chats_for_invite_p_o_i(call.message, data['user_id'], i)
    await call.message.answer('Выберите группу для настройки инвайта', reply_markup=cancel_markup_profile())
    await state.set_state(ClientState.add_group_to_sources)

#@dp.callback_query_handlers(text_contains=["invPoI:"], state = ClientState.add_group_to_sources)
async def invPoI(call: types.CallbackQuery, state: FSMContext):
    client_id = call.data.split(':')[-2]
    chat_id = call.data.split(':')[-1]
    ch_c_repo = get_channel_client_repo()
    group = await ch_c_repo.get_group_by_id_and_userId(chat_id, client_id)
    s_repo = get_source_repo()
    all_sourcees = await s_repo.get_list_all_sourses()
    print('Все источники:',all_sourcees)
    sources = await s_repo.get_source_by_channel_id(chat_id)
    data = await state.get_data()
    id_source = data['groups']
    print('id_source:', id_source)
    flag = True
    for i in id_source:
        if (f'{chat_id}', i) in all_sourcees:
            await call.message.answer(f'Эта группа уже добавлена для {group[3]}')
            continue
        flag = False
    if flag:
        await call.message.answer(f'Все группы уже были добавлены ранее!')
        return

    message = f'Выбрана группа "{group[3]}"\n\n' \
              f'Инвайт в группу будет осуществляться из расчёта 300 человек в день для избежания блокировки телеграмм вашей группы.\n' \
              f'* Обязательно проверьте наличие количество оплаченных инвайтов в личном кабинете.'
    await call.message.answer(message, reply_markup=get_inline_chats_pars(client_id, chat_id))
    for i in id_source:
        await s_repo.add_source_channel(f'{chat_id}', i)
    await state.set_state(ClientState.dop_state)



async def numbers_scrap(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        client_repo = get_client_repo()
        async with state.proxy() as data:
            groups = data['groups']
            mem = await client_api.mem_scraping(
                call.message, data['client_scrap_data'], data['lang'], groups, call.from_user.id
            )
            await client_repo.update(data['client_scrap_data'].id, work_id=CWorkes.UNWORKING.value['id'])
        await call.message.answer(
            f'Готово!\nКол-во полученных пользователей: {mem}', reply_markup=parse_start_markup()
        )
        await state.set_state(ClientState.client)
    except Exception as err:
        LOGGER.error(err)


async def send_file(message: types.Message, state: FSMContext):
    try:
        await message.answer('Подготовка файла...')
        file = open(f'./members/members_contacts_{message.chat.id}.xlsx', 'rb')
        await bot.send_document(message.chat.id, file, caption='Файл готов!', reply_markup=go_to_main_markup())
        file.close()
        path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./members/members_contacts_{message.chat.id}.xlsx'
        )
        os.remove(path)
    except Exception as err:
        LOGGER.error(err)


async def search_history(message: types.Message, state: FSMContext):
    try:
        history = await client_api.send_search_history(message.from_user.id)
        if history != 0:
            file = open(f'./history/search_history_{message.chat.id}.xlsx', 'rb')
            await bot.send_document(message.chat.id, file, caption='Файл готов!', reply_markup=go_to_main_markup())
            file.close()
            path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), f'./history/search_history_{message.chat.id}.xlsx'
            )
            os.remove(path)
        else:
            await message.answer('Ваша история поиска пуста, перейдите в меню "Поиск открытых чатов"')
    except Exception as err:
        LOGGER.error(err)
        await message.answer('Ваша история поиска пуста, перейдите в меню "Поиск открытых чатов"')


async def antispam(message: types.Message, state: FSMContext):
    user_repo = get_user_repo()
    u_name = await bot.get_me()
    await message.answer(
        f'Чтобы бот(@{u_name.username}) ловил весь спам, рекламу и мат - сделайте его админом вашей группы,'
        ' после этого он автоматически заработает. Если хотите добавить дополнительные слова, на которые '
        'будет реагировать бот - нажмите "Добавить триггеры"', reply_markup=add_triger_markup()
    )
    triggers = await user_repo.get_triggers_by_id(message.from_user.id)
    if len(triggers):
        await message.answer('Подключенные группы:')
        for tr in triggers:
            await message.answer(
                f'group id: {tr.group_id}\n'
                f'слова триггеры: {tr.words}'
            )


async def add_triggers(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(GlobalState.add_triggers)
    await call.message.answer(
        'Перешлите мне ссылку на вашу группу, если группа закрытая, то пригласительную ссылку',
        reply_markup=cancel_markup()
    )


async def get_chat_id(message: types.Message, state: FSMContext):
    try:
        client_repo = get_client_repo()
        try:
            client_datas = await client_repo.get_by_status_and_work_id(
                status_id=CStatuses.RESERVE.value['id'], work_id=CWorkes.UNWORKING.value['id']
            )
        except:
            client_datas = await client_repo.get_by_status_and_work_id(
                status_id=CStatuses.AUTHORIZED.value['id'], work_id=CWorkes.UNWORKING.value['id']
            ) 
            LOGGER.info('Взяты акки AUTHORIZED')
        client_data = random.choice(client_datas)
        hash = list(filter(None, message.text.split('/')))[-1].replace('+', '')
        group_id = await client_api.get_user_group_id(client_data, message.text, hash)
        async with state.proxy() as data:
            data['group_id'] = str(group_id)
        await state.set_state(GlobalState.save_triggers)
        await message.answer('Введите слова через пробел')
    except Exception as err:
        LOGGER.error(err)
        await message.answer('Что-то не так с ссылкой, попробуйте еще раз')


async def save_triggers(message: types.Message, state: FSMContext):
    user_repo = get_user_repo()
    async with state.proxy() as data:
        try:
            await user_repo.create_triggers(data['group_id'], str(message.from_user.id), message.text)
        except:
            await user_repo.bw_update(group_id=data['group_id'], user_id = str(message.from_user.id), words = message.text)
    user = await user_repo.get_by_id(message.from_user.id)
    await message.answer('Данные успешно сохранены!')
    if user.role_id == 2:
        await state.set_state(ClientState.client)
        await message.answer('Вы ы главном меню', reply_markup=MAIN_CL_MARKUP)
    elif user.role_id == 10:
        await state.set_state(GlobalState.admin)
        await message.answer('Вы ы главном меню', reply_markup=MAIN_MARKUP)



@dp.message_handler(IsGroup())
async def check_message(message: types.Message):
    user_repo = get_user_repo()
    triggers = await user_repo.get_triggers_by_group_id(message.chat.id)
    detector = is_dirt()
    text = message.text.lower().replace(' ', '')
    print(text)
    if re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', message.text):
        await message.delete()
        await bot.send_message(message.chat.id, 'Нельзя слать ссылки!!!')
    if detector(text):
        await message.bot.ban_chat_member(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            until_date=datetime.now()+timedelta(minutes=1)
        )
        await message.answer(f'Мат запрещен. Пользователь {message.from_user.username} получает бан!')
        await message.delete()
    if triggers:
        text = message.text
        checklist = set((triggers.words).split(' '))
        common_words = set(text.split()) & checklist
        if len(common_words):
            await message.answer(f'Ваше сообщение содержит запрещенное слово')
            await message.delete()


async def test(message: types.Message, state: FSMContext):
    client_repo = get_client_repo()
    client_data = await client_repo.get_by_id('2')
    await client_api.send_phone_hash_code(client_data)


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(deleteServiceMes, content_types=['new_chat_members', 'left_chat_member'])

    dp.register_message_handler(start, commands='start', state=None)

    dp.register_message_handler(send_wa_accounts, Text(equals=Bts.WA_ACCS.value), state=GlobalState.admin)
    dp.register_message_handler(send_accounts, Text(equals=Bts.ACCOUNTS.value), state=GlobalState.admin)
    dp.register_message_handler(reg_menu_ask_phone, Text(equals=ClientBts.ACCEPT_POLICY.value))
    dp.register_message_handler(que_and_ans, Text(equals=ClientBts.QUE_AND_ANS.value), state='*')
    dp.register_message_handler(reg_menu_send_phone_code, content_types=types.ContentType.CONTACT, state=ClientState.send_phone_code)
    dp.register_message_handler(replenish_balance, Text(equals=ClientBts.REPLENISH_BALANCE.value), state=ClientState.client)
    dp.register_callback_query_handler(amount_ask, text_contains='cur:', state='*')
    dp.register_message_handler(payment_confirmation, state=ClientState.paym_confirm)
    dp.register_callback_query_handler(reg_menu_sphere_ask, text_contains='sphere:', state=ClientState.about_1)
    dp.register_callback_query_handler(reg_menu_bot_usage, text_contains='work:', state=ClientState.about_2)
    dp.register_callback_query_handler(reg_menu_save_answers, text_contains='usage:', state=ClientState.about_3)
    dp.register_callback_query_handler(add_triggers, text_contains='triggers', state='*')
    dp.register_message_handler(user_profile, Text(equals=[ClientBts.PROFILE.value, 'Перейти в профиль']), state=ClientState.client)
    dp.register_message_handler(ehco_add_account, Text(equals=Bts.ADD_ACCOUNT.value), state=GlobalState.admin)
    dp.register_message_handler(WA_echo_add_account, Text(equals=Bts.ADD_WA_ACCOUNT.value), state=GlobalState.admin)
    dp.register_message_handler(send_wa_mailing, Text(equals=Bts.MAILING.value), state=GlobalState.admin)
    dp.register_message_handler(cancel, Text(equals=Bts.CANCEL.value, ignore_case=True), state='*')  # любой кроме admin
    dp.register_message_handler(WA_set_id_instance, state=GlobalState.wa_instance)
    dp.register_message_handler(WA_set_api_token, state=GlobalState.wa_token)
    dp.register_message_handler(WA_mailing, Text(equals=Bts.ADD_WA_MAILING.value), state=GlobalState.admin)
    dp.register_message_handler(WA_mailing_message, content_types=[types.ContentType.DOCUMENT, ], state=GlobalState.wa_mailing_file)
    dp.register_message_handler(WA_mailing_info, state=GlobalState.wa_mailing_message)
    dp.register_callback_query_handler(WA_mailing_save, text_contains='wa_client:save_mailing', state=GlobalState.wa_mailing_message)
    dp.register_callback_query_handler(WA_mailing_start, text_contains='wa_mailing:mailing_start:', state=GlobalState.admin)
    dp.register_callback_query_handler(WA_logout, text_contains='wa_client:walogout:', state=GlobalState.admin)
    dp.register_callback_query_handler(WA_reboot, text_contains='wa_client:wareboot:', state=GlobalState.admin)
    dp.register_message_handler(set_api_id, state=GlobalState.set_api_id)
    dp.register_message_handler(set_api_hash, state=GlobalState.set_api_hash)
    dp.register_message_handler(set_phone, state=GlobalState.set_phone)
    dp.register_message_handler(get_chat_id, state=GlobalState.add_triggers)
    dp.register_callback_query_handler(account_delete, text_contains='client:delete', state=GlobalState.admin)
    dp.register_callback_query_handler(send_authorization_code, text_contains='client:authorization',
                                       state=GlobalState.admin)
    dp.register_message_handler(authorization, state=GlobalState.auth_acc)
    dp.register_callback_query_handler(waitProxy, text_contains='client:addProxy', state=GlobalState.admin)
    dp.register_callback_query_handler(parse_or_invite, text_contains='apply', state='*')
    dp.register_callback_query_handler(chioce_group_p_o_i, text=['invite'],state='*')
    dp.register_callback_query_handler(invPoI,  text_contains=["invPoI:"], state=ClientState.add_group_to_sources)
    dp.register_callback_query_handler(numbers_scrap, text_contains='numberscrap', state='*')
    dp.register_message_handler(addProxy, state=GlobalState.add_proxy)
    dp.register_callback_query_handler(proxyON, text_contains='client:proxyON', state=GlobalState.admin)
    dp.register_callback_query_handler(wa_auth, text_contains='wa_client:waauthorization:', state=GlobalState.admin)
    dp.register_callback_query_handler(wa_check_auth, text_contains='wa_client:qrcheck:', state=GlobalState.wa_send_qr)
    dp.register_callback_query_handler(proxyOFF, text_contains='client:proxyOFF', state=GlobalState.admin)
    dp.register_callback_query_handler(proxyDELETE, text_contains='client:ProxyDelete', state=GlobalState.admin)
    dp.register_callback_query_handler(group_list, text_contains='pay', state='*')
    dp.register_message_handler(send_chats, Text(equals=Bts.GROUPS.value), state=GlobalState.admin)
    dp.register_callback_query_handler(parsing, text_contains='parsing:', state=GlobalState.admin)
    dp.register_callback_query_handler(stop_inviting, text_contains='stop_inviting:', state=GlobalState.admin)
    dp.register_callback_query_handler(send_inviting_result, text_contains='inviting:', state=GlobalState.admin)
    dp.register_message_handler(go_to_main, Text(equals=Bts.GO_TO_MAIN.value), state=GlobalState.admin)
    dp.register_message_handler(go_to_user_main, Text(equals=ClientBts.GO_TO_MAIN.value), state=ClientState.client)
    dp.register_message_handler(ser_menu, Text(equals=Bts.SERVICES.value), state=GlobalState.admin)
    dp.register_message_handler(keywords_ask, Text(equals=ClientBts.SEARCH_OP_CHATS.value), state='*')
    dp.register_message_handler(start_chat_scraping, state=GlobalState.start_ch_scrap)
    dp.register_callback_query_handler(ser_search_open_chat, text_contains='segment:', state=GlobalState.lang_choice)
    dp.register_callback_query_handler(other_chats, text_contains='other', state=GlobalState.group_choice)
    dp.register_callback_query_handler(no_groups, text_contains='nogroups', state=GlobalState.group_choice)
    dp.register_message_handler(parse_nps_ask, state=ClientState.mark_nps)
    dp.register_callback_query_handler(nps_save, text_contains='nps:', state='*')
    dp.register_callback_query_handler(other_chats, text_contains='other', state=GlobalState.group_choice)
    dp.register_callback_query_handler(no_groups, text_contains='nogroups', state=GlobalState.group_choice)
    dp.register_message_handler(parse_nps_ask, state=ClientState.mark_nps)
    dp.register_callback_query_handler(nps_save, text_contains='nps:', state='*')
    dp.register_message_handler(search_history, Text(equals=ClientBts.SEARCH_HISTORY.value), state='*')
    dp.register_callback_query_handler(send_group_info_profile, text_contains='invProfile:', state=ClientState.choice_group_profile)
    dp.register_callback_query_handler(send_group_info_pars, text_contains='invProfile:', state=ClientState.choice_group_pars)
    dp.register_callback_query_handler(start_inv_settings, text_contains='invProf:', state=ClientState.dop_state)
    dp.register_callback_query_handler(stop_inv_settings,text_contains='stop_inviting:', state=ClientState.dop_state)
    dp.register_callback_query_handler(delete_source,text_contains='delSource:', state=ClientState.choice_source_del)
    dp.register_message_handler(group_choice, state=GlobalState.group_choice)
    dp.register_message_handler(send_file, Text(equals=Bts.PARSE_START.value), state=ClientState.client)
    dp.register_message_handler(antispam, Text(equals=Bts.ANTI_SPAM.value), state='*')
    dp.register_message_handler(save_triggers, state=GlobalState.save_triggers)


register_handlers_admin(dp)


async def on_shutdown(dp):
    """Отключаемся от БД при выключении бота."""
    try:
        await database.disconnect()
        LOGGER.info('DB disconnected')
    except Exception as err:
        LOGGER.error(err)


if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
