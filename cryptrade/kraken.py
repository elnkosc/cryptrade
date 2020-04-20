import krakenex

from cryptrade.exceptions import AuthenticationError, ProductError, ParameterError
from cryptrade.exchange_api import TradeClient, Product, Ticker, Order, Account, ApiCreator

import sys
import time

# kraken fees (percentage)
MAKER_FEE = 0.0016
TAKER_FEE = 0.0026

product_map = {
    "ADABTC": "ADAXBT",
    "ALGOBTC": "ALGOXBT",
    "BATBTC": "BATXBT",
    "BCHBTC": "BCHXBT",
    "DASHBTC": "DASHXBT",
    "EOSBTC": "EOSXBT",
    "GNOBTC": "GNOXBT",
    "ICXBTC": "ICXXBT",
    "LINKBTC": "LINKXBT",
    "LSKBTC": "LSKXBT",
    "NANOBTC": "NANOXBT",
    "OMGBTC": "OMGXBT",
    "PAXGBTC": "PAXGXBT",
    "QTUMBTC": "QTUMXBT",
    "SCBTC": "SCXBT",
    "TRXBTC": "TRXXBT",
    "USDTUSD": "USDTZUSD",
    "WAVESBTC": "WAVESXBT",
    "BTCCHF": "XBTCHF",
    "BTCDAI": "XBTDAI",
    "BTCUSDC": "XBTUSDC",
    "BTCUSDT": "XBTUSDT",
    "ETCETH": "XETCXETH",
    "ETCBTC": "XETCXXBT",
    "ETCEUR": "XETCZEUR",
    "ETCUSD": "XETCZUSD",
    "ETHBTC": "XETHXXBT",
    "ETHBTC.d": "XETHXXBT.d",
    "ETHCAD": "XETHZCAD",
    "ETHCAD.d": "XETHZCAD.d",
    "ETHEUR": "XETHZEUR",
    "ETHEUR.d": "XETHZEUR.d",
    "ETHGBP": "XETHZGBP",
    "ETHGBP.d": "XETHZGBP.d",
    "ETHJPY": "XETHZJPY",
    "ETHJPY.d": "XETHZJPY.d",
    "ETHUSD": "XETHZUSD",
    "ETHUSD.d": "XETHZUSD.d",
    "LTCBTC": "XLTCXXBT",
    "LTCEUR": "XLTCZEUR",
    "LTCUSD": "XLTCZUSD",
    "MLNETH": "XMLNXETH",
    "MLNBTC": "XMLNXXBT",
    "MLNEUR": "XMLNZEUR",
    "MLNUSD": "XMLNZUSD",
    "REPETH": "XREPXETH",
    "REPBTC": "XREPXXBT",
    "REPEUR": "XREPZEUR",
    "REPUSD": "XREPZUSD",
    "XTZBTC": "XTZXBT",
    "BTCCAD": "XXBTZCAD",
    "BTCCAD.d": "XXBTZCAD.d",
    "BTCEUR": "XXBTZEUR",
    "BTCEUR.d": "XXBTZEUR.d",
    "BTCGBP": "XXBTZGBP",
    "BTCGBP.d": "XXBTZGBP.d",
    "BTCJPY": "XXBTZJPY",
    "BTCJPY.d": "XXBTZJPY.d",
    "BTCUSD": "XXBTZUSD",
    "BTCUSD.d": "XXBTZUSD.d",
    "XDGBTC": "XXDGXXBT",
    "XLMBTC": "XXLMXXBT",
    "XLMEUR": "XXLMZEUR",
    "XLMUSD": "XXLMZUSD",
    "XMRBTC": "XXMRXXBT",
    "XMREUR": "XXMRZEUR",
    "XMRUSD": "XXMRZUSD",
    "XRPBTC": "XXRPXXBT",
    "XRPCAD": "XXRPZCAD",
    "XRPEUR": "XXRPZEUR",
    "XRPJPY": "XXRPZJPY",
    "XRPUSD": "XXRPZUSD",
    "ZECBTC": "XZECXXBT",
    "ZECEUR": "XZECZEUR",
    "ZECUSD": "XZECZUSD",
    "EURUSD": "ZEURZUSD",
    "GBPUSD": "ZGBPZUSD",
    "USDCAD": "ZUSDZCAD",
    "USDJPY": "ZUSDZJPY"}

