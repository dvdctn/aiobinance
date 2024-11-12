# Async Binance API connector

## Description

`aiobinance` is an asynchronous lightweight Python client designed to interact with Binance's RESTful API. It provides **Smart Date Range** and **API Rate Limit Management**. This library is still in development and support for more endpoints will be implemented.

## Key Features

- **Async Support**: Designed for high-performance asynchronous operations using `asyncio`.
- **API Rate Limit Management**: Manage API rate limits specifically for every single endpoint by automatically tracking and controlling the rate at which requests are sent to the API. This ensures that your application stays within the allowed rate limits, preventing request rejections and potential service disruptions.
- **Smart Date Range Management**: This library simplifies working with large date ranges that may exceed the API's bounds by automatically splitting requests as needed. When a date range for a request is too large, the library breaks it into smaller, rate-limit-compliant requests and reassembles the results. This allows you to request broad date ranges in a single call, without worrying about rate limits or handling partial results.

## Installation

The module requires Python 3.10+ and an asynchronous environment to handle async functions. Necessary dependencies:

- [aiohttp](https://github.com/aio-libs/aiohttp)
- [certifi](https://github.com/certifi/python-certifi)
- [aiolimiter](https://github.com/mjpieters/aiolimiter)

## Getting Started

To initialize the `BinanceAsync` client, you need:

- **API Key** (optional)
- **API Secret** (optional)

```python
from binance import BinanceAsync
import asyncio

async def main():
    client = BinanceAsync(key="your-api-key", secret="your-secret-key")
    market_info = await client.marketInfo(symbol="BTCUSDT")
    print(market_info)

asyncio.run(main())
```

## Available Methods

### Public API

- **`marketInfo`**

  Retrieve exchange information with optional filters.

  ```python
  await client.marketInfo(symbol="BNBBTC")
  ```

- **`klines`**

  Retrieve kline/candlestick bars for a symbol.

  ```python
  await client.klines(
    symbol="BTCUSDT", # Can also be 'BTC/USDT' or 'BTC-USDT'
    interval='1h',
    since=datetime(2020, 1, 1),
    until=datetime(2023, 1, 1)
  )
  ```

### Signed API

- **`userAsset`**

  Retrieve user assets, optionally including BTC valuation.

  ```python
  assets = await client.userAsset(asset="BTC", needBtcValuation=True)
  ```

- **`spotTrades`**

  Retrieve spot trades for a specific symbol.

  ```python
  assets = await client.spotTrades(
      symbol="BTCUSDT",
      since=datetime(2023, 1, 1),
  )
  ```

- **`fiat_deposit_withdrawal`**

  Fetch fiat deposit/withdrawal records within a date range.

  ```python
  from datetime import datetime

  transactions = await client.fiat_deposit_withdrawal(
      transactionType=FiatTransactionType.DEPOSIT,
      since=datetime(2023, 1, 1),
      until=datetime(2023, 2, 1)
  )
  ```

## Notes

- **Error Handling**: Currently, basic error handling is implemented. Future improvements will address handling more specific error cases.

## License

This module is released under the MIT License.

## Contributing

Contributions are welcome! Please open issues for any bugs or feature requests and feel free to submit pull requests.

## Disclaimer

This project is in development and more methods will be added.

---
