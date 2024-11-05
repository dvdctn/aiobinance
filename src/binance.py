# binance.py
# aiobinance
#
# Created by David Catania on 04/11/2024.
# Copyright © 2024 David Catania. All rights reserved.

from asyncio import create_task, gather
from datetime import datetime
from enum import Enum
from urllib.parse import urlencode

from base.asyncExchange import AsyncExchange
from enums import FiatTransactionType


class BinanceAsync(AsyncExchange):

    def __init__(
        self, key: str = None, secret: str = None, tz="UTC", name="Binance"
    ) -> None:
        super().__init__(
            key=key,
            secret=secret,
            password=None,
            name=name,
            url="https://api.binance.com",
            tz=tz,
        )

        if key:
            self._SESSION.headers.extend({"X-MBX-APIKEY": key})

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

        The endpoint for this request is GET "/api/v3/exchangeInfo".

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
        ENDPOINT = "/api/v3/exchangeInfo"

        # Build request parameters
        params = {
            "symbol": symbol,
            "symbols": symbols,
            "permissions": permissions,
            "showPermissionSets": show_permission_sets,
            "symboslStatus": symbol_status,
        }

        info: dict = await self._request(endPoint=ENDPOINT, params=params, sign=False)

        return info

    #
    # SIGNED API
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
        ENDPOINT = "/sapi/v3/asset/getUserAsset"

        params = {
            "asset": asset,
            "needBtcValuation": needBtcValuation,
        }

        resp: list[dict] = await self._request(
            endPoint=ENDPOINT, params=params, method="POST"
        )

        return resp

    async def fiat_deposit_withdrawal(
        self,
        transactionType: FiatTransactionType,
        since: datetime,
        until: datetime = None,
    ) -> list[dict]:
        """
        Fetches fiat deposit or withdrawal transactions within a specified date range.

        The endpoint for this request is GET "/sapi/v1/fiat/orders".

        https://developers.binance.com/docs/fiat/rest-api/Get-Fiat-Deposit-Withdraw-History

        Parameters
        ----------
        transactionType : FiatTransactionType
            Specifies the type of transaction to fetch.
        since : datetime
            The start datetime from which transactions should be retrieved.
        until : datetime, optional
            The end datetime up to which transactions should be retrieved. If not provided, the current time is
            used as the default, retrieving all transactions from `since` up to the present.

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

        ENDPOINT = "/sapi/v1/fiat/orders"  # UID 90000

        # unixtime
        start_ms, end_ms = self._parseTime(since, until)

        payload = {
            "transactionType": transactionType.value,
            "beginTime": start_ms,
            "endTime": end_ms,
            "rows": 500,
        }

        resp = await self._paginatedRequests(
            endPoint=ENDPOINT,
            params=payload,
        )

        return resp

    #
    # Request Methods
    #

    async def _paginatedRequests(
        self,
        endPoint: str,
        params: dict = None,
        rowsKey="rows",
        pageKey="page",
        dataKey="data",
        totalKey="total",
        method="GET",
    ):
        """
        Fetches data from a paginated API endpoint asynchronously.

        This function retrieves data from an API that returns paginated results.
        It sends requests to each page in parallel (after the first page), which
        improves performance over sequential requests. All results are collected
        and returned as a single list.

        Parameters
        ----------
        endPoint : str
            The URL of the API endpoint to which the requests are made.
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
        - This function assumes that the API follows a consistent structure for pagination, where a page number is specified,
          and the response includes both the `dataKey` containing the data items and the `totalKey` indicating the total number
          of pages.
        - The function avoids mutating the original `params` dictionary by copying it.
        """

        payload = params.copy()
        itemsPerRequest = payload[rowsKey]

        data = []

        # Make first request to know the total number of items to retrieve
        payload[pageKey] = 1
        resp = await self._request(endPoint=endPoint, params=payload, method=method)
        data.extend(resp[dataKey])

        # Make following requests asyncronously
        tasks = []
        for _ in range(itemsPerRequest, resp[totalKey] + 1, itemsPerRequest):
            payload[pageKey] += 1
            tasks.append(
                create_task(
                    self._request(endPoint=endPoint, params=payload, method=method)
                )
            )

        resp = await gather(*tasks)
        data.extend([x for r in resp for x in r[dataKey]])

        return data

    async def _request(
        self, endPoint: str, params: dict = None, sign=True, method="GET"
    ):
        if params is None:
            payload = dict()

        else:
            payload = self._preparePayload(params)

        if sign:
            # Adds recv and timestamp and generates signature
            payload["recvWindow"] = self._RECV_WINDOW
            payload["timestamp"] = str(int(datetime.now().timestamp() * 1000))
            payload["signature"] = self._sign(payload)

        async with self._SESSION.request(
            method=method, url=endPoint, params=payload
        ) as resp:

            print(resp.real_url)
            print(resp.headers)

            json: dict | list = await resp.json()

        return json

    def _sign(self, params):
        param_str = urlencode(params)
        return self._encrypt(param_str)
