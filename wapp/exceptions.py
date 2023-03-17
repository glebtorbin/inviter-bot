from http import HTTPStatus
from .wa_errors import ERRORS


class GreenApiException(BaseException):
    def __init__(self, status_code, error_identifier):
        if status_code == HTTPStatus.BAD_REQUEST:
            if error_identifier not in ERRORS.keys():
                message = f'Неизвестная ошибка {error_identifier}'
            message = ERRORS[error_identifier]
        elif status_code == 466:
            if error_identifier not in ERRORS.keys():
                message = f'Неизвестная ошибка {error_identifier}'
            message = ERRORS[error_identifier]
        elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
            if error_identifier not in ERRORS.keys():
                message = f'Неизвестная ошибка {error_identifier}'
            message = ERRORS[error_identifier]
        else:
            message = f"HTTP Status Code was: {status_code}. Текст ошибки: {error_identifier}"

        super().__init__(message)