currency_map = {
    "BTC": "XXBT",
    "ETH": "XETH",
    "ETC": "XETC",
    "LTC": "XLTC",
    "EUR": "ZEUR",
    "USD": "ZUSD",
    "XRP": "XXRP",
    "KRW": "ZKRW",
    "JPY": "ZJPY",
    "GBP": "ZGBP",
    "CAD": "ZCAD",
    "ZEC": "XZEC",
    "XVN": "XXVN",
    "XTZ": "XXTZ",
    "XMR": "XXMR",
    "XLM": "XXLM",
    "XDG": "XXDG",
    "REP": "XREP",
    "NMC": "XNMC",
    "MLN": "XMLN",
    "ICN": "XICN",
    "DAO": "XDAO"}


def map_product(trading_currency, buying_currency):
    prod_id = trading_currency + buying_currency
    if prod_id in product_map:
        return product_map[prod_id]
    else:
        return prod_id


def map_currency(currency):
    if currency in currency_map:
        return currency_map[currency]
    else:
        return currency


def reverse_map_currency(currency):
    if currency in currency_map.values():
        return next(key for key, value in currency_map.items() if value == currency)
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
            raise ParameterError("missing or invalid credentials for Kraken")

        try:
            self._client = krakenex.API(api_key, api_secret)
        except Exception:
            raise AuthenticationError("invalid Kraken API key and/or secret")


class KrakenProduct(Product):
    def __init__(self, auth_client, trading_currency, buying_currency):
        try:
            super().__init__(auth_client, trading_currency, buying_currency)
            self._prod_id = map_product(self._trading_currency, self._buying_currency)

            product_data = {"pair": f"{self._prod_id}"}
            product = self._auth_client.client.query_public("AssetPairs", product_data)

            if "result" in product:
                for k, v in product["result"].items():
                    self._min_amount = 1 / 10 ** v["lot_decimals"]
                    self._min_price = 1 / 10 ** v["pair_decimals"]
                    self._min_order_value = 0
            else:
                raise ProductError(product["error"][0])

        except ProductError:
            raise
        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Kraken")


class KrakenTicker(Ticker):
    def __init__(self, auth_client, product):
        super().__init__(auth_client, product)
        self._name = "Kraken"

    def update(self):
        try:
            product_ticker = self._auth_client.client.query_public("Ticker", {"pair": f"{self._product.prod_id}"})
            if "result" in product_ticker:
                for k, v in product_ticker["result"].items():
                    self._bid = float(v["b"][0])
                    self._ask = float(v["a"][0])
                    self._price = float(v["c"][0])
                    self._timestamp = time.time()

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
                self._order_id = order_result["result"]["txid"][0]
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
            order_data = {"txid": self._order_id}
            order_update = self._auth_client.client.query_private("QueryOrders", order_data)

            if "result" in order_update:
                self._status = order_update["result"][self._order_id]["status"]
                self._filled_size = float(order_update["result"][self._order_id]["vol_exec"])
                self._executed_value = self._filled_size * float(order_update["result"][self._order_id]["price"])
                if self._status in ["closed", "canceled", "expired"]:
                    self._settled = True
            else:
                self._settled = True
                raise AttributeError(order_update["error"][0])

        except Exception:
            self._status = "error"
            self._message = f"get order exception: {sys.exc_info()[1]}"

        return self._settled

    def cancel(self):
        if not self._settled:
            try:
                super().cancel()
                self._auth_client.client.query_private("CancelOrder", {"txid": self.order_id})
            except Exception:
                self._message = "Cancellation failed"


class KrakenAccount(Account):
    def __init__(self, auth_client):
        super().__init__(auth_client)
        self._name = "Kraken"

    def update(self):
        try:
            account_info = self._auth_client.client.query_private("Balance")

            if "result" in account_info:
                self._balance.clear()
                for currency, balance in account_info["result"].items():
                    c = reverse_map_currency(currency.upper())
                    if float(balance) > 0:
                        self._balance[c] = float(balance)
                self._timestamp = time.time()

        except Exception:
            # ignore
            pass


class KrakenApiCreator(ApiCreator):
    def create_trade_client(self, credentials):
        return KrakenTradeClient(credentials)

    def create_product(self, auth_client, trading_currency, buying_currency):
        return KrakenProduct(auth_client, trading_currency, buying_currency)

    def create_ticker(self, auth_client, product):
        return KrakenTicker(auth_client, product)

    def create_order(self, auth_client, product, order_type, price, amount):
        return KrakenOrder(auth_client, product, order_type, price, amount)

    def create_account(self, auth_client):
        return KrakenAccount(auth_client)

    def maker_fee(self):
        return MAKER_FEE

    def taker_fee(self):
        return TAKER_FEE
