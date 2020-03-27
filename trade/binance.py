from binance.client import Client as BinClient
from trade import *
import sys

# global binance constants
TRANSACTION_FEE = 0.001  # transaction fee (percentage)


class BinTradeClient(TradeClient):
    def __init__(self, api_key, api_secret):
        super().__init__()
        self._client = BinClient(api_key, api_secret)

    def cancel_all(self, product):
        # not available on binance
        pass


class BinProduct(Product):
    def __init__(self, auth_client, trading_currency, buying_currency, basic_amount):
        try:
            super().__init__(auth_client, trading_currency, buying_currency, basic_amount)
            self._prod_id = self._trading_currency + self._buying_currency

            symbol_info = self._auth_client.client.get_symbol_info(self._prod_id)
            for f in symbol_info["filters"]:
                if f["filterType"] == "MIN_NOTIONAL":
                    self._min_order_value = float(f["minNotional"])
                elif f["filterType"] == "PRICE_FILTER":
                    self._min_price = float(f["minPrice"])
                elif f["filterType"] == "LOT_SIZE":
                    self._min_amount = float(f["minQty"])

            if self._basic_amount < self._min_amount:
                raise AttributeError(f"Smallest value for {self._trading_currency} "
                                     f"trading amount on Binance is {self._min_amount}")

        except Exception:
            raise


class BinTicker(Ticker):
    def update(self):
        try:
            product_ticker = self._auth_client.client.get_ticker(symbol=self._product.prod_id)
            self._bid = float(product_ticker["bidPrice"])
            self._ask = float(product_ticker["askPrice"])
            self._price = float(product_ticker["lastPrice"])

        except Exception:
            pass


class BinOrder(Order):
    def __init__(self, auth_client, product, order_type, price, amount):
        try:
            super().__init__(auth_client, product, order_type, price, amount)

            if self._product.valid(self._amount, self._price):
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
            else:
                result = {}

            if "orderId" in result:
                self._order_id = result["orderId"]
                self._status = result["status"]
                self._filled_size = float(result["executedQty"])
                self._executed_value = self._filled_size * self._price
                self._settled = False
                self._message = "order creation successful"
            else:
                self._order_id = ""
                self._status = "error"
                self._filled_size = 0.0
                self._executed_value = 0.0
                self._settled = True
                self._message = "order creation failed: unknown error"

        except Exception:
            self._order_id = ""
            self._status = "error"
            self._filled_size = 0.0
            self._executed_value = 0.0
            self._settled = True
            self._message = f"limit order exception: {sys.exc_info()[0]}"

    def status(self):
        try:
            order_update = self._auth_client.client.get_order(symbol=self._product.prod_id, orderId=self._order_id)

            if "orderId" in order_update:
                self._status = order_update["status"]
                self._filled_size = float(order_update["executedQty"])
                self._executed_value = self._filled_size * self._price
                if self._status in ["CANCELED", "FILLED", "EXPIRED", "REJECTED"]:
                    self._settled = True
            else:
                self._status = "error"
                self._message = order_update["message"]
                self._settled = True

        except Exception:
            self._status = "error"
            self._message = f"order update exception: {sys.exc_info()[0]}"
            self._settled = True

        return self._settled

    def cancel(self):
        super().cancel()
        try:
            self._auth_client.client.cancel_order(symbol=self._product.prod_id, orderId=self._order_id)
        except Exception:
            self._message = "Cancellation failed"


class BinAccount(Account):
    def update(self, exchange_rate):
        asset = self._auth_client.client.get_asset_balance(asset=self._product.buying_currency)
        if asset is not None:
            self._bc_amount = float(asset["free"])
        else:
            self._bc_amount = 0.0

        asset = self._auth_client.client.get_asset_balance(asset=self._product.trading_currency)
        if asset is not None:
            self._tc_amount = float(asset["free"])
        else:
            self._tc_amount = 0.0

        self._value = self._tc_amount * exchange_rate


class BinAccumulator(Accumulator):
    def __init__(self, name):
        super().__init__(name)
        self._fee = TRANSACTION_FEE


class BinApiCreator(ApiCreator):
    def create_trade_client(self, api_key, api_secret, api_pass=None):
        return BinTradeClient(api_key, api_secret)

    def create_product(self, auth_client, trading_currency, buying_currency, basic_amount):
        return BinProduct(auth_client, trading_currency, buying_currency, basic_amount)

    def create_ticker(self, auth_client, product):
        return BinTicker(auth_client, product)

    def create_order(self, auth_client, product, order_type, price, amount):
        return BinOrder(auth_client, product, order_type, price, amount)

    def create_account(self, auth_client, product):
        return BinAccount(auth_client, product)

    def create_accumulator(self, name):
        return BinAccumulator(name)
