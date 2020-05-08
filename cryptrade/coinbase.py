import cbpro

from cryptrade.exceptions import AuthenticationError, ProductError, ParameterError
from cryptrade.exchange_api import TradeClient, Product, Ticker, Order, Account, ApiCreator

import sys
from datetime import datetime


def map_product(trading_currency, buying_currency):
    return trading_currency + "-" + buying_currency


def map_to_exchange_currency(currency):
    return currency


def map_from_exchange_currency(currency):
    return currency


class CBTradeClient(TradeClient):
    def __init__(self, credentials):
        super().__init__()

        if "coinbase" in credentials and \
                "api_key" in credentials["coinbase"] and \
                "api_secret" in credentials["coinbase"] and \
                "api_pass" in credentials["coinbase"]:
            api_key = credentials["coinbase"]["api_key"]
            api_secret = credentials["coinbase"]["api_secret"]
            api_pass = credentials["coinbase"]["api_pass"]
        else:
            raise ParameterError("missing or invalid credentials for Coinbase Pro")

        try:
            self._client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)
        except Exception:
            raise AuthenticationError("invalid Coinbase API key, secret, and/or password")


class CBProduct(Product):
    def __init__(self, auth_client, trading_currency, buying_currency):
        try:
            super().__init__(auth_client, trading_currency, buying_currency)
            self._prod_id = map_product(self._trading_currency, self._buying_currency)

            products = self._auth_client.client.get_products()
            for product in products:
                if product["id"] == self._prod_id:
                    self._min_amount = float(product["base_min_size"])
                    self._min_price = float(product["quote_increment"])
                    break
            self._min_order_value = self._min_price

        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Coinbase Pro")


class CBTicker(Ticker):
    def __init__(self, auth_client, product):
        super().__init__(auth_client, product)
        self._name = "Coinbase Pro"

    def update(self):
        try:
            product_ticker = self._auth_client.client.get_product_ticker(self._product.prod_id)

            if "trade_id" in product_ticker:
                self._bid = float(product_ticker["bid"])
                self._ask = float(product_ticker["ask"])
                self._price = float(product_ticker["price"])
                self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore exceptions
            pass


class CBOrder(Order):
    def __init__(self, auth_client, product, order_type, price, amount):
        try:
            super().__init__(auth_client, product, order_type, price, amount)

            if not self._product.valid(self._amount, self._price):
                raise AttributeError("Invalid amount/price for order")

            result = self._auth_client.client.place_limit_order(
                self._product.prod_id,
                self._order_type,
                self._price,
                self._amount,
                time_in_force="GTC")

            if "id" in result:
                self._created = True
                self._order_id = result["id"]
                self._status = result["status"]
                self._filled_size = float(result["filled_size"])
                self._executed_value = float(result["executed_value"])
                self._settled = bool(result["settled"])
                self._message = "order creation successful"
            else:
                if "message" in result:
                    raise AttributeError(result["message"])
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
            order_update = self._auth_client.client.get_order(self._order_id)

            if "message" not in order_update:
                self._status = order_update["status"]
                self._filled_size = float(order_update["filled_size"])
                self._executed_value = float(order_update["executed_value"])
                self._settled = bool(order_update["settled"])
            else:
                # order not found, set settled flag
                self._settled = True
                raise AttributeError(order_update["message"])

        except Exception:
            self._status = "error"
            self._message = f"get order exception: {sys.exc_info()[1]}"

        if self._settled:
            self._timestamp = datetime.now().replace(microsecond=0)

        return self._settled

    def cancel(self):
        if not self._settled:
            try:
                super().cancel()
                self._auth_client.client.cancel_order(self.order_id)
            except Exception:
                self._message = "Cancellation failed"


class CBAccount(Account):
    def __init__(self, auth_client):
        super().__init__(auth_client)
        self._name = "Coinbase Pro"

    def update(self):
        try:
            self._balance.clear()
            for sub_account in self._auth_client.client.get_accounts():
                c = map_from_exchange_currency(sub_account["currency"].upper())
                if float(sub_account["balance"]) > 0:
                    self._balance[c] = float(sub_account["balance"])
            self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore
            pass


class CBApiCreator(ApiCreator):
    _maker_fee = 0.005
    _taker_fee = 0.005

    @staticmethod
    def create_trade_client(credentials):
        return CBTradeClient(credentials)

    @staticmethod
    def create_product(auth_client, trading_currency, buying_currency):
        return CBProduct(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client, product):
        return CBTicker(auth_client, product)

    @staticmethod
    def create_order(auth_client, product, order_type, price, amount):
        return CBOrder(auth_client, product, order_type, price, amount)

    @staticmethod
    def create_account(auth_client):
        return CBAccount(auth_client)
