# errors.py
# aiobinance
#
# Created by David on 04/11/2024.
# Copyright © 2024 David. All rights reserved.


class ExchangeException(Exception):
    """Exception class for Exchange instances."""

    def __init__(
        self,
        exchange: str,
        message: str = None,
        ret_code: int = None,
        endpoint: str = None,
        params: dict = None,
        response_message: str = None,
    ):
        if message is None:
            message = f"{exchange}: Exchange Exception."
        super().__init__(message)
        self.exchange = exchange
        self.ret_code = ret_code
        self.endpoint = endpoint
        self.params = params
        self.response_message = response_message


class UnmatchedIPError(ExchangeException):
    """Raised when the request IP address does not match the allowed IPs for the API key."""

    def __init__(self, exchange: str, ip_address: str, message: str = None, **kwargs):
        if message is None:
            message = f"IP address '{ip_address}' does not match any of the allowed IPs for this API Key."
            for key, value in kwargs.items():
                if value:
                    message += f" {key}: '{value}'."

        super().__init__(exchange=exchange, message=message, **kwargs)

        self.ip_address = ip_address


class InvalidApiKeyException(ExchangeException):
    """Raised when the API key is either expired or does not exist."""

    def __init__(self, exchange: str, api_key: str, message: str = None, **kwargs):
        if message is None:
            message = f"API key '{api_key}' is invalid or expired. Check whether the key and domain are matched"

        super().__init__(exchange=exchange, message=message, **kwargs)

        self.api_key = api_key


class InvalidSymbolException(ExchangeException):
    """Raised when the requested trade symbol does not exist."""

    def __init__(self, exchange: str, symbol: str, message: str = None, **kwargs):
        if message is None:
            message = f"Trade symbol '{symbol}' does not exist."

        super().__init__(exchange=exchange, message=message, **kwargs)

        self.symbol = symbol
