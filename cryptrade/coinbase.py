import cbpro

from cryptrade.exceptions import AuthenticationError, ProductError
from cryptrade.exchange_api import TradeClient, Currency, Product, Ticker, Order, Account, ApiCreator

import sys
from datetime import datetime


class CBTradeClient(TradeClient):
    def __init__(self, credentials: dict) -> None:
        super().__init__()

        if "coinbase" in credentials and \
                "api_key" in credentials["coinbase"] and \
                "api_secret" in credentials["coinbase"] and \
                "api_pass" in credentials["coinbase"]:
            api_key = credentials["coinbase"]["api_key"]
            api_secret = credentials["coinbase"]["api_secret"]
            api_pass = credentials["coinbase"]["api_pass"]
            try:
                self._client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)
            except Exception:
                raise AuthenticationError("invalid Coinbase API key, secret, and/or password")

        else:
            try:
                self._client = cbpro.PublicClient()
            except:
                raise AuthenticationError("Could not create non-authenticated Client for Coinbase Pro")


class CBCurrency(Currency):
    _currency_map = {}

    def __init__(self, currency_id: str) -> None:
        super().__init__(currency_id)


class CBProduct(Product):
    def __init__(self, auth_client: CBTradeClient, trading_currency: CBCurrency, buying_currency: CBCurrency) -> None:
        try:
            super().__init__(auth_client, trading_currency, buying_currency)

            products = self._auth_client.client.get_products()
            for product in products:
                if product["id"] == self.prod_id:
                    self._min_order_amount = float(product["base_min_size"])
                    self._min_order_price = float(product["quote_increment"])
                    self._order_price_precision = float(product["quote_increment"])
                    self._order_amount_precision = float(product["base_increment"])
                    self._min_order_value = self._min_order_amount * self._min_order_price
                    break
            self._min_order_value = self._min_order_price

        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Coinbase Pro")

    @property
    def prod_id(self) -> str:
        return str(self._trading_currency) + "-" + str(self._buying_currency)


class CBTicker(Ticker):
    def __init__(self, auth_client: CBTradeClient, product: CBProduct) -> None:
        super().__init__(auth_client, product)
        self._name = "Coinbase Pro"

    def update(self) -> None:
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
    def __init__(self, auth_client: CBTradeClient, product: CBProduct, order_type: str,
                 price: float, amount: float) -> None:
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

    def status(self) -> bool:
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

    def cancel(self) -> None:
        if not self._settled:
            try:
                super().cancel()
                self._auth_client.client.cancel_order(self.order_id)
            except Exception:
                self._message = "Cancellation failed"


class CBAccount(Account):
    def __init__(self, auth_client: CBTradeClient) -> None:
        super().__init__(auth_client)
        self._name = "Coinbase Pro"

    def update(self) -> None:
        try:
            self._balance.clear()
            for sub_account in self._auth_client.client.get_accounts():
                c = CBCurrency.map_from_exchange_currency(sub_account["currency"].upper())
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
    def create_trade_client(credentials: dict) -> CBTradeClient:
        return CBTradeClient(credentials)

    @staticmethod
    def create_currency(currency_id: str) -> CBCurrency:
        return CBCurrency(currency_id)

    @staticmethod
    def create_product(auth_client: CBTradeClient, trading_currency: CBCurrency,
                       buying_currency: CBCurrency) -> CBProduct:
        return CBProduct(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client: CBTradeClient, product: CBProduct) -> CBTicker:
        return CBTicker(auth_client, product)

    @staticmethod
    def create_order(auth_client: CBTradeClient, product: CBProduct, order_type: str, price: float,
                     amount: float) -> CBOrder:
        return CBOrder(auth_client, product, order_type, price, amount)

    @staticmethod
    def create_account(auth_client: CBTradeClient) -> CBAccount:
        return CBAccount(auth_client)
