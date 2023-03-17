import json
import base64
import logging
import logging.handlers as loghandlers
from http import HTTPStatus
import asyncio
import requests

from .wa_errors import ERRORS, Errors
from repositories.getRepo import get_member_repo, get_wa_client_repo
from enums import WA_CWorkes, WA_Mailing_statuses, WA_CStatuses


LOGGER = logging.getLogger('wapi_log')
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s  %(filename)s  %(funcName)s  %(lineno)d  %(name)s  %(levelname)s: %(message)s')
log_handler = loghandlers.RotatingFileHandler(
    './logs/wa_api_logs.log',
    maxBytes=1000000,
    encoding='utf-8',
    backupCount=50
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(formatter)
LOGGER.addHandler(log_handler)


GREEN_ENDPOINT = "https://api.green-api.com/waInstance{id}/{type}/{token}"

async def wa_verify():
    member_repo = get_member_repo()
    wa_repo = get_wa_client_repo()
    acc = await wa_repo.get_by_phone('995595074761')
    members = await member_repo.get_with_phone_WA()
    if not members:
        print('У всех юзеров проверен WA')
        return
    for mem in members:
        data = json.dumps({
            "phoneNumber": int(mem.phone)
        })
        headers = {
            'Content-Type': 'application/json'
        }
        r = requests.post(
            GREEN_ENDPOINT.format(
                id=acc.id_instance, type='CheckWhatsapp', token=acc.api_token
            ), headers=headers, data=data
        )
        try:
            result = r.json()['existsWhatsapp']
            await member_repo.update(id=mem.id, WA=result)
            print(r.text)
        except Exception as err:
            LOGGER.debug(err, r.status_code, r.text)
            if r.status_code == HTTPStatus.BAD_REQUEST:
                if r.text == Errors.BAD_PHONE_NUM.value:
                    LOGGER.debug(ERRORS[Errors.BAD_PHONE_NUM])
                    continue
                elif r.text == Errors.TIMEOUT.value:
                    LOGGER.debug(ERRORS[Errors.TIMEOUT])
                    continue
                elif r.text == Errors.RESTARTING.value:
                    LOGGER.debug(ERRORS[Errors.RESTARTING])
                    break
                elif r.text == Errors.NOT_AUTH.value:
                    LOGGER.debug(ERRORS[Errors.NOT_AUTH])
                    break
                elif r.text == Errors.BAD_DATA.value:
                    LOGGER.debug(ERRORS[Errors.BAD_DATA])
                    break
                else:
                    LOGGER.debug(f'Неизвестная ошибка: {r.status_code}, {r.text}')
                    continue
            elif r.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                if r.text == Errors.TOO_MANY_REQ.value:
                    LOGGER.debug(ERRORS[Errors.TOO_MANY_REQ])
                    continue
                else:
                    LOGGER.debug(f'Неизвестная ошибка: {r.status_code}, {r.text}')
                    continue
            elif r.status_code == 466:
                if r.text == Errors.LIMIT.value:
                    LOGGER.debug(ERRORS[Errors.LIMIT])
                    break
                else:
                    LOGGER.debug(f'Неизвестная ошибка: {r.status_code}, {r.text}')
                    continue
            else:
                LOGGER.debug(f'Неизвестная ошибка: {r.status_code}, {r.text}')
                continue


async def wa_check_state(client_data):
    try:
        payload = {}
        headers= {}
        response = requests.get(
            GREEN_ENDPOINT.format(
                id=client_data.id_instance, type='getStateInstance', token=client_data.api_token
            ), headers=headers, data = payload
        )
        return response.json()['stateInstance']
    except Exception as err:
        LOGGER.error(err)


async def wa_get_acc_settings(client_data):
    try:
        payload = {}
        headers= {}
        response = requests.get(
            GREEN_ENDPOINT.format(
                id=client_data.id_instance, type='GetSettings', token=client_data.api_token
            ), headers=headers, data = payload
        )
        return response.json()
    except Exception as err:
        LOGGER.error(err)


async def wa_send_qr(client_data):
    try:
        payload = {}
        headers= {}
        response = requests.get(
            GREEN_ENDPOINT.format(
                id=client_data.id_instance, type='qr', token=client_data.api_token
            ), headers=headers, data = payload
        )
        qr = response.json()['message']
        with open(f"qr/qr_{client_data.id_instance}.png", "wb") as fh:
            fh.write(base64.decodebytes(bytes(qr, 'utf-8')))
    except Exception as err:
        LOGGER.error(err)


async def wa_mailing(mailing_id):
    try:
        wa_repo = get_wa_client_repo()
        accs = await wa_repo.get_5()
        mailing = await wa_repo.get_mailing_by_id(mailing_id)
    except Exception as err:
        LOGGER.error(err)
    try:
        all_contacts = await wa_repo.get_mailing_phones(mailing_id)
        acc_num = 0
        len_accs = len(accs) - 1
        for acc in accs:
            await wa_repo.update(acc.id, work_id=WA_CWorkes.CHECKING.value['id'])
            # acc_status = await wa_check_state(acc)
            # if acc_status != 'authorized':
            #     accs.remove(acc)
            #     await wa_repo.update(acc.id, status_id=WA_CStatuses.WAITING_AUTHORIZATION.value['id'], phone='not authorized')
            #     LOGGER.info(f'Аккаунт {acc.id, acc.phone} вылетел, требуется проверка авторизации')
            #     print(1)
        for contact in all_contacts:
            acc = accs[acc_num]
            print(acc.phone, contact, mailing.text)
            payload = json.dumps({
                "chatId": f"{contact.phone}@c.us",
                "message": mailing.text
            })
            headers = {
              'Content-Type': 'application/json'
            }
            response = requests.post(GREEN_ENDPOINT.format(
                id=acc.id_instance, type='sendMessage', token=acc.api_token
            ), headers=headers, data = payload)
            print(response.json())
            await wa_repo.mailing_phones_update(mailing_id=mailing_id, phone=contact.phone, is_send=True)
            await wa_repo.mailing_send_update(mailing_id, c_send=1)
            if acc_num < len_accs:
                acc_num+=1
            else:
                acc_num=0
            await asyncio.sleep(2)
        for acc in accs:
            await wa_repo.update(acc.id, work_id=WA_CWorkes.UNWORKING.value['id'])
        await wa_repo.mailing_update(mailing_id, status_id=WA_Mailing_statuses.FINISHED.value['id'])
        await wa_repo.mailing_phones_delete(mailing_id)
    except Exception as err:
        LOGGER.error(err)


async def wa_logout(client_data):
    try:
        payload = {}
        headers= {}
        response = requests.get(
            GREEN_ENDPOINT.format(
                id=client_data.id_instance, type='logout', token=client_data.api_token
            ), headers=headers, data = payload
        )
        return response.json()['isLogout']
    except Exception as err:
        LOGGER.error(err)


async def wa_reboot(client_data):
    try:
        payload = {}
        headers= {}
        response = requests.get(
            GREEN_ENDPOINT.format(
                id=client_data.id_instance, type='reboot', token=client_data.api_token
            ), headers=headers, data = payload
        )
        return response.json()['isReboot']
    except Exception as err:
        LOGGER.error(err)


