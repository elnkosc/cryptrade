import asyncio
from datetime import datetime
from math import trunc

from cryptrade.observers import Observable


def trunc_dec(number, digits):
    stepper = 10 ** digits
    return trunc(stepper * number) / stepper


class TradeClient:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        return self._client


class Product:
    def __init__(self, auth_client, trading_currency, buying_currency):
        self._auth_client = auth_client
        self._trading_currency = trading_currency
        self._buying_currency = buying_currency
        self._prod_id = trading_currency + buying_currency
        self._min_order_value = 0.0
        self._min_order_amount = 0.0
        self._min_order_price = 0.0

        if self._buying_currency == self._trading_currency:
            raise AttributeError("Trading and buying currency cannot be the same")

    @property
    def buying_currency(self):
        return self._buying_currency

    @property
    def trading_currency(self):
        return self._trading_currency

    @property
    def prod_id(self):
        return self._prod_id

    @property
    def min_order_value(self):
        return self._min_order_value

    @property
    def min_order_amount(self):
        return self._min_order_amount

    @property
    def min_order_price(self):
        return self._min_order_price

    def valid(self, amount, price):
        return amount >= self._min_order_amount and \
               price >= self._min_order_price and \
               amount * price >= self._min_order_value

    def format_price(self, price):
        if self._min_order_price > 0:
            return trunc_dec(price, len(str(self._min_order_price)) - 2)
        else:
            return price

    def format_amount(self, amount):
        if self._min_order_amount > 0:
            return trunc_dec(amount, len(str(self._min_order_amount)) - 2)
        else:
            return amount

    def __str__(self):
        return f"{self._trading_currency}-{self._buying_currency}"


class Ticker(Observable):
    def __init__(self, auth_client, product):
        super().__init__()
        self._auth_client = auth_client
        self._product = product
        self._ask = 0.0
        self._bid = 0.0
        self._price = 0.0
        self._timestamp = None
        self._name = ""

    def update(self):
        self._timestamp = datetime.now()

    def generate(self):
        while True:
            self.update()
            yield self

    async def produce(self, interval):
        while True:
            self.update()
            await self.notify()
            await asyncio.sleep(interval)

    @property
    def spread(self):
        return self._ask - self._bid

    @property
    def bid(self):
        return self._bid

    @property
    def ask(self):
        return self._ask

    @property
    def price(self):
        return self._price

    @property
    def timestamp(self):
        return self._timestamp

    def __str__(self):
        return (f"Ticker: {self._name}, {self._product}\n"
                f"Time  : {self._timestamp}\n"
                f"Price : {self._price:8.4f}\n"
                f"Bid   : {self._bid:8.4f}\n"
                f"Ask   : {self._ask:8.4f}\n"
                f"Spread: {self.spread:8.4f}\n")


class Order(Observable):
    def __init__(self, auth_client, product, order_type, price, amount):
        super().__init__()
        self._auth_client = auth_client
        self._product = product
        self._order_type = order_type
        self._price = self._product.format_price(price)
        self._amount = self._product.format_amount(amount)
        self._created = False
        self._order_id = None
        self._status = "open"
        self._filled_size = 0.0
        self._executed_value = 0.0
        self._settled = False
        self._message = ""
        self._timestamp = None

    def status(self):
        return self._settled

    @property
    def order_id(self):
        return self._order_id

    @property
    def order_type(self):
        return self._order_type

    @property
    def filled_size(self):
        return self._filled_size

    @property
    def executed_value(self):
        return self._executed_value

    @property
    def price(self):
        return self._price

    @property
    def error(self):
        return self._status == "error"

    @property
    def created(self):
        return self._created

    @property
    def message(self):
        return self._message

    @property
    def timestamp(self):
        return self._timestamp

    async def produce(self, interval):
        while True:
            if self.status():
                await self.notify()
            await asyncio.sleep(interval)

    def cancel(self):
        self._status = "canceled"
        self._message = "order canceled by user"
        self._settled = True

    def __str__(self):
        return (f"Order:\n"
                f"Order ID      : {self._order_id}\n"
                f"Product ID    : {self._product.prod_id}\n"
                f"Type          : {self._order_type}\n"
                f"Price         : {self._price}\n"
                f"Amount        : {self._amount:2.4f}\n"
                f"Status        : {self._status}\n"
                f"Filled Size   : {self._filled_size:2.4f}\n"
                f"Executed Value: {self._executed_value:4.4f}\n"
                f"Settled       : {self._settled}\n"
                f"Message       : {self._message}\n")


class Account(Observable):
    def __init__(self, auth_client):
        super().__init__()
        self._auth_client = auth_client
        self._balance = {}
        self._timestamp = None
        self._name = ""

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def balance(self):
        return self._balance

    def balance_string(self):
        s = ""
        for currency, balance in self._balance.items():
            s += f"{currency} : {balance:8.4f}\n"
        return s

    def update(self):
        self._timestamp = datetime.now()

    def generate(self):
        while True:
            self.update()
            yield self

    async def produce(self, interval):
        while True:
            self.update()
            await self.notify()
            await asyncio.sleep(interval)

    def currency_balance(self, currency):
        if currency in self._balance.keys():
            return self._balance[currency]
        else:
            return 0

    def __str__(self):
        return (f"Account: {self._name}\n"
                f"Time   : {self._timestamp}\n"
                f"{self.balance_string()}")


class ApiCreator:
    _maker_fee = 0
    _taker_fee = 0

    @staticmethod
    def create_trade_client(credentials):
        return TradeClient()

    @staticmethod
    def create_product(auth_client, trading_currency, buying_currency):
        return Product(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client, product):
        return Ticker(auth_client, product)

    @staticmethod
    def create_order(auth_client, product, order_type, price, amount):
        return Order(auth_client, product, order_type, product, amount)

    @staticmethod
    def create_account(auth_client):
        return Account(auth_client)

    @classmethod
    def maker_fee(cls):
        return cls._maker_fee

    @classmethod
    def taker_fee(cls):
        return cls._taker_fee
