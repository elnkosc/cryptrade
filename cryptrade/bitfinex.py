import bfxapi.client
import bfxapi.models.notification
from bfxapi.models.order import OrderType

from cryptrade.exchange_api import TradeClient, Currency, Product, Ticker, Order, Account, ApiCreator
from cryptrade.exceptions import AuthenticationError, ProductError

import sys
from datetime import datetime
import asyncio


class BfxTradeClient(TradeClient):
    def __init__(self, credentials: dict) -> None:
        super().__init__()

        if "bitfinex" in credentials and \
                "api_key" in credentials["bitfinex"] and \
                "api_secret" in credentials["bitfinex"]:
            api_key = credentials["bitfinex"]["api_key"]
            api_secret = credentials["bitfinex"]["api_secret"]
            try:
                # for product information v1 of the API is required, the rest is done on v2
                self._client = {
                    "v1": bfxapi.client.BfxRest(api_key, api_secret, host="https://api.bitfinex.com/v1"),
                    "v2": bfxapi.client.BfxRest(api_key, api_secret, host="https://api.bitfinex.com/v2")}
            except Exception:
                raise AuthenticationError("invalid Bitfinex API key and/or secret")
        else:
            try:
                # for product information v1 of the API is required, the rest is done on v2
                self._client = {
                    "v1": bfxapi.client.BfxRest(API_KEY=None, API_SECRET=None, host="https://api.bitfinex.com/v1"),
                    "v2": bfxapi.client.BfxRest(API_KEY=None, API_SECRET=None, host="https://api.bitfinex.com/v2")}
            except Exception:
                raise AuthenticationError("Could not create non-authenticated Client for Bitfinex")


class BfxCurrency(Currency):
    _currency_map = {
        "USDT": "UST",
        "TUSD": "TSD"}

    def __init__(self, currency_id: str) -> None:
        super().__init__(currency_id)


class BfxProduct(Product):
    def __init__(self, auth_client: BfxTradeClient, trading_currency: BfxCurrency,
                 buying_currency: BfxCurrency) -> None:
        try:
            super().__init__(auth_client, trading_currency, buying_currency)

            product_list = asyncio.run(self._auth_client.client["v1"].fetch("symbols_details"))
            product_found = False
            for product in product_list:
                if product["pair"] == self.prod_id.lower():
                    self._min_order_amount = float(product["minimum_order_size"])
                    self._min_order_price = 0
                    self._min_order_value = 0
                    self._order_price_precision = None
                    self._order_amount_precision = None
                    product_found = True
                    break

            if not product_found:
                raise ProductError(f"{trading_currency}/{buying_currency} not supported on Bitfinex")

        except ProductError:
            raise
        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Bitfinex")

    @property
    def prod_id(self) -> str:
        return self._trading_currency.exchange_currency_id + self._buying_currency.exchange_currency_id


class BfxTicker(Ticker):
    def __init__(self, auth_client: BfxTradeClient, product: BfxProduct) -> None:
        super().__init__(auth_client, product)
        self._name = "Bitfinex"

    async def async_update(self) -> None:
        try:
            product_ticker = await self._auth_client.client["v2"].get_public_ticker("t" + self._product.prod_id)
            self._bid = product_ticker[0]
            self._ask = product_ticker[2]
            self._price = product_ticker[6]
            self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore exceptions
            pass

    def update(self) -> None:
        asyncio.run(self.async_update())

    async def produce(self, interval: int) -> None:
        while True:
            await self.async_update()
            await self.notify()
            await asyncio.sleep(interval)


class BfxOrder(Order):
    def __init__(self, auth_client: BfxTradeClient, product: BfxProduct, order_type: str,
                 price: float, amount: float) -> None:
        try:
            super().__init__(auth_client, product, order_type, price, amount)

            if not self._product.valid(self._amount, self._price):
                raise AttributeError("Invalid amount/price for order")

            if self._order_type == "buy":
                order_result = asyncio.run(self._auth_client.client["v2"].submit_order(
                    "t"+self._product.prod_id, self._price, self._amount, market_type=OrderType.EXCHANGE_LIMIT))
            elif self._order_type == "sell":
                order_result = asyncio.run(self._auth_client.client["v2"].submit_order(
                    "t"+self._product.prod_id, self._price, -1 * self._amount, market_type=OrderType.EXCHANGE_LIMIT))
            else:
                raise AttributeError("invalid order-type (buy/sell)")

            if order_result.is_success():
                self._created = True
                self._order_id = order_result.notify_info[0].id
                self._status = order_result.notify_info[0].status
                self._filled_size = 0.0
                self._executed_value = 0.0
                self._settled = False
                self._message = "order creation successful"
            else:
                raise AttributeError("unknown error")

        except Exception:
            self._order_id = ""
            self._status = "error"
            self._filled_size = 0.0
            self._executed_value = 0.0
            self._settled = True
            self._message = f"Invalid order: {sys.exc_info()[1]}"

    def status(self) -> bool:
        try:
            order_update = asyncio.run(self._auth_client.client["v2"].submit_update_order(self._order_id))

            if order_update.is_success():
                self._status = order_update.notify_info.status
                self._filled_size = abs(order_update.notify_info.amount_filled)
                self._executed_value = self._filled_size * self._price
                if "CANCELED" in self._status or "EXECUTED" in self._status:
                    self._settled = True
            else:
                self._settled = True
                raise AttributeError("order update failed")

        except Exception:
            # order removed by external factor
            self._settled = True
            self._status = "unknown"
            self._message = f"get order exception: {sys.exc_info()[1]}"

        if self._settled:
            self._timestamp = datetime.now().replace(microsecond=0)

        return self._settled

    def cancel(self) -> None:
        if not self._settled:
            try:
                super().cancel()
                asyncio.run(self._auth_client.client["v2"].submit_cancel_order(self._order_id))
            except Exception:
                self._message = "Cancellation failed"


class BfxAccount(Account):
    def __init__(self, auth_client: BfxTradeClient) -> None:
        super().__init__(auth_client)
        self._name = "Bitfinex"

    async def async_update(self) -> None:
        try:
            account_info = await self._auth_client.client["v2"].get_wallets()
            self._balance.clear()
            for wallet in account_info:
                c = BfxCurrency.map_from_exchange_currency(wallet.currency.upper())
                if wallet.balance > 0:
                    self._balance[c] = wallet.balance
            self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore
            pass

    def update(self) -> None:
        asyncio.run(self.async_update())

    async def produce(self, interval: int) -> None:
        while True:
            await self.async_update()
            await self.notify()
            await asyncio.sleep(interval)


class BfxApiCreator(ApiCreator):
    _maker_fee = 0.001
    _taker_fee = 0.002

    @staticmethod
    def create_trade_client(credentials: dict) -> BfxTradeClient:
        return BfxTradeClient(credentials)

    @staticmethod
    def create_currency(currency_id: str) -> BfxCurrency:
        return BfxCurrency(currency_id)

    @staticmethod
    def create_product(auth_client: BfxTradeClient, trading_currency: BfxCurrency,
                       buying_currency: BfxCurrency) -> BfxProduct:
        return BfxProduct(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client: BfxTradeClient, product: BfxProduct) -> BfxTicker:
        return BfxTicker(auth_client, product)

    @staticmethod
    def create_order(auth_client: BfxTradeClient, product: BfxProduct, order_type: str, price: float,
                     amount: float) -> BfxOrder:
        return BfxOrder(auth_client, product, order_type, price, amount)

    @staticmethod
    def create_account(auth_client: BfxTradeClient) -> BfxAccount:
        return BfxAccount(auth_client)
