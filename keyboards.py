from typing import Tuple

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup, WebAppInfo)
from aiogram.types.menu_button import MenuButtonWebApp
from enums import CProxyStatuses, CStatuses, WA_CStatuses, WA_Mailing_statuses

def get_content_markup(msg, data):
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton(msg, callback_data=data)
    )
    return markup


def wa_save_correct_phones_markup(mai_id):
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Добавить в рассылку', callback_data=f'wa_client:save_correct_phones:{mai_id}')
    )
    return markup

def wa_save_mailing_markup():
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Сохранить', callback_data=f'wa_client:save_mailing')
    )
    return markup

def wa_check_qr_markup(client_data):
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Проверить авторизацию', callback_data=f'wa_client:qrcheck:{client_data.id}')
    )
    return markup

def support_markup():
    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Задать вопрос', url='http://t.me/inviters_support_bot')
    )
    return markup

def nps_markup(service):
    markup = InlineKeyboardMarkup(row_width=5).add(
        InlineKeyboardButton(text='1', callback_data=f'nps:{service}:1'),
        InlineKeyboardButton(text='2', callback_data=f'nps:{service}:2'),
        InlineKeyboardButton(text='3', callback_data=f'nps:{service}:3'),
        InlineKeyboardButton(text='4', callback_data=f'nps:{service}:4'),
        InlineKeyboardButton(text='5', callback_data=f'nps:{service}:5')
    )
    return markup


def cancel_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton('отмена')
    )
    return markup

def send_contact_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton('Отправить свой контакт ☎️', request_contact=True)
    )
    return markup

def inline_scrap_or_invite_markup():
    keyboard = [
        [InlineKeyboardButton(text='Парс номеров', callback_data='numberscrap')],
        [InlineKeyboardButton(text='Инвайтит участников', callback_data='invite')]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def inline_apply_group_ch_markup():
    keyboard = [
        [InlineKeyboardButton(text='Подтвердить', callback_data='apply')],
        [InlineKeyboardButton(text='Выбрать другие', callback_data='other')]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup

def inline_no_groups__markup():
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Нет подходящих групп', callback_data='nogroups')]])
    return markup

def inline_pay_markup():
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Оплатить', callback_data='pay')]])
    return markup

def add_triger_markup():
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Добавить триггеры', callback_data='triggers')]])
    return markup


def true_ans_markup(text):
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f'{text} ✅', callback_data='ok')]])
    return markup

