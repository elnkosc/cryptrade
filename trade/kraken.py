import krakenex
from trade import *
import sys

# coinbase constants
MAKER_FEE = 0.0016  # transaction fee (percentage)
TAKER_FEE = 0.0026


def map_currency(currency):
    if currency == "XXBT":
        return "BTC"
    elif currency == "XETH":
        return "ETH"
    elif currency == "ZEUR":
        return "EUR"
    elif currency == "ZUSD":
        return "USD"
    elif currency == "ZJPY":
        return "JPY"
    elif currency == "ZGBP":
        return "GBP"
    elif currency == "ZCAD":
        return "CAD"
    elif currency == "XZEC":
        return "ZEC"
    elif currency == "XXRP":
        return "XRP"
    elif currency == "XXMR":
        return "XMR"
    elif currency == "XXLM":
        return "XLM"
    elif currency == "XXDG":
        return "XDG"
    elif currency == "XXBT":
        return "XBT"
    else:
        return currency


class KrakenTradeClient(TradeClient):
    def __init__(self, credentials):
        super().__init__()

        if "kraken" in credentials and \
                "api_key" in credentials["kraken"] and \
                "api_secret" in credentials["kraken"]:
            api_key = credentials["kraken"]["api_key"]
            api_secret = credentials["kraken"]["api_secret"]
        else:
            raise AttributeError("missing or invalid credentials for kraken")

        try:
            self._client = krakenex.API(api_key, api_secret)
        except Exception:
            raise

    def cancel_all(self, product):
        # not supported on kraken
        pass


class KrakenProduct(Product):

    def __init__(self, auth_client, trading_currency, buying_currency):
        try:
            super().__init__(auth_client, trading_currency, buying_currency)
            self._prod_id = self._trading_currency + self._buying_currency
            product = self._auth_client.client.query_public("AssetPairs", {"pair": f"{self._prod_id}"})

            if "result" in product:
                for k, v in product["result"].items():
                    self._min_amount = 1 / 10 ** v["lot_decimals"]
                    self._min_price = 1 / 10 ** v["pair_decimals"]
                    self._min_order_value = 0
            else:
                print(self._prod_id)
                raise AttributeError(product["error"][0])

        except Exception:
            raise


class KrakenTicker(Ticker):
    def update(self):
        try:
            product_ticker = self._auth_client.client.query_public("Ticker", {"pair": f"{self._product.prod_id}"})
            if "result" in product_ticker:
                for k, v in product_ticker["result"].items():
                    self._bid = float(v["b"][0])
                    self._ask = float(v["a"][0])
                    self._price = float(v["c"][0])
            else:
                raise AttributeError(product_ticker["error"][0])

        except Exception:
            # ignore exceptions
            pass


class KrakenOrder(Order):
    def __init__(self, auth_client, product, order_type, price, amount):
        try:
            super().__init__(auth_client, product, order_type, price, amount)

            if not self._product.valid(self._amount, self._price):
                raise AttributeError("Invalid amount/price for order")

            order_data = {"pair": self._product.prod_id,
                          "type": self._order_type,
                          "ordertype": "limit",
                          "price": str(self._price),
                          "volume": str(self._amount)}

            order_result = self._auth_client.client.query_private("AddOrder", order_data)

            if "result" in order_result and "txid" in order_result["result"]:
                self._created = True
                self._order_id = order_result["result"]["txid"]
                self._status = "created"
                self._filled_size = 0.0
                self._executed_value = 0.0
                self._settled = False
                self._message = "order creation successful"
            else:
                if "error" in order_result:
                    raise AttributeError(order_result["error"][0])
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
            order_update = self._auth_client.client.query_private("QueryOrders", {"txid": self._order_id})

            if "result" in order_update:
                self._status = order_update["result"]["status"]
                self._filled_size = float(order_update["result"]["vol_exec"])
                self._executed_value = self._filled_size * float(order_update["result"]["price"])
                if self._status in ["closed", "canceled", "expired"]:
                    self._settled = True
            else:
                self._settled = True
                raise AttributeError(order_update["error"])

        except Exception:
            self._status = "error"
            self._message = f"get order exception: {sys.exc_info()[1]}"

        return self._settled

    def cancel(self):
        try:
            super().cancel()
            self._auth_client.client.query_private("CancelOrder", {"txid": self.order_id})
        except Exception:
            self._message = "Cancellation failed"


class KrakenAccount(Account):
    def update(self, exchange_rate):
        account_info = self._auth_client.client.query_private("Balance")

        if "result" in account_info:
            for k, v in account_info["result"].items():
                if map_currency(k) == self._product.buying_currency:
                    self._bc_amount = float(v)
                elif map_currency(k) == self._product.trading_currency:
                    self._tc_amount = float(v)
                    self._value = self._tc_amount * exchange_rate


class KrakenAccumulator(Accumulator):
    def __init__(self, name):
        super().__init__(name)
        self._fee = MAKER_FEE


class KrakenApiCreator(ApiCreator):
    def create_trade_client(self, credentials):
        return KrakenTradeClient(credentials)

    def create_product(self, auth_client, trading_currency, buying_currency):
        return KrakenProduct(auth_client, trading_currency, buying_currency)

    def create_ticker(self, auth_client, product):
        return KrakenTicker(auth_client, product)

    def create_order(self, auth_client, product, order_type, price, amount):
        return KrakenOrder(auth_client, product, order_type, price, amount)

    def create_account(self, auth_client, product):
        return KrakenAccount(auth_client, product)

    def create_accumulator(self, name):
        return KrakenAccumulator(name)
