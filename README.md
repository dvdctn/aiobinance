# Async Binance API connector

## Description

`BinanceAsync` is an asynchronous lightweight Python client designed to interact with Binance's RESTful API. It provides methods for retrieving market information, managing user assets, and handling fiat transactions. This module is still in early development and is subject to change.

### Features

- **Async Support**: Designed for high-performance asynchronous operations using `asyncio`.

## Installation

The module requires Python 3.7+ and an asynchronous environment to handle async functions. Install necessary dependencies (e.g., `aiohttp` for making async HTTP requests).

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

### Signed API

- **`userAsset`**
  Retrieve user assets, optionally including BTC valuation.

  ```python
  assets = await client.userAsset(asset="BTC", needBtcValuation=True)
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
- **Rate Limits**: Ensure your requests adhere to Binance's rate limits to avoid API restrictions.

## License

This module is released under the MIT License.

## Contributing

Contributions are welcome! Please open issues for any bugs or feature requests and feel free to submit pull requests.

## Disclaimer

This project is in early development and not yet ready for production use. API functionality may change without notice.

---
