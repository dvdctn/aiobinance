# endpoints.py
# aiobinance
#
# Created by David on 08/11/2024.
# Copyright © 2024 David. All rights reserved.

from enum import Enum

from aiobinance.base.baseEndpoint import BaseEndpoint, HTTPMethod, LimitType
from aiobinance.enums import EndpointSecurity


class Endpoints(Enum):
    """
    Enum with the endpoints of the Binance API.
    """

    # Wallet

    COINS = BaseEndpoint(
        URL="/sapi/v1/capital/config/getall",
        METHOD=HTTPMethod.GET,
        WEIGHT=10,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )

    USER_ASSETS = BaseEndpoint(
        URL="/sapi/v3/asset/getUserAsset",
        METHOD=HTTPMethod.POST,
        WEIGHT=5,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )

    ACCOUNT_SNAPSHOT = BaseEndpoint(
        URL="/sapi/v1/accountSnapshot",
        METHOD=HTTPMethod.GET,
        WEIGHT=2_400,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )
    DIVIDEND = BaseEndpoint(
        URL="/sapi/v1/asset/assetDividend",
        METHOD=HTTPMethod.GET,
        WEIGHT=10,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )
    DUSTLOG = BaseEndpoint(
        URL="/sapi/v1/asset/dribblet",
        METHOD=HTTPMethod.GET,
        WEIGHT=1,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )
    WITHDRAW_HISTORY = BaseEndpoint(
        URL="/sapi/v1/capital/withdraw/history",
        METHOD=HTTPMethod.GET,
        WEIGHT=18_000,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP_SEC,
    )
    DEPOSIT_HISTORY = BaseEndpoint(
        URL="/sapi/v1/capital/deposit/hisrec",
        METHOD=HTTPMethod.GET,
        WEIGHT=1,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )

    # Fiat

    FIAT_ORDERS = BaseEndpoint(
        URL="/sapi/v1/fiat/orders",
        METHOD=HTTPMethod.GET,
        WEIGHT=90_000,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.UID,
    )

    # Rebate

    REBATE = BaseEndpoint(
        URL="/sapi/v1/rebate/taxQuery",
        METHOD=HTTPMethod.GET,
        WEIGHT=12_000,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.UID,
    )

    # Convert

    CONVERT_HISTORY = BaseEndpoint(
        URL="/sapi/v1/convert/tradeFlow",
        METHOD=HTTPMethod.GET,
        WEIGHT=3_000,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.UID,
    )

    # Auto Invest

    AUTOINVEST_SUB = BaseEndpoint(
        URL="/sapi/v1/lending/auto-invest/history/list",
        METHOD=HTTPMethod.GET,
        WEIGHT=1,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )

    # Simple Earn

    SE_FLEX_REWARDS = BaseEndpoint(
        URL="/sapi/v1/simple-earn/flexible/history/rewardsRecord",
        METHOD=HTTPMethod.GET,
        WEIGHT=150,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )

    # Spot

    SPOT_TRADES = BaseEndpoint(
        URL="/api/v3/myTrades",
        METHOD=HTTPMethod.GET,
        WEIGHT=20,
        SECURITY=EndpointSecurity.USER_DATA,
        LIMIT_TYPE=LimitType.IP,
    )

    # Public

    EXCHANGE_INFO = BaseEndpoint(
        URL="/api/v3/exchangeInfo",
        METHOD=HTTPMethod.GET,
        WEIGHT=20,
        SECURITY=EndpointSecurity.NONE,
        LIMIT_TYPE=LimitType.IP,
    )

    KLINES = BaseEndpoint(
        URL="/api/v3/klines",
        METHOD=HTTPMethod.GET,
        WEIGHT=2,
        SECURITY=EndpointSecurity.NONE,
        LIMIT_TYPE=LimitType.IP,
    )
