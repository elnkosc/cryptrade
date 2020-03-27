import cbpro
from trade import *
import sys

# coinbase constants
TRANSACTION_FEE = 0.005  # transaction fee (percentage)


class CBTradeClient(TradeClient):
    def __init__(self, api_key, api_secret, api_pass):
        super().__init__()
        self._client = cbpro.AuthenticatedClient(api_key, api_secret, api_pass)

    def cancel_all(self, product):
        self._client.cancel_all(product.prod_id)


class CBProduct(Product):
    def __init__(self, auth_client, trading_currency, buying_currency, basic_amount):
        try:
            super().__init__(auth_client, trading_currency, buying_currency, basic_amount)
            self._prod_id = self._trading_currency + "-" + self._buying_currency

            products = self._auth_client.client.get_products()
            for product in products:
                if product["id"] == self._prod_id:
                    self._min_amount = float(product["base_min_size"])
                    self._min_price = float(product["quote_increment"])
                    break
            self._min_order_value = self._min_price

            if self._basic_amount < self._min_amount:
                raise AttributeError(f"Smallest value for {self._trading_currency} "
                                     f"trading amount on Coinbase is {self._min_amount}")

        except Exception:
            raise


class CBTicker(Ticker):
    def update(self):
        try:
            product_ticker = self._auth_client.client.get_product_ticker(self._product.prod_id)
            if "trade_id" in product_ticker:
                self._bid = float(product_ticker["bid"])
                self._ask = float(product_ticker["ask"])
                self._price = float(product_ticker["price"])

        except Exception:
            pass


class CBOrder(Order):
    def __init__(self, auth_client, product, order_type, price, amount):
        try:
            super().__init__(auth_client, product, order_type, price, amount)

            if self._product.valid(self._amount, self._price):
                result = self._auth_client.client.place_limit_order(
                    self._product.prod_id,
                    self._order_type,
                    self._price,
                    self._amount,
                    time_in_force="GTC")
            else:
                result = {}

            if "id" in result:
               self._order_id = result["id"]
               self._status = result["status"]
               self._filled_size = float(result["filled_size"])
               self._executed_value = float(result["executed_value"])
               self._settled = bool(result["settled"])
               self._message = "order creation successful"
            else:
                self._order_id = ""
                self._status = "error"
                self._filled_size = 0.0
                self._executed_value = 0.0
                self._settled = True

                if "message" in result:
                    self._message = result["message"]
                else:
                    self._message = "order creation failed: unknown error"
        except:
            self._order_id = ""
            self._status = "error"
            self._filled_size = 0.0
            self._executed_value = 0.0
            self._settled = True
            self._message = f"limit order exception: {sys.exc_info()[0]}"

    def status(self):
        try:
            order_update = self._auth_client.client.get_order(self._order_id)

            if "message" not in order_update:
                self._status = order_update["status"]
                self._filled_size = float(order_update["filled_size"])
                self._executed_value = float(order_update["executed_value"])
                self._settled = bool(order_update["settled"])
            else:
                self._status = "error"
                self._message = order_update["message"]
                self._settled = True
        except:
            self._status = "error"
            self._message = f"get order exception: {sys.exc_info()[0]}"
            self._settled = True

        return self._settled

    def cancel(self):
        super().cancel()
        self._auth_client.client.cancel_order(self.order_id)


class CBAccount(Account):
    def update(self, exchange_rate):
        for sub_account in self._auth_client.client.get_accounts():
            if sub_account["currency"] == self._product.buying_currency:
                self._bc_amount = float(sub_account["balance"])
            elif sub_account["currency"] == self._product.trading_currency:
                self._tc_amount = float(sub_account["balance"])
                self._value = self._tc_amount * exchange_rate


class CBAccumulator(Accumulator):
    def __init__(self, name):
        super().__init__(name)
        self._fee = TRANSACTION_FEE


class CBApiCreator(ApiCreator):
    def create_trade_client(self, api_key, api_secret, api_pass):
        return CBTradeClient(api_key, api_secret, api_pass)

    def create_product(self, auth_client, trading_currency, buying_currency, basic_amount):
        return CBProduct(auth_client, trading_currency, buying_currency, basic_amount)

    def create_ticker(self, auth_client, product):
        return CBTicker(auth_client, product)

    def create_order(self, auth_client, product, order_type, price, amount):
        return CBOrder(auth_client, product, order_type, price, amount)

    def create_account(self, auth_client, product):
        return CBAccount(auth_client, product)

    def create_accumulator(self, name):
        return CBAccumulator(name)
