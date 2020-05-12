from binance.client import Client as BinClient

from cryptrade.exceptions import AuthenticationError, ProductError
from cryptrade.exchange_api import TradeClient, Product, Ticker, Order, Account, ApiCreator

import sys
from datetime import datetime


def map_product(trading_currency: str, buying_currency: str) -> str:
    return trading_currency + buying_currency


def map_to_exchange_currency(currency: str) -> str:
    return currency


def map_from_exchange_currency(currency: str) -> str:
    return currency


class BinTradeClient(TradeClient):
    def __init__(self, credentials: dict) -> None:
        super().__init__()

        if "binance" in credentials and \
                "api_key" in credentials["binance"] and \
                "api_secret" in credentials["binance"]:
            api_key = credentials["binance"]["api_key"]
            api_secret = credentials["binance"]["api_secret"]
            try:
                self._client = BinClient(api_key, api_secret)
            except Exception:
                raise AuthenticationError("invalid Binance API key and/or secret")
        else:
            try:
                self._client = BinClient()
            except Exception:
                raise AuthenticationError("Could not create non-authenticated Client for Binance")


class BinProduct(Product):
    def __init__(self, auth_client: BinTradeClient, trading_currency: str, buying_currency: str) -> None:
        try:
            super().__init__(auth_client, trading_currency, buying_currency)
            self._prod_id = map_product(self._trading_currency, self._buying_currency)

            symbol_info = self._auth_client.client.get_symbol_info(self._prod_id)
            for f in symbol_info["filters"]:
                if f["filterType"] == "MIN_NOTIONAL":
                    self._min_order_value = float(f["minNotional"])
                elif f["filterType"] == "PRICE_FILTER":
                    self._min_price = float(f["minPrice"])
                elif f["filterType"] == "LOT_SIZE":
                    self._min_amount = float(f["minQty"])

        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Binance")


class BinTicker(Ticker):
    def __init__(self, auth_client: BinTradeClient, product: BinProduct) -> None:
        super().__init__(auth_client, product)
        self._name = "Binance"

    def update(self) -> None:
        try:
            product_ticker = self._auth_client.client.get_ticker(symbol=self._product.prod_id)
            self._bid = float(product_ticker["bidPrice"])
            self._ask = float(product_ticker["askPrice"])
            self._price = float(product_ticker["lastPrice"])
            self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore exceptions
            pass


class BinOrder(Order):
    def __init__(self, auth_client: BinTradeClient, product: BinProduct, order_type: str,
                 price: float, amount: float) -> None:
        try:
            super().__init__(auth_client, product, order_type, price, amount)

            if not self._product.valid(self._amount, self._price):
                raise AttributeError("Invalid amount/price for order")

            if self._order_type == "buy":
                result = self._auth_client.client.order_limit_buy(
                    symbol=self._product.prod_id,
                    quantity=self._amount,
                    price=str(self._price))
            elif self._order_type == "sell":
                result = self._auth_client.client.order_limit_sell(
                    symbol=self._product.prod_id,
                    quantity=self._amount,
                    price=str(self._price))
            else:
                raise AttributeError(f"Invalid order-type: {self._order_type}")

            if "orderId" in result:
                self._created = True
                self._order_id = result["orderId"]
                self._status = result["status"]
                self._filled_size = float(result["executedQty"])
                self._executed_value = self._filled_size * self._price
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
            order_update = self._auth_client.client.get_order(symbol=self._product.prod_id, orderId=self._order_id)

            if "orderId" in order_update:
                self._status = order_update["status"]
                self._filled_size = float(order_update["executedQty"])
                self._executed_value = self._filled_size * self._price
                if self._status in ["CANCELED", "FILLED", "EXPIRED", "REJECTED"]:
                    self._settled = True
            else:
                # order (most likely) not found, set settled flag
                self._settled = True
                raise AttributeError("order not found")

        except Exception:
            self._status = "error"
            self._message = f"order update exception: {sys.exc_info()[1]}"

        if self._settled:
            self._timestamp = datetime.now().replace(microsecond=0)

        return self._settled

    def cancel(self):
        if not self._settled:
            try:
                super().cancel()
                self._auth_client.client.cancel_order(symbol=self._product.prod_id, orderId=self._order_id)
            except Exception:
                self._message = "Cancellation failed"


class BinAccount(Account):
    def __init__(self, auth_client: BinTradeClient) -> None:
        super().__init__(auth_client)
        self._name = "Binance"

    def update(self) -> None:
        try:
            account = self._auth_client.client.get_account()
            self._balance.clear()
            if "balances" in account:
                for balance in account["balances"]:
                    c = map_from_exchange_currency(balance["asset"].upper())
                    amount = float(balance["free"]) + float(balance["locked"])
                    if amount > 0:
                        self._balance[c] = amount
            self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore exceptions
            pass


class BinApiCreator(ApiCreator):
    _maker_fee = 0.001
    _taker_fee = 0.002

    @staticmethod
    def create_trade_client(credentials: dict) -> BinTradeClient:
        return BinTradeClient(credentials)

    @staticmethod
    def create_product(auth_client: BinTradeClient, trading_currency: str, buying_currency: str) -> BinProduct:
        return BinProduct(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client: BinTradeClient, product: BinProduct) -> BinTicker:
        return BinTicker(auth_client, product)

    @staticmethod
    def create_order(auth_client: BinTradeClient, product: BinProduct, order_type: str, price: float,
                     amount: float) -> BinOrder:
        return BinOrder(auth_client, product, order_type, price, amount)

    @staticmethod
    def create_account(auth_client: BinTradeClient) -> BinAccount:
        return BinAccount(auth_client)
