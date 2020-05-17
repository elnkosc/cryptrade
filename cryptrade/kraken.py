import krakenex

from cryptrade.exceptions import AuthenticationError, ProductError
from cryptrade.exchange_api import TradeClient, Currency, Product, Ticker, Order, Account, ApiCreator

import sys
from datetime import datetime


class KrakenTradeClient(TradeClient):
    def __init__(self, credentials: dict) -> None:
        super().__init__()

        if "kraken" in credentials and \
                "api_key" in credentials["kraken"] and \
                "api_secret" in credentials["kraken"]:
            api_key = credentials["kraken"]["api_key"]
            api_secret = credentials["kraken"]["api_secret"]
            try:
                self._client = krakenex.API(api_key, api_secret)
            except Exception:
                raise AuthenticationError("invalid Kraken API key and/or secret")
        else:
            try:
                self._client = krakenex.API()
            except Exception:
                raise AuthenticationError("Could not create non-authenticated Client for Kraken")


class KrakenCurrency(Currency):
    _currency_map = {
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

    def __init__(self, currency_id: str) -> None:
        super().__init__(currency_id)


class KrakenProduct(Product):
    _product_map = {
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

    def __init__(self, auth_client: KrakenTradeClient, trading_currency: Currency, buying_currency: Currency) -> None:
        try:
            super().__init__(auth_client, trading_currency, buying_currency)

            product_data = {"pair": f"{self.prod_id}"}
            product = self._auth_client.client.query_public("AssetPairs", product_data)

            if "result" in product:
                for k, v in product["result"].items():
                    self._min_order_amount = 1 / 10 ** v["lot_decimals"]
                    self._min_order_price = 1 / 10 ** v["pair_decimals"]
                    self._min_order_value = self._min_order_amount * self._min_order_price
                    self._order_price_precision = 1 / 10 ** v["pair_decimals"]
                    self._order_amount_precision = 1 / 10 ** v["lot_decimals"]
            else:
                raise ProductError(product["error"][0])

        except ProductError:
            raise
        except Exception:
            raise ProductError(f"{trading_currency}/{buying_currency} not supported on Kraken")


class KrakenTicker(Ticker):
    def __init__(self, auth_client: KrakenTradeClient, product: KrakenProduct) -> None:
        super().__init__(auth_client, product)
        self._name = "Kraken"

    def update(self) -> None:
        try:
            product_ticker = self._auth_client.client.query_public("Ticker", {"pair": f"{self._product.prod_id}"})
            if "result" in product_ticker:
                for k, v in product_ticker["result"].items():
                    self._bid = float(v["b"][0])
                    self._ask = float(v["a"][0])
                    self._price = float(v["c"][0])
                self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore exceptions
            pass


class KrakenOrder(Order):
    def __init__(self, auth_client: KrakenTradeClient, product: KrakenProduct, order_type: str,
                 price: float, amount: float) -> None:
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

    def status(self) -> bool:
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

        if self._settled:
            self._timestamp = datetime.now().replace(microsecond=0)

        return self._settled

    def cancel(self) -> None:
        if not self._settled:
            try:
                super().cancel()
                self._auth_client.client.query_private("CancelOrder", {"txid": self.order_id})
            except Exception:
                self._message = "Cancellation failed"


class KrakenAccount(Account):
    def __init__(self, auth_client: KrakenTradeClient) -> None:
        super().__init__(auth_client)
        self._name = "Kraken"

    def update(self) -> None:
        try:
            account_info = self._auth_client.client.query_private("Balance")

            if "result" in account_info:
                self._balance.clear()
                for currency, balance in account_info["result"].items():
                    c = KrakenCurrency.map_from_exchange_currency(currency.upper())
                    if float(balance) > 0:
                        self._balance[c] = float(balance)
                self._timestamp = datetime.now().replace(microsecond=0)

        except Exception:
            # ignore
            pass


class KrakenApiCreator(ApiCreator):
    _maker_fee = 0.0016
    _taker_fee = 0.0026

    @staticmethod
    def create_trade_client(credentials: dict) -> KrakenTradeClient:
        return KrakenTradeClient(credentials)

    @staticmethod
    def create_currency(currency_id: str) -> KrakenCurrency:
        return KrakenCurrency(currency_id)

    @staticmethod
    def create_product(auth_client: KrakenTradeClient, trading_currency: KrakenCurrency,
                       buying_currency: KrakenCurrency) -> KrakenProduct:
        return KrakenProduct(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client: KrakenTradeClient, product: KrakenProduct) -> KrakenTicker:
        return KrakenTicker(auth_client, product)

    @staticmethod
    def create_order(auth_client: KrakenTradeClient, product: KrakenProduct, order_type: str,
                     price: float, amount: float) -> KrakenOrder:
        return KrakenOrder(auth_client, product, order_type, price, amount)

    @staticmethod
    def create_account(auth_client: KrakenTradeClient) -> KrakenAccount:
        return KrakenAccount(auth_client)
