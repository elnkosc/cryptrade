import math
import asyncio
import time


def trunc_dec(number, digits):
    stepper = 10 ** digits
    return math.trunc(stepper * number) / stepper


class CryptradeError(Exception):
    def __init__(self, *args):
        pass


class AuthenticationError(CryptradeError):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return __name__ + ": AuthenticationError, " + self._message


class ProductError(CryptradeError):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return __name__ + ": Unsupported cryptrade-pair specified, " + self._message


class ParameterError(CryptradeError):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return __name__ + ": Invalid parameter(s), " + self._message


class History:
    def __init__(self, name, item, interval, max_items):
        self._name = name
        self._item = item
        self._interval = interval
        self._max_items = max_items
        self._history_count = 0
        self._history = []

    async def start(self):
        async for item in self._item.start():
            self._history_count += 1
            if self._history_count > self._max_items:
                self._history.pop(0)

            self._history.append(item)
            print(self)
            await asyncio.sleep(self._interval)

    # just pretty print last value
    def __str__(self):
        if self._history_count == 0:
            return ""
        else:
            return f"{self._name}\n{self._history[-1]}"


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
        self._prod_id = ""
        self._min_order_value = 0.0
        self._min_amount = 0.0
        self._min_price = 0.0

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
    def min_amount(self):
        return self._min_amount

    @property
    def min_price(self):
        return self._min_price

    def valid(self, amount, price):
        return amount >= self._min_amount and price >= self._min_price and amount * price >= self._min_order_value

    def format_price(self, price):
        if self._min_price > 0:
            return trunc_dec(price, len(str(self._min_price)) - 2)
        else:
            return price

    def format_amount(self, amount):
        if self._min_amount > 0:
            return trunc_dec(amount, len(str(self._min_amount)) - 2)
        else:
            return amount

    def __str__(self):
        return f"{self._trading_currency}-{self._buying_currency}"


class Ticker:
    def __init__(self, auth_client, product):
        self._auth_client = auth_client
        self._product = product
        self._ask = 0.0
        self._bid = 0.0
        self._price = 0.0
        self._timestamp = None

    def update(self):
        self._timestamp = time.time()

    async def start(self):
        pass

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

    def __str__(self):
        time_format = "%Y-%m-%d %H:%M:%S"
        return (f"Ticker: {self._product}\n"
                f"Time  : {time.strftime(time_format, time.localtime(self._timestamp))}\n"
                f"Price : {self._price:8.4f}\n"
                f"Bid   : {self._bid:8.4f}\n"
                f"Ask   : {self._ask:8.4f}\n"
                f"Spread: {self.spread:8.4f}\n")


class Order:
    def __init__(self, auth_client, product, order_type, price, amount):
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

    def status(self):
        return self._settled

    @property
    def order_id(self):
        return self._order_id

    @property
    def filled_size(self):
        return self._filled_size

    @property
    def executed_value(self):
        return self._executed_value

    @property
    def error(self):
        return self._status == "error"

    @property
    def created(self):
        return self._created

    @property
    def message(self):
        return self._message

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


class Account:
    def __init__(self, auth_client, product):
        self._auth_client = auth_client
        self._product = product
        self._tc_amount = 0.0
        self._bc_amount = 0.0
        self._started = False

    def update(self):
        pass

    async def start(self):
        pass

    @property
    def trading_amount(self):
        return self._tc_amount

    @property
    def buying_amount(self):
        return self._bc_amount

    def __str__(self):
        return (f"Account: {self._product.trading_currency}-{self._product.buying_currency}\n"
                f"{self._product.buying_currency} : {self._bc_amount:8.4f}\n"
                f"{self._product.trading_currency} : {self._tc_amount:8.4f}\n")


class TransactionMonitor:
    def __init__(self, name, fee=None):
        self._name = name
        self._fee = fee
        self._total_number = 0
        self._total_amount = 0.0
        self._total_value = 0.0
        self._total_fee = 0.0

    def add(self, amount, value, fee=None):
        self._total_amount += amount
        self._total_value += value
        self._total_number += 1
        if fee is not None:
            self._total_fee += (amount * value * fee)
        elif self._fee is not None:
            self._total_fee += (amount * value * self._fee)

    @property
    def total_amount(self):
        return self._total_amount

    @property
    def total_value(self):
        return self._total_value

    @property
    def total_number(self):
        return self._total_number

    @property
    def total_fee(self):
        return self._total_fee

    def __str__(self):
        return (f"Total {self._name}\n"
                f"Transactions: {self._total_number:4d}\n"
                f"Amount      : {self._total_amount:4.4f}\n"
                f"Value       : {self._total_value:6.2f}\n"
                f"Total Fee   : {self._total_fee:6.2f}\n")


class ApiCreator:
    def create_trade_client(self, credentials):
        pass

    def create_product(self, auth_client, trading_currency, buying_currency):
        pass

    def create_ticker(self, auth_client, product):
        pass

    def create_order(self, auth_client, product, order_type, price, amount):
        pass

    def create_account(self, auth_client, product):
        pass

    def create_transaction_monitor(self, name):
        pass
