# asyncExchange.py
# aiobinance
#
# Created by David Catania on 04/11/2024.
# Copyright © 2024 David Catania. All rights reserved.

import json
from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import sha256 as hashlib_sha256
from hmac import new as hmac_new
from re import search
from ssl import create_default_context
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientSession, TCPConnector
from certifi import where as certifi_where


class AsyncExchange(ABC):
    TIME_INTERVAL = dict(
        s=1_000,
        m=60_000,
        h=3_600_000,
        d=86_400_000,
        w=604_800_000,
        M=2_592_000_000,
    )
    PUBLIC_IP = None

    def __init__(
        self,
        key: str,
        secret: str,
        password: str,
        name: str,
        url: str,
        tz: str,
        recvWindow="5000",
    ) -> None:

        self._KEY = key
        self._SECRET = secret
        self._PASSWORD = password
        self._TIMEZONE = ZoneInfo(tz)

        self.NAME = name
        self.URL = url
        self._RECV_WINDOW = recvWindow

        ssl_context = create_default_context(cafile=certifi_where())
        self._SESSION = ClientSession(
            base_url=url,
            connector=TCPConnector(ssl=ssl_context),
            headers={
                "Content-Type": "application/json",
            },
        )

    #
    # API CALLS
    #

    #
    # HELPERS
    #

    async def close(self):
        await self._SESSION.close()

    @abstractmethod
    async def _request(self, endPoint: str, params: dict = None, method="GET"):
        pass

    async def _getPublicIP(self):
        # Check if the public IP is already set
        if AsyncExchange.PUBLIC_IP:
            return AsyncExchange.PUBLIC_IP

        # Fetch public IP asynchronously
        try:
            # Define own ClientSession because it has a different baseurl from the exchange
            async with ClientSession() as session:
                async with session.get(url="https://api.ipify.org") as response:
                    # Raise exception for any HTTP errors (e.g., 4xx, 5xx)
                    response.raise_for_status()

                    # Store and return the public IP
                    AsyncExchange.PUBLIC_IP = await response.text()
                    return AsyncExchange.PUBLIC_IP

        except ClientError as e:
            return None

    def _encrypt(self, msg) -> str:
        hash = hmac_new(
            key=bytes(self._SECRET, "utf-8"),
            msg=msg.encode("utf-8"),
            digestmod=hashlib_sha256,
        )

        return hash.hexdigest()

    def _parseTime(self, since: datetime, until: datetime | None):
        """
        Convert `since` and `until` datetime objects to timestamps in milliseconds.
        To avoid unexpected behaviours, use timezone-aware datetime object, otherwise
        it's assumed to be in `self._TIMEZONE`.

        Parameters
        ----------
        since : datetime
            The start datetime.
        until : datetime, default=None
            The end datetime. If None, the current time is used.

        Returns
        -------
        Tuple[int, int]
            A tuple containing timestamps in milliseconds for `since` and `until`.
        """

        # SINCE
        start_ms = self._timestamp(since)

        # UNTIL
        until = until or datetime.now(tz=self._TIMEZONE)
        end_ms = self._timestamp(until)

        return (start_ms, end_ms)

    def _timestamp(self, date: datetime):
        """
        Convert a datetime object to a timestamp in milliseconds. If `date` is timezone-naive,
        it's assumed to be in the exchange's timezone (self._TIMEZONE).

        Parameters
        ----------
        date : datetime
            The datetime to convert.

        Returns
        -------
        int
            The timestamp in milliseconds.

        Raises
        ------
        ValueError
            If the `date` parameter is None.
        """

        if date.tzinfo:
            date_aware = date

        else:
            date_aware = date.replace(tzinfo=self._TIMEZONE)

        start_ms = int(date_aware.timestamp() * 1000)

        return start_ms

    def _checkHTTPErrors(self, code) -> str:
        if code != 200:
            match code:
                case 400:
                    msg = "Bad request. Need to send the request with GET / POST (must be capitalized)"
                case 401:
                    msg = "Unauthorized. 1. Invalid API Key; 2. Need to put authentication params in the request header"
                case 403:
                    msg = "Forbidden request. Possible causes: 1. IP rate limit breached; 2. You send GET request with an empty json body"
                case 404:
                    msg = "Cannot find path. Possible causes: 1. Wrong path"
                case 405:
                    msg = "Method Not Allowed. You tried to access the resource with an invalid method"
                case 500:
                    msg = "Internal Server Error. Try again later"
                case 503:
                    msg = "Service Unavailable. Possible causes: 1. Maintenance. Try again later"
                case _:
                    msg = "Unknown error."

            return msg

    def _timeInterval(self, tf: str) -> int:
        """
        Given a time interval in the format '1x' or 'x1', returns its duration in milliseconds.

        Parameters
        ----------
        tf : str
            Time interval, e.g., '1m' or 'W1'. Case-sensitive.
            - 'm': minutes
            - 'h': hours
            - 'd': days
            - 'W': weeks
            - 'M': months (assumed as 30 days)

        Returns
        -------
        int
            Duration in milliseconds.
        """
        num = int(search(r"(\d+)", tf)[0])
        timeInterval = search("([A-Za-z]{1})", tf)[0]

        # Convert to lowercase for dictionary lookup if needed
        if timeInterval in ["S", "H", "D", "W"]:
            timeInterval = timeInterval.lower()

        millSecInterval = num * AsyncExchange.TIME_INTERVAL[timeInterval]

        return millSecInterval

    def _preparePayload(self, payload: dict) -> dict:
        """
        Remove key-value pairs with `None` values from the request's payload.

        Parameters
        ----------
        payload : dict[str, Any]
            The dictionary containing the payload of the request.

        Returns
        -------
        dict[str, Any]
            A new dictionary containing only key-value pairs from `payload`
            where the values are not `None`.
        """

        out = dict()
        for k, v in payload.items():
            # Skip None values or empty collections
            if v is None or (hasattr(v, "__len__") and len(v) == 0):
                continue

            if isinstance(v, bool):
                out[k] = str(v).lower()

            elif isinstance(v, list):
                out[k] = json.dumps(v, separators=(",", ":"))

            else:
                out[k] = v

        return out
