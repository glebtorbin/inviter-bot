from enum import Enum

class Errors(Enum):
    BAD_PHONE_NUM = '"bad phone number, valid 11 or 12 digits"'
    TIMEOUT = '"check phone number timeout limit exceeded"'
    RESTARTING = '"instance in starting process try later"'
    NOT_AUTH = '"instance not authorized"'
    BAD_DATA = '"bad request data"'
    TOO_MANY_REQ = '"Too Many Requests"'
    LIMIT = '"correspondentsStatus"'


ERRORS = {
    Errors.BAD_PHONE_NUM:
    'Неверный формат номера телефона, должен быть 11 или 12 цифр',

    Errors.TIMEOUT:
    'Превышен лимит времени ожидания ответа о проверке номера телефона',

    Errors.RESTARTING:
    'Аккаунт находится в процессе запуска/перезапуска. '
    'Попробуйте повторить попытку спустя несколько секунд.',

    Errors.NOT_AUTH:
   'Аккаунт не авторизован. Для авторизации аккаунта перейдите в '
   'Личный кабинет и считайте QR-код из приложения WhatsApp Business на телефоне.',

    Errors.BAD_DATA:
   'Данные запроса не валидны. Исправьте ошибку в параметрах запроса и повторите попытку.',

    Errors.TOO_MANY_REQ:
   'Пользователь отправил слишком много запросов за '
    'заданный промежуток времени. Уменьшите частоту запросов.',

    Errors.LIMIT:
   'Исчерпан лимит, подробнее в теле ошибки.'
}