import asyncio
from datetime import datetime
from math import trunc
from cryptrade.observers import Observable


class TradeClient:
    def __init__(self) -> None:
        self._client = None

    @property
    def client(self):
        return self._client


class Currency:
    _currency_map = {}

    def __init__(self, currency_id: str) -> None:
        self._currency_id = currency_id

    @classmethod
    def map_from_exchange_currency(cls, currency: str) -> str:
        results = [key for key, value in cls._currency_map.items() if value == currency]
        return results[0] if results else currency

    @property
    def currency_id(self) -> str:
        return self._currency_id

    @property
    def exchange_currency_id(self) -> str:
        return type(self)._currency_map.get(self._currency_id, self._currency_id)

    def __str__(self) -> str:
        return self._currency_id

    def __eq__(self, other: "Currency") -> bool:
        return self.currency_id == other.currency_id


class Product:
    _product_map = {}

    def __init__(self, auth_client: TradeClient, trading_currency: Currency, buying_currency: Currency) -> None:
        self._auth_client = auth_client
        self._trading_currency = trading_currency
        self._buying_currency = buying_currency
        self._min_order_value = 0.0
        self._min_order_amount = 0.0
        self._min_order_price = 0.0
        self._order_price_precision = None
        self._order_amount_precision = None

        if self._buying_currency == self._trading_currency:
            raise AttributeError("Trading and buying currency cannot be the same")

    @staticmethod
    def trunc_dec(number: float, digits: int) -> float:
        stepper = 10 ** digits
        return trunc(stepper * number) / stepper

    @staticmethod
    def apply_precision(number: float, precision: float) -> float:
        return Product.trunc_dec(number // precision * precision, len(str(precision)) - 2)

    @classmethod
    def map_from_exchange_product(cls, prod_id: str) -> str:
        return next(key for key, value in cls._product_map.items() if value == prod_id)

    @property
    def prod_id(self) -> str:
        prod = str(self._trading_currency) + str(self._buying_currency)
        return type(self)._product_map.get(prod, prod)

    @property
    def buying_currency(self) -> Currency:
        return self._buying_currency

    @property
    def trading_currency(self) -> Currency:
        return self._trading_currency

    @property
    def min_order_value(self) -> float:
        return self._min_order_value

    @property
    def min_order_amount(self) -> float:
        return self._min_order_amount

    @property
    def min_order_price(self) -> float:
        return self._min_order_price

    def valid(self, amount: float, price: float) -> bool:
        return amount >= self._min_order_amount and \
               price >= self._min_order_price and \
               amount * price >= self._min_order_value

    def format_price(self, price: float) -> float:
        if self._order_price_precision is not None and self._order_price_precision > 0:
            return type(self).apply_precision(price, self._order_price_precision)
        else:
            return price

    def format_amount(self, amount: float) -> float:
        if self._order_amount_precision is not None and self._order_amount_precision > 0:
            return type(self).apply_precision(amount, self._order_amount_precision)
        else:
            return amount

    def __str__(self) -> str:
        return f"{self._trading_currency}-{self._buying_currency}"


class Ticker(Observable):
    def __init__(self, auth_client: TradeClient, product: Product) -> None:
        super().__init__()
        self._auth_client = auth_client
        self._product = product
        self._ask = 0.0
        self._bid = 0.0
        self._price = 0.0
        self._timestamp = None
        self._name = ""

    def update(self) -> None:
        self._timestamp = datetime.now()

    def generate(self) -> None:
        while True:
            self.update()
            yield self

    async def produce(self, interval: int) -> None:
        while True:
            self.update()
            await self.notify()
            await asyncio.sleep(interval)

    @property
    def bid(self) -> float:
        return self._bid

    @property
    def ask(self) -> float:
        return self._ask

    @property
    def price(self) -> float:
        return self._price

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def __str__(self) -> str:
        return (f"Ticker: {self._name}, {self._product}\n"
                f"Time  : {self._timestamp}\n"
                f"Price : {self._price:8.4f}\n"
                f"Bid   : {self._bid:8.4f}\n"
                f"Ask   : {self._ask:8.4f}\n"
                f"Spread: {self._ask-self._bid:8.4f}\n")


class Order(Observable):
    def __init__(self, auth_client: TradeClient, product: Product, order_type: str, price: float,
                 amount: float) -> None:
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

    def status(self) -> bool:
        return self._settled

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def order_type(self) -> str:
        return self._order_type

    @property
    def filled_size(self) -> float:
        return self._filled_size

    @property
    def executed_value(self) -> float:
        return self._executed_value

    @property
    def error(self) -> bool:
        return self._status == "error"

    @property
    def created(self) -> bool:
        return self._created

    @property
    def message(self) -> str:
        return self._message

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    async def produce(self, interval: int) -> None:
        while True:
            if self.status():
                await self.notify()
            await asyncio.sleep(interval)

    def cancel(self) -> None:
        self._status = "canceled"
        self._message = "order canceled by user"
        self._settled = True

    def __str__(self) -> str:
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
    def __init__(self, auth_client: TradeClient) -> None:
        super().__init__()
        self._auth_client = auth_client
        self._balance = {}
        self._timestamp = None
        self._name = ""

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def balance(self) -> dict:
        return self._balance

    def balance_string(self) -> str:
        s = ""
        for currency, balance in self._balance.items():
            s += f"{currency}    : {balance:8.4f}\n"
        return s

    def update(self) -> None:
        self._timestamp = datetime.now()

    def generate(self) -> None:
        while True:
            self.update()
            yield self

    async def produce(self, interval: int) -> None:
        while True:
            self.update()
            await self.notify()
            await asyncio.sleep(interval)

    def currency_balance(self, currency: str) -> float:
        if currency in self._balance.keys():
            return self._balance[currency]
        else:
            return 0

    def __str__(self) -> str:
        return (f"Account: {self._name}\n"
                f"Time   : {self._timestamp}\n"
                f"{self.balance_string()}")


class ApiCreator:
    _maker_fee = 0
    _taker_fee = 0

    @staticmethod
    def create_trade_client(credentials: dict) -> TradeClient:
        return TradeClient()

    @staticmethod
    def create_currency(currency_id: str) -> Currency:
        return Currency(currency_id)

    @staticmethod
    def create_product(auth_client: TradeClient, trading_currency: Currency, buying_currency: Currency) -> Product:
        return Product(auth_client, trading_currency, buying_currency)

    @staticmethod
    def create_ticker(auth_client: TradeClient, product: Product) -> Ticker:
        return Ticker(auth_client, product)

    @staticmethod
    def create_order(auth_client: TradeClient, product: Product, order_type: str, price: float, amount: float) -> Order:
        return Order(auth_client, product, order_type, price, amount)

    @staticmethod
    def create_account(auth_client: TradeClient) -> Account:
        return Account(auth_client)

    @classmethod
    def maker_fee(cls) -> float:
        return cls._maker_fee

    @classmethod
    def taker_fee(cls) -> float:
        return cls._taker_fee
