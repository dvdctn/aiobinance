# binance.py
# aiobinance
#
# Created by David on 04/11/2024.
# Copyright © 2024 David. All rights reserved.

import json
import logging
import re
from asyncio import create_task, gather
from datetime import datetime
from urllib.parse import urlencode

from aiobinance.base.asyncExchange import AsyncExchange
from aiobinance.base.baseEndpoint import BaseEndpoint
from aiobinance.endpoints import Endpoints
from aiobinance.enums import EndpointSecurity, FiatTransactionType


class BinanceAsync(AsyncExchange):

    def __init__(
        self,
        key: str = None,
        secret: str = None,
        base_url: str = None,
        tz="UTC",
        name="Binance",
    ) -> None:
        base_url = base_url or "https://api.binance.com"

        super().__init__(
            key=key,
            secret=secret,
            password=None,
            name=name,
            base_url=base_url,
            tz=tz,
        )

        if key:
            self._SESSION.headers.extend({"X-MBX-APIKEY": key})

        self.log = logging.getLogger(__name__)

    #
    # PUBLIC API
    #

    async def marketInfo(
        self,
        symbol: str = None,
        symbols: list[str] = None,
        permissions: list[str] = None,
        show_permission_sets=True,
        symbol_status: str = None,
    ) -> dict:
        """
        Retrieve exchange information from the Binance API with customizable query parameters.

        The endpoint for this request is "/api/v3/exchangeInfo".

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api#exchange-information

        Parameters
        ----------
        symbol : str, optional
            A single trading pair symbol, such as "BNBBTC". Cannot be used with `symbols`.
        symbols : list of str, optional
            A list of trading pair symbols, such as ["BTCUSDT", "BNBBTC"]. Cannot be used with `symbol`.
        permissions : list of str, optional
            Permissions to filter the response by. Examples include "SPOT" or "MARGIN".
        show_permission_sets : bool, optional
            If True, includes the `permissionSets` field in the response. Defaults to True.
        symbol_status : str, optional
            Filters symbols based on trading status. Valid values are "TRADING", "HALT", and "BREAK".
            Cannot be used in combination with `symbols` or `symbol`.

        Returns
        -------
        dict
            The JSON response from the Binance API, parsed as a dictionary. If there is an error,
            returns a dictionary with an "error" key containing the error message.

        Examples
        --------
        >>> get_binance_exchange_info(symbol="BNBBTC")
        >>> get_binance_exchange_info(symbols=["BTCUSDT", "BNBBTC"], permissions=["SPOT"], symbol_status="TRADING")
        """
        ENDPOINT = Endpoints.EXCHANGE_INFO

        # Build request parameters
        params = {
            "symbol": self._prepareSymbol(symbol),
            "symbols": [self._prepareSymbol(symbol) for symbol in symbols],
            "permissions": permissions,
            "showPermissionSets": show_permission_sets,
            "symboslStatus": symbol_status,
        }
        params = dict(
            symbol=self._prepareSymbol(symbol),
            symbols=[self._prepareSymbol(symbol) for symbol in symbols],
            permissions=permissions,
            showPermissionSets=show_permission_sets,
            symboslStatus=symbol_status,
        )

        info: dict = await self._request(endPoint=ENDPOINT, params=params)

        return info

    async def klines(
        self,
        symbol: str,
        timeframe: str,
        since: int | datetime,
        until: int | datetime,
        timezone: str = "0",
        limit=1000,
    ) -> list[list[float | int]]:
        """
        Fetches and aggregates kline data for a given trading symbol
        over a specified time range and interval.

        The endpoint for this request is "/api/v3/klines".

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/public-api-endpoints#klinecandlestick-data

        Parameters
        ----------
        symbol : str
            Trading symbol as required by the exchange API (e.g., 'BTCUSDT').
            Non-alphanumeric characters are automatically removed, allowing
            the use of any delimiter (e.g., 'BTC/USDT' or 'BTC-USDT' will be
            treated as 'BTCUSDT').

        timeframe : str
            Interval format as '{interval}{time unit}' (e.g., '5m').
            Valid time units include:
            - 's' -> seconds
            - 'm' -> minutes
            - 'h' -> hours
            - 'd' -> days
            - 'w' -> weeks
            - 'M' -> months

        since : int or datetime
            Timestamp for the starting time of the first candlestick (inclusive).
            Always interpreted in UTC, regardless of timezone.
            If `int`, it must be provided in milliseconds.

        until : int or datetime
            Timestamp for the ending time of the last candlestick (inclusive).
            Always interpreted in UTC, regardless of timezone.
            If `int`, it must be provided in milliseconds.

        timezone : str
            If timezone provided, kline intervals are interpreted in that timezone instead of UTC.

            Note that startTime and endTime are always interpreted in UTC, regardless of timezone.
            Supported values:
            - Hours and minutes (e.g. "-1:00", "05:45")
            - Only hours (e.g. "0", "8", "4")
            - Accepted range is strictly [-12:00 to +14:00] inclusive


        limit : int, optional
            Maximum number of klines to retrieve per request (default is 1000).

        Returns
        -------
        list of list of float or int
            A list of lists, where each inner list represents a kline with the following format:
            `[Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Unused field, ignore]`.

        Notes
        -----
        - The time between `since`and `until` can exceed the limit imposed by the API:
          this method will split the request accordingly.
        - Response time is in UTC.
        """

        symbol = self._prepareSymbol(symbol)

        START_MS, END_MS = self._parseTime(since, until)

        # Range date
        BASE_STEP = self._timeInterval(timeframe)
        STEP = BASE_STEP * limit
        tasks = []
        # stop = END_MS + BASE_STEP because the stop must be included
        # step =  STEP + BASE_STEP to avoid repeated data (otherwise the last
        # kline of the previous request is the same as the start of the new one)
        for start in range(START_MS, END_MS + BASE_STEP, STEP + BASE_STEP):
            end = min(END_MS, start + STEP)
            tasks.append(
                create_task(
                    self._baseKlines(
                        params=dict(
                            symbol=symbol,
                            interval=timeframe,
                            startTime=start,
                            endTime=end,
                            timeZone=timezone,
                            limit=limit,
                        )
                    )
                )
            )

        klines = await gather(*tasks)
        # logger.debug("Downloaded all klines.")

        return klines

    #
    # Spot
    #

    async def spotTrades(
        self,
        symbol: str,
        since: int | datetime = None,
        until: int | datetime = None,
        orderId: int = None,  # This can only be used in combination with symbol.
        fromId: int = None,  # TradeId to fetch from. Default gets most recent trades.
        limit: int = 1000,
        enforceLimit=False,  # Wether to stop with the first call and don't proceed with following request
    ):
        """
        Fetches a list of spot trades for a specific symbol, optionally within a specified time range,
        and allows for pagination or batch fetching based on the `enforceLimit` parameter.

        This method is designed to retrieve spot trades, leveraging either time-based or ID-based
        pagination to obtain all trades within a specified range or up to the specified `limit`.

        The endpoint for this request is "/api/v3/myTrades".

        https://developers.binance.com/docs/binance-spot-api-docs/rest-api/public-api-endpoints#account-trade-list-user_data

        Parameters
        ----------
        symbol : str
            The trading pair symbol to fetch trades for (e.g., "BTCUSDT").
        since : int or datetime, optional
            The starting point for fetching trades. Can be a timestamp in milliseconds or a `datetime` object.
        until : int or datetime, optional
            The ending point for fetching trades. Can be a timestamp in milliseconds or a `datetime` object.
            If present and `since=None`, limits the fetching to a single request, disregarding `enforceLimit`.
        orderId : int, optional
            Filter trades based on a specific order ID. Only works in combination with `symbol`.
        fromId : int, optional
            The trade ID to fetch trades from. If omitted, the method retrieves the most recent trades.
        limit : int, default=1000
            The maximum number of trades to retrieve per request.
        enforceLimit : bool, default=False
            If True, limits the fetch to a single request based on the `limit` parameter.
            If False, retrieves all available trades until there are no more trades to fetch or `until` is reached.

        Returns
        -------
        list[dict]
            A list of trades as dictionaries, each containing trade data for the specified `symbol`.

        Notes
        -----
        - If both `since` and `until` are specified, the method will use a time-based interval split approach
          to ensure that the API time range limits are respected. So the time range between `startTime` and
          `endTime` can exceed the API limitation.
        - `until` with `since=None` will restrict fetching to a single request, disregarding `enforceLimit`.
        """

        ENDPOINT = Endpoints.SPOT_TRADES

        START_MS = self._timestamp(since) if since else None
        END_MS = self._timestamp(until) if until else None

        params = dict(
            symbol=self._prepareSymbol(symbol),
            orderId=orderId,
            startTime=START_MS,
            endTime=END_MS,
            fromId=fromId,
            limit=limit,
        )

        if START_MS and END_MS:
            # Max time difference between startTime and endTime allowed by the API: 24h
            INTERVAL = 1_000 * 60 * 60 * 24

            data = await self._split_request_interval(
                endpoint=ENDPOINT, maxRange=INTERVAL, params=params
            )

        else:
            data = await self._tradesCycle(params=params, enforceLimit=enforceLimit)

        return data

    #
    # Wallet
    #

    async def userAsset(self, asset: str = None, needBtcValuation=True) -> list[dict]:
        """
        Retrieve user's asset information from the API.

        The endpoint for this request is GET "/sapi/v3/asset/getUserAsset".

        https://developers.binance.com/docs/wallet/asset/user-assets

        Parameters
        ----------
        asset : str, optional
            The symbol of the specific asset to retrieve information for (e.g., "BTC", "ETH").
            If not provided, information for all assets with a positive balance is returned.
        needBtcValuation : bool, optional, default=True
            Indicates whether the BTC valuation of each asset should be included in the response.

        Returns
        -------
        list[dict]
            A list of dictionaries containing asset information. Each dictionary includes:

            - "asset" (str): The asset symbol (e.g., "BTC").
            - "free" (str): The amount of the asset that is freely available.
            - "locked" (str): The amount of the asset that is currently locked.
            - "freeze" (str): The amount of the asset that is frozen.
            - "withdrawing" (str): The amount of the asset that is currently being withdrawn.
            - "ipoable" (str): The amount of the asset that can be used in IPOs.
            - "btcValuation" (str): The BTC valuation of the asset, if `needBtcValuation` is `True`,
                otherwise `0`.

        Example Response
        ----------------
        [
            {
                "asset": "AVAX",
                "free": "1",
                "locked": "0",
                "freeze": "0",
                "withdrawing": "0",
                "ipoable": "0",
                "btcValuation": "0"
            },
            ...
        ]

        Notes
        -----
        - The `btcValuation` value in the response will be `0` if `needBtcValuation` is set to `False`.
        """
        ENDPOINT = Endpoints.USER_ASSETS

        params = {
            "asset": asset,
            "needBtcValuation": needBtcValuation,
        }

        resp: list[dict] = await self._request(endPoint=ENDPOINT, params=params)

        return resp

    #
    # Fiat
    #

    async def fiat_deposit_withdrawal(
        self,
        transactionType: FiatTransactionType,
        since: int | datetime,
        until: int | datetime = None,
        limit: int = 500,
    ) -> list[dict]:
        """
        Fetches fiat deposit or withdrawal transactions within a specified date range.

        The endpoint for this request is "/sapi/v1/fiat/orders".

        https://developers.binance.com/docs/fiat/rest-api/Get-Fiat-Deposit-Withdraw-History

        Parameters
        ----------
        transactionType : FiatTransactionType
            Specifies the type of transaction to fetch.
        since : datetime or int
            The start datetime from which transactions should be retrieved.
        until : datetime or int, optional
            The end datetime up to which transactions should be retrieved. If not provided, the current time is
            used as the default, retrieving all transactions from `since` up to the present.
        limit : int, optional
            Maximum number of transactions to retrieve per request, default is 500. (aka 'row' parameter)

        Returns
        -------
        list[dict]
            A list of dictionaries where each dictionary represents a fiat transaction with the following fields:

            - orderNo (str): Unique identifier for the transaction.
            - fiatCurrency (str): The fiat currency involved in the transaction, e.g., "BRL".
            - indicatedAmount (str): The indicated transaction amount before any fees, as a string for precision.
            - amount (str): The actual transaction amount after fees, as a string for precision.
            - totalFee (str): The total transaction fee applied, represented as a string.
            - method (str): The payment method used for the transaction, e.g., "BankAccount".
            - status (str): Current status of the transaction. Possible values include:
                * "Processing"
                * "Failed"
                * "Successful"
                * "Finished"
                * "Refunding"
                * "Refunded"
                * "Refund Failed"
                * "Order Partial Credit Stopped"
            - createTime (int): The creation timestamp of the transaction in milliseconds since the epoch.
            - updateTime (int): The last updated timestamp of the transaction in milliseconds since the epoch.

        Examples
        --------
        ```python
        transactions = await binance.fiat_deposit_withdrawal(
            transactionType=FiatTransactionType.DEPOSIT,
            since=datetime(2023, 1, 1, tzinfo=ZoneInfo("Europe/Rome")),
            until=datetime(2023, 2, 1, tzinfo=ZoneInfo("Europe/Rome"))
        )
        ```
        """

        ENDPOINT = Endpoints.FIAT_ORDERS

        # unixtime
        start_ms, end_ms = self._parseTime(since, until)

        payload = {
            "transactionType": transactionType.value,
            "beginTime": start_ms,
            "endTime": end_ms,
            "rows": limit,  # Max 500
        }

        resp = await self._paginatedRequests(
            endPoint=ENDPOINT,
            params=payload,
        )

        return resp

    #
    # Request Methods
    #

    async def _tradesCycle(self, params: dict, enforceLimit: bool):
        """
        Asynchronously fetches and processes trades in a paginated manner until a certain condition is met.

        This method retrieves trades from a specified endpoint and iterates over them until a certain condition is met,
        either by reaching the trade limit or by having fewer trades than the specified limit in a single response.
        The `enforceLimit` parameter controls whether to stop fetching additional trades after the first response.

        Parameters
        ----------
        params : dict
            Dictionary of parameters to pass to the endpoint for fetching trades. Required keys include:
            - "limit" (int): Maximum number of trades per request.
            - "endTime" (optional): Fetch to trades before this timestamp. If present, limits the fetching to a
                single request, disregarding `enforceLimit`.
            - "startTime" (optional): Starting timestamp for fetching trades.

        enforceLimit : bool
            If True, limits the fetch to a single request based on the `limit` specified in `params`. If False,
            the method will continue to fetch and aggregate trades until the response contains fewer trades
            than the specified limit.

        Returns
        -------
        list[dict]
            Returns a list of trade data dictionaries.

        Notes
        -----
        - `endTime` in `params` will restrict fetching to a single request, disregarding `enforceLimit`.
        - When paginating, it updates the payload with the last trade ID in each response to fetch the next batch.
        """

        ENDPOINT = Endpoints.SPOT_TRADES

        payload = params.copy()
        limit: int = params["limit"]

        data = []
        resp = await self._request(endPoint=ENDPOINT, params=payload)

        # If 'until' was given as an argument, doesn't fetch more trades
        if payload["endTime"]:
            return resp

        # Retrieves all trades until the response has less trades than the limit
        while not enforceLimit:
            data.extend(resp)
            if len(resp) < limit:
                break

            # Fetches the trades starting from the next trade ID.
            # Removes the 'startTime' because it cannot be passed together with 'fromId'
            payload["fromId"] = resp[-1]["id"] + 1
            payload.pop("startTime", None)

            resp = await self._request(endPoint=ENDPOINT, params=payload)

        return data

    async def _baseKlines(self, params: dict) -> list[list[float | int]]:
        klineList: list[list] = await self._request(
            endPoint=Endpoints.KLINES,
            params=params,
        )

        # 'Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Unused field, ignore'
        stringField = {1, 2, 3, 4, 5, 7, 9, 10}
        klines = [
            [
                float(field) if idx in stringField else field
                for idx, field in enumerate(kline)
            ]
            for kline in klineList
        ]

        return klines

    async def _paginatedRequests(
        self,
        endPoint: Endpoints,
        params: dict = None,
        rowsKey="rows",
        pageKey="page",
        dataKey="data",
        totalKey="total",
    ):
        """
        Fetches data from a paginated API endpoint asynchronously.

        This function retrieves data from an API that returns paginated results.
        It sends requests to each page in parallel (after the first page), which
        improves performance over sequential requests. All results are collected
        and returned as a single list.

        Parameters
        ----------
        endPoint : Endpoints
            The endpoint to which the request is sent.
        params : dict, optional
            A dictionary of query parameters to include with each request.
        rowsKey : str, optional
            The key in `params` where the total number of items per request is stored. Defaults to "rows".
        pageKey : str, optional
            The key in the API response where the page number is stored. Defaults to "page".
        dataKey : str, optional
            The key in the API response where the data is stored. Defaults to "data".
        totalKey : str, optional
            The key in the API response where the total number of pages is stored. Defaults to "total".
        method : str, optional
            The HTTP method to use for the requests. Defaults to "GET".

        Returns
        -------
        List[Any]
            A list containing the aggregated data from all pages. Each item in
            the list corresponds to a data item returned by the API in the
            specified `dataKey` field across all pages.

        Raises
        ------
        Exception
            Any exception raised by `_HTTP_Request` will propagate up if an individual page request fails and is not handled
            within the function. Consider implementing error handling for production use.

        Notes
        -----
        - The function avoids mutating the original `params` dictionary by copying it.
        """

        payload = params.copy()
        itemsPerRequest = payload[rowsKey]

        data = []

        # Make first request to know the total number of items to retrieve
        payload[pageKey] = 1
        resp = await self._request(endPoint=endPoint, params=payload)
        data.extend(resp[dataKey])

        # Make following requests asyncronously
        tasks = []
        for _ in range(itemsPerRequest, resp[totalKey] + 1, itemsPerRequest):
            payload[pageKey] += 1
            tasks.append(create_task(self._request(endPoint=endPoint, params=payload)))

        resp = await gather(*tasks)
        data.extend([x for r in resp for x in r[dataKey]])

        return data

    async def _split_request_interval(
        self, endpoint: Endpoints, maxRange: int, params: dict, func=None
    ):
        START_MS = params["startTime"]
        END_MS = params["endTime"]

        func = func or self._request

        payload = params.copy()
        tasks = []
        for start in range(START_MS, END_MS, maxRange):
            payload["startTime"] = start
            payload["endTime"] = min(END_MS, start + maxRange)

            tasks.append(create_task(func(endpoint, payload)))

        resp = await gather(*tasks)
        data = [x for l in resp for x in l]

        return data

    async def _request(self, endPoint: Endpoints, params: dict = None):
        """
        Asynchronously send an HTTP request to a specified endpoint with optional
        parameters and signing, while respecting endpoint-specific rate limits.

        Parameters
        ----------
        endPoint : Endpoints
            The endpoint to which the request is sent.
        params : dict, optional
            A dictionary of parameters to include in the request payload.
            If `None`, no additional parameters are sent.
        sign : bool, default=True
            If True, sign the request payload with additional authentication fields.
        method : str, default="GET"
            The HTTP method to use for the request (e.g., "GET", "POST").

        Returns
        -------
        dict or list
            The JSON-decoded response from the endpoint, which could be a
            dictionary or list based on the API response.

        Notes
        -----
        - **Rate Limiting**: The method respects the endpoint’s rate limit:
            - Determines if the rate limit for the specified endpoint has been reached.
            - Pauses the request if the rate limit is exceeded, waiting until the rate limit is reset.
            - Proceeds with the request immediately if the rate limit allows.
            Using `await` for this check ensures that the pause, if needed, is
            non-blocking, allowing other asynchronous tasks to proceed without delay.
        """
        # Obtains the endpoint details
        baseEndpoint: BaseEndpoint = endPoint.value

        # This ensures that the rate-limit of the endpoint is respected
        async with baseEndpoint:

            # Payload is prepared inside the rate-limiter because the timeout of sign
            payload = self._preparePayload(
                params=params, security=baseEndpoint.SECURITY
            )

            async with self._SESSION.request(
                method=baseEndpoint.METHOD.value, url=baseEndpoint.URL, params=payload
            ) as resp:

                self.log.debug(resp.real_url)
                self.log.debug(resp.headers)

                data: dict | list = await resp.json()

                self.log.debug(data)

        return data

    def _preparePayload(self, params: dict | None, security: EndpointSecurity) -> dict:
        """
        Prepare the request payload by removing any key-value pairs with `None` values and
        converting certain data types as required.

        Parameters
        ----------
        params : dict, optional
            The dictionary containing the initial payload parameters for the request.
        sign : bool, default=True
            If True, sign the payload for authentication.

        Returns
        -------
        dict
            A `new` dictionary containing only key-value pairs from `params` where values are not `None`
            or empty collections. Additionally, it converts boolean values to lowercase strings, lists
            to JSON strings, and, if `sign` is True, adds `recvWindow`, `timestamp`, and `signature` fields.

        Notes
        -----
        - Boolean values are converted to lowercase strings ("true" or "false").
        - Lists are JSON-encoded with compact separators (`,`, `:`).
        - When `sign` is enabled, a timestamp and a signature are generated using internal helper methods.

        """

        payload = dict()

        if params is not None:

            for k, v in params.items():
                # Skip None values or empty collections
                if v is None or (hasattr(v, "__len__") and len(v) == 0):
                    continue

                if isinstance(v, bool):
                    payload[k] = str(v).lower()

                elif isinstance(v, list):
                    payload[k] = json.dumps(v, separators=(",", ":"))

                else:
                    payload[k] = v

        if security in EndpointSecurity.SIGNED:
            # Adds recv and timestamp and generates signature
            payload["recvWindow"] = self._RECV_WINDOW
            payload["timestamp"] = str(int(datetime.now().timestamp() * 1000))
            payload["signature"] = self._sign(payload)

        return payload

    def _prepareSymbol(self, symbol: str):
        return re.sub("[^A-Za-z0-9]", "", symbol).upper()

    def _sign(self, params):
        param_str = urlencode(params)
        return self._encrypt(param_str)
