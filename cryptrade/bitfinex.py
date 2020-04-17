import bfxapi.client
import bfxapi.models.notification
from bfxapi.models.order import OrderType
from cryptrade import *
import sys
import time
import asyncio

# bitfinex constants
MAKER_FEE = 0.001  # transaction fee (percentage)
TAKER_FEE = 0.002


def map_currency(currency):
    if currency == "USDT":
        c = "UST"
    elif currency == "TUSD":
        c = "TSD"
    else:
        c = currency
    return currency

def map_product(trading_currency, buying_currency):
    return map_currency(trading_currency) + map_currency(buying_currency)


class BfxTradeClient(TradeClient):
    def __init__(self, credentials):
        super().__init__()

        if "bitfinex" in credentials and \
                "api_key" in credentials["bitfinex"] and \
                "api_secret" in credentials["bitfinex"]:
            api_key = credentials["bitfinex"]["api_key"]
            api_secret = credentials["bitfinex"]["api_secret"]
        else:
            raise ParameterError("missing or invalid credentials for Kraken")

        try:
            # for product information v1 of the API is required, the rest is done on v2
            self._client = {
                "v1": bfxapi.client.BfxRest(api_key, api_secret, host="https://api.bitfinex.com/v1"),
                "v2": bfxapi.client.BfxRest(api_key, api_secret, host="https://api.bitfinex.com/v2")}
        except Exception:
            raise AuthenticationError("invalid Bitfinex API key and/or secret")


class BfxProduct(Product):
    def __init__(self, auth_client, trading_currency, buying_currency):
        try:
            super().__init__(auth_client, trading_currency, buying_currency)
            self._prod_id = map_product(self._trading_currency, self._buying_currency)

            product_list = asyncio.run(self._auth_client.client["v1"].fetch("symbols_details"))
            product_found = False
            for product in product_list:
                if product["pair"] == self._prod_id.lower():
                    self._min_amount = float(product["minimum_order_size"])
                    self._min_price = 0
                    self._min_order_value = 0
                    product_found = True
                    break

            if not product_found:
                raise ProductError(f"{trading_currency}/{buying_currency} not supported on Bitfinex")

        except ProductError:
            raise
        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Bitfinex")


class BfxTicker(Ticker):
    def update(self):
        try:
            product_ticker = asyncio.run(self._auth_client.client["v2"].get_public_ticker("t" + self._product.prod_id))
            self._bid = product_ticker[0]
            self._ask = product_ticker[2]
            self._price = product_ticker[6]
            self._timestamp = time.time()

        except Exception:
            # ignore exceptions
            pass

    async def start(self):
        while True:
            # not possible to use update as get_public_ticker is async function that is called with async.run()
            try:
                product_ticker = await self._auth_client.client["v2"].get_public_ticker("t" + self._product.prod_id)
                self._bid = product_ticker[0]
                self._ask = product_ticker[2]
                self._price = product_ticker[6]
                self._timestamp = time.time()

                yield self

            except Exception:
                # ignore exceptions
                pass


class BfxOrder(Order):
    def __init__(self, auth_client, product, order_type, price, amount):
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

    def status(self):
        try:
            order_update = asyncio.run(self._auth_client.client["v2"].submit_update_order(self._order_id))

            if order_update.is_sucess():
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

        return self._settled

    def cancel(self):
        if not self._settled:
            try:
                super().cancel()
                asyncio.run(self._auth_client.client["v2"].submit_cancel_order(self._order_id))
            except Exception:
                self._message = "Cancellation failed"


class BfxAccount(Account):
    def update(self):
        try:
            account_info = asyncio.run(self._auth_client.client["v2"].get_wallets())
            for wallet in account_info:
                if wallet.currency == map_currency(self._product.buying_currency):
                    self._bc_amount = wallet.balance
                elif wallet.currency == map_currency(self._product.trading_currency):
                    self._tc_amount = wallet.balance

        except Exception:
            # ignore
            pass

    async def start(self):
        while True:
            try:
                account_info = await self._auth_client.client["v2"].get_wallets()
                for wallet in account_info:
                    if wallet.currency == map_currency(self._product.buying_currency):
                        self._bc_amount = wallet.balance
                    elif wallet.currency == map_currency(self._product.trading_currency):
                        self._tc_amount = wallet.balance
                yield self

            except Exception:
                # ignore
                pass


class BfxApiCreator(ApiCreator):
    def create_trade_client(self, credentials):
        return BfxTradeClient(credentials)

    def create_product(self, auth_client, trading_currency, buying_currency):
        return BfxProduct(auth_client, trading_currency, buying_currency)

    def create_ticker(self, auth_client, product):
        return BfxTicker(auth_client, product)

    def create_order(self, auth_client, product, order_type, price, amount):
        return BfxOrder(auth_client, product, order_type, price, amount)

    def create_account(self, auth_client, product):
        return BfxAccount(auth_client, product)

    def create_transaction_monitor(self, name):
        return TransactionMonitor(name, MAKER_FEE)
