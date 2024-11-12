# endpoints.py
# src
#
# Created by David on 07/11/2024.
# Copyright © 2024 David. All rights reserved.

from enum import Enum

from aiolimiter import AsyncLimiter

from aiobinance.enums import EndpointSecurity


class ApiType(Enum):
    """
    Enum representing the api endpoint type, either '/api/' or '/sapi/'
    """

    API = "api"
    SAPI = "sapi"


class LimitType(Enum):
    """
    Enum representing the type of limit imposed on an endpoint,
    either IP-based or ACCOUNT-based (UID)
    """

    IP = 0
    UID = 1
    IP_SEC = 2


class Limits(Enum):
    # API endpoints share the 6,000 per minute limit based on IP.
    api_LIMIT = 6_000
    # Each SAPI endpoint has an independent limit counter, either based on IP or UID
    sapi_IP_LIMIT = 12_000
    sapi_UID_LIMIT = 180_000
    sapi_IP_LIMIT_SEC = 180_000


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"


class BaseEndpoint:
    """
    Represents an API endpoint with rate limiting based on IP or UID constraints.

    This class provides rate limiting for different types of API endpoints. The rate
    limits are applied based on the endpoint type (`SAPI` or `API`) and the specified
    limit type (`IP` or `UID`). A shared rate limiter is used for all `/api` endpoints,
    while each `/sapi` endpoint has an independent rate limiter based on its `LIMIT_TYPE`.

    Attributes
    ----------
    SHARED_IP_LIMIT : int
        The `/api/` endpoints total limit per minute, shared across all of them.
    IP_LIMIT : int
        The `/sapi/` IP-based endpoint total limit per minute, indipendent for each endpoint.
    UID_LIMIT : int
        The `/sapi/` UID-based endpoint total limit per minute, indipendent for each endpoint.

    Parameters
    ----------
    URL : str
        The URL of the endpoint.
    WEIGHT : int
        The request weight of the endpoint.
    LIMIT_TYPE : LimitType
        Specifies whether the rate limit is based on IP or UID. `/api/` endpoints are all IP-based.

    Notes
    -----
    - The rate limit for `/api` endpoints is shared across all instances.
    - The rate limit for `/sapi` endpoints is specific to each instance, depending on
      whether it is an IP- or UID-based limit.
    - The limiter automatically adjusts based on the endpoint’s API type and limit type.

    Examples
    --------
    Instantiate an endpoint and acquire the limiter within an async context:

    >>> endpoint = BaseEndpoint(URL="/api/v1/order", WEIGHT=5, LIMIT_TYPE=LimitType.IP)
    ... async with endpoint:
    ...     # Process request within rate limit constraints
    """

    # Shared limiter for '/api' endpoints
    _sharedLimiter = AsyncLimiter(max_rate=Limits.api_LIMIT.value, time_period=60)

    __slots__ = "URL", "WEIGHT", "METHOD", "SECURITY", "_limiter"

    def __init__(
        self,
        URL: str,
        METHOD: HTTPMethod,
        SECURITY: EndpointSecurity,
        WEIGHT: int,
        LIMIT_TYPE: LimitType,
    ) -> None:
        self.URL: str = URL
        self.METHOD: HTTPMethod = METHOD
        self.SECURITY: EndpointSecurity = SECURITY
        self.WEIGHT: int = WEIGHT

        # The type of limit imposed on this endpoint, either IP-based or ACCOUNT-based (UID)
        # self.LIMIT_TYPE: LimitType = LIMIT_TYPE

        # The api endpoint type, either '/api/' or '/sapi/'
        API_TYPE = ApiType(URL.split("/", maxsplit=2)[1])

        if API_TYPE == ApiType.SAPI:
            if LIMIT_TYPE == LimitType.UID:
                self._limiter = AsyncLimiter(
                    max_rate=Limits.sapi_UID_LIMIT.value, time_period=60
                )
            elif LIMIT_TYPE == LimitType.IP:
                self._limiter = AsyncLimiter(
                    max_rate=Limits.sapi_IP_LIMIT.value, time_period=60
                )
            elif LIMIT_TYPE == LimitType.IP_SEC:
                self._limiter = AsyncLimiter(
                    max_rate=Limits.sapi_IP_LIMIT_SEC.value, time_period=1
                )

        elif API_TYPE == ApiType.API:
            self._limiter = BaseEndpoint._sharedLimiter

    async def acquire(self):
        """Blocks if rate limit is exceeded."""
        await self._limiter.acquire(amount=self.WEIGHT)

    async def __aenter__(self) -> None:
        await self.acquire()

        return None

    async def __aexit__(self, exc_type, exc, tb):
        return None