def success_add_channel():
    keyboard = [
        [KeyboardButton('Настроить инвайт в чат')],
        [KeyboardButton('Подключить еще группу')],
        [KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def error_add_channel():
    keyboard = [
        [KeyboardButton('Повторить попытку')],
        [KeyboardButton('Обратиться к поддержке')],
        [KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def call_employee():
    keyboard = [
        [KeyboardButton('Обратиться к поддержке')],
        [KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def error_pars_chat():
    keyboard = [
        [KeyboardButton('Повторить попытку')],
        [KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup
def accept_bot_markup():
    keyboard = [
        [KeyboardButton('Подтвердить')],
        [KeyboardButton('Отмена')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def go_to_profile():
    keyboard = [
        [KeyboardButton('Перейти в профиль')],
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def get_inline_chats_profile_p_o_i(client_id, chat_id) -> InlineKeyboardMarkup:
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Выбрать', callback_data=f'invPoI:{client_id}:{chat_id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup

def get_inline_chats_profile(client_id, chat_id) -> InlineKeyboardMarkup:
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Выбрать', callback_data=f'invProfile:{client_id}:{chat_id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup

def get_inline_del_source(id_channel, id_source) -> InlineKeyboardMarkup:
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Выбрать', callback_data=f'delSource:{id_channel}:{id_source}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup

def chat_profile_card(status_invite):
    keyboard = [
        [KeyboardButton('Отключить источник'), KeyboardButton('Добавить источник')],
        [KeyboardButton(f"{'Вкл. инвайт' if status_invite == 0 else 'Выкл. инвайт'}"), KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def choice_add_sour():
    keyboard = [
        [KeyboardButton('Через ссылку на чат'), KeyboardButton('Через поиск открытого')],
         [KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def get_inline_chats_pars(client_id, chat_id) -> InlineKeyboardMarkup:
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Начать инвайт', callback_data=f'invProf:{client_id}:{chat_id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def chat_pars_card():
    keyboard = [
        [KeyboardButton('Изменить группу')],
        [KeyboardButton('Вернуться в главное меню')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup
def cancel_markup_profile():
    keyboard = [
        [KeyboardButton('Отмена')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def pay_markup(user_id, amount):
    webApp = WebAppInfo(url=f'https://invite-robot.ru/pay_inv/{user_id}/{amount}/')
    keyboard = [
        [InlineKeyboardButton('Оплатить', web_app=webApp), InlineKeyboardButton('Проверить оплату', callback_data=f'checkpay:{user_id}:{amount}')]
    ]  
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    return markup  


def cur_markup():
    keyboard = [
        [InlineKeyboardButton(text='RUB', callback_data='cur:rub')],
        [InlineKeyboardButton(text='USD', callback_data='cur:usd')]
    ]  
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_profile_markup():
    keyboard = [
        [KeyboardButton('Пополнить баланс'), KeyboardButton('Подключить группу')],
        [KeyboardButton('Управление инвайтами'), KeyboardButton('Антиспам')],
        [KeyboardButton('◀️На главную')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def get_user_markup(*rows: Tuple[str]) -> ReplyKeyboardMarkup:
    """ Принимает кортежи вида `('button1', 'b2', 'b3', ...), (b1,b2,b3)` где каждый котеж новая строка в клаве"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for row in rows:
        markup.row(*map(KeyboardButton, row))
    return markup



def bot_usage_markup():
    keyboard = [
        [InlineKeyboardButton(text='Продвижение канала', callback_data='usage:Продвижение канала')],
        [InlineKeyboardButton(text='Продажа инфопродуктов', callback_data='usage:Продажа инфопродуктов')],
        [InlineKeyboardButton(text='Продажа услуг', callback_data='usage:Продажа услуг')],
        [InlineKeyboardButton(text='Другое', callback_data='usage:Другое')]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def work_markup():
    keyboard = [
        [InlineKeyboardButton(text='Лидер команды', callback_data='work:Лидер команды')],
        [InlineKeyboardButton(text='Руководитель отдела', callback_data='work:Руководитель отдела')],
        [InlineKeyboardButton(text='Самозанятый', callback_data='work:Самозанятый')]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def sphere_markup():
    keyboard = [
        [InlineKeyboardButton(text='Маркетинг', callback_data='sphere:Маркетинг')],
        [InlineKeyboardButton(text='Дизайн', callback_data='sphere:Дизайн')],
        [InlineKeyboardButton(text='Рекрутинг', callback_data='sphere:Рекрутинг')],
        [InlineKeyboardButton(text='Финансы', callback_data='sphere:Финансы')],
        [InlineKeyboardButton(text='Образование', callback_data='sphere:Образование')],
        [InlineKeyboardButton(text='Консалтинг', callback_data='sphere:Консалтинг')],
        [InlineKeyboardButton(text='Другое', callback_data='sphere:Другое')]
    ]  
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup

def user_accept_markup():
    keyboard = [
        [KeyboardButton('Принять и продолжить')]
    ]  
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup

def get_admin_markup(*rows: Tuple[str]) -> ReplyKeyboardMarkup:
    """ Принимает кортежи вида `('button1', 'b2', 'b3', ...), (b1,b2,b3)` где каждый котеж новая строка в клаве"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for row in rows:
        markup.row(*map(KeyboardButton, row))
    return markup


def parse_start_markup():
    keyboard = [
        [KeyboardButton('Получить данные')]
    ]  
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup


def go_to_main_markup():
    keyboard = [
        [KeyboardButton('◀️На главную')]
    ]  
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup


def lang_ch_markup():
    keyboard = [
        [InlineKeyboardButton(text='Русскоязычная', callback_data='segment:ru')],
        [InlineKeyboardButton(text='Англоязычная', callback_data='segment:en')]
    ]  
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_services_markup():
    keyboard = [
        [KeyboardButton('Поиск участников чата'), KeyboardButton('Поиск источников(чатов)')],
        [KeyboardButton('Поиск аккаунтов по номеру телефона'), KeyboardButton('История поиска')],
        [KeyboardButton('Антиспам'), KeyboardButton('Рассылка WA')], [KeyboardButton('◀️На главную')]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return markup


def get_inline_client_markup(client) -> InlineKeyboardMarkup:
    keyboard = []
    if client.status_id == CStatuses.WAITING_AUTHORIZATION.value['id']:
        keyboard.append([InlineKeyboardButton(text='Авторизоваться', callback_data=f'client:authorization:{client.id}')])
    keyboard.append([InlineKeyboardButton(text='Удалить', callback_data=f'client:delete:{client.id}')])
    if not client.proxy_status_id == CProxyStatuses.PROXY_NONE.value['id']:
        if client.proxy_status_id == CProxyStatuses.PROXY_ON.value['id']:
            keyboard.append([InlineKeyboardButton(text='Выключить прокси', callback_data=f'client:proxyOFF:{client.id}')])
        elif client.proxy_status_id == CProxyStatuses.PROXY_OFF.value['id']:
            keyboard.append([InlineKeyboardButton(text='Включить прокси', callback_data=f'client:proxyON:{client.id}')])
        keyboard.append([InlineKeyboardButton(text='Удалить прокси', callback_data=f'client:ProxyDelete:{client.id}')])
    else:
        keyboard.append([InlineKeyboardButton(text='Добавить прокси', callback_data=f'client:addProxy:{client.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_inline_wa_mailing_correct_markup(mai):
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='добавить номера', callback_data=f'wa_mailing:mailing_correct_ph:{mai.id}'),
    InlineKeyboardButton(text='изменить текст', callback_data=f'wa_mailing:mailing_correct_text:{mai.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup 

def get_inline_wa_mailing_cont_markup(mai):
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='остановить', callback_data=f'wa_mailing:mailing_stop:{mai.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup 

def get_inline_wa_mailing_stop_markup(mai):
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Запустить', callback_data=f'wa_mailing:mailing_start:{mai.id}'),
    InlineKeyboardButton(text='Скорректировать', callback_data=f'wa_mailing:mailing_correct:{mai.id}')])
    keyboard.append([InlineKeyboardButton(text='Удалить', callback_data=f'wa_mailing:mailing_delete:{mai.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup 


def get_inline_wa_mailing_markup(mai):
    keyboard = []
    if mai.status_id == WA_Mailing_statuses.UNWORKING.value['id'] or mai.status_id == WA_Mailing_statuses.PAUSED.value['id']:
        keyboard.append([InlineKeyboardButton(text='Запустить', callback_data=f'wa_mailing:mailing_start:{mai.id}'),
        InlineKeyboardButton(text='Скорректировать', callback_data=f'wa_mailing:mailing_correct:{mai.id}')])
        keyboard.append([InlineKeyboardButton(text='Удалить', callback_data=f'wa_mailing:mailing_delete:{mai.id}')])
    elif mai.status_id == WA_Mailing_statuses.WORKING.value['id']:
        keyboard.append([InlineKeyboardButton(text='остановить', callback_data=f'wa_mailing:mailing_stop:{mai.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup   

def get_inline_wa_client_markup(client) -> InlineKeyboardMarkup:
    keyboard = []
    if client.status_id == WA_CStatuses.WAITING_AUTHORIZATION.value['id']:
        keyboard.append([InlineKeyboardButton(text='Авторизоваться', callback_data=f'wa_client:waauthorization:{client.id}')])
    elif client.status_id == WA_CStatuses.AUTHORIZED.value['id']:
        keyboard.append([InlineKeyboardButton(text='Разлогинить', callback_data=f'wa_client:walogout:{client.id}')])
        keyboard.append([InlineKeyboardButton(text='Перезапустить', callback_data=f'wa_client:wareboot:{client.id}')])
    keyboard.append([InlineKeyboardButton(text='Удалить', callback_data=f'wa_client:wadelete:{client.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_inline_chats_markup(client, chat) -> InlineKeyboardMarkup:
    keyboard = []
    if chat.admin_rights or chat.creator:
        keyboard.append([InlineKeyboardButton(text='Инвайтить в эту группу', callback_data=f'inviting:{client.id}:{chat.id}')])
    keyboard.append([InlineKeyboardButton(text='Парсить участников', callback_data=f'parsing:{client.id}:{chat.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_inline_invite_stop_markup(client_id, chat_id) -> InlineKeyboardMarkup:
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Остановить', callback_data=f'stop_inviting:{client_id}:{chat_id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup
