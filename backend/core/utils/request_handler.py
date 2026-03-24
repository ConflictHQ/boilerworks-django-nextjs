from http import HTTPStatus

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class RequestHandler:
    session = None

    def __init__(
            self,
            default_retries: int = 1,
            default_backoff_factor: float = 1,
            default_status_forcelist: list = (
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    HTTPStatus.BAD_GATEWAY,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    HTTPStatus.GATEWAY_TIMEOUT
            )
    ):
        self.default_retries = default_retries
        self.default_backoff_factor = default_backoff_factor
        self.default_status_forcelist = default_status_forcelist

    def create_session(self, retries: int, backoff_factor: float, status_force_list: list):
        if self.session is None:
            session = requests.Session()
            retry = Retry(
                total=retries,
                read=retries,
                connect=retries,
                backoff_factor=backoff_factor,
                status_forcelist=status_force_list,
            )

            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            self.session = session

        return self.session

    def make_request(self, method: str, url: str, **kwargs):
        session = kwargs.pop('session', None)

        if session is None:
            retries = kwargs.pop('retries', self.default_retries)
            backoff_factor = kwargs.pop('backoff_factor', self.default_backoff_factor)
            status_force_list = kwargs.pop('status_forcelist', self.default_status_forcelist)
            session = self.create_session(
                retries=retries,
                backoff_factor=backoff_factor,
                status_force_list=status_force_list
            )

        response = session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
