import asyncio
import datetime
import time
from math import trunc


class Observable:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    async def notify(self):
        if len(self._observers) > 0:
            await asyncio.wait([observer.notify(self) for observer in self._observers])


class Observer:
    def __init__(self, observable):
        self._observable = observable
        self._observable.attach(self)

    async def notify(self, observable):
        pass


class TickerMonitor(Observer):
    def __init__(self, ticker, ticker_name, time_window):
        super().__init__(ticker)
        self._name = ticker_name
        self._time_window = time_window
        self._high = 0
        self._low = 0
        self._average = 0
        self._ticker_data = []

    async def notify(self, ticker):
        # remove entries older than time_window
        while len(self._ticker_data) > 0 and ticker.timestamp - self._ticker_data[0]["time"] > self._time_window:
            self._ticker_data.pop(0)

        if ticker.timestamp is not None:
            self._ticker_data.append({"time": ticker.timestamp,
                                      "ask": ticker.ask,
                                      "bid": ticker.bid,
                                      "price": ticker.price})
            prices = [data["price"] for data in self._ticker_data]
            self._high = max(prices)
            self._low = min(prices)
            self._average = sum(prices) / len(prices)

    @property
    def high(self):
        return self._high

    @property
    def low(self):
        return self._low

    @property
    def average(self):
        return self._average

    def __str__(self):
        if len(self._ticker_data) == 0:
            return ""
        else:
            time_format = "%Y-%m-%d %H:%M:%S"
            oldest_time = self._ticker_data[0]["time"]
            newest_time = self._ticker_data[len(self._ticker_data)-1]["time"]
            time_period = trunc(newest_time - oldest_time)
            return (f"TICKER {self._name}\n"
                    f"Time   : {time.strftime(time_format, time.localtime(newest_time))}\n"
                    f"Period : {str(datetime.timedelta(seconds=time_period))}\n"
                    f"High   : {self._high:8.4f}\n"
                    f"Low    : {self._low:8.4f}\n"
                    f"Average: {self._average:8.4f}\n")


class AccountMonitor(Observer):
    def __init__(self, account, account_name):
        super().__init__(account)
        self._name = account_name
        self._account_data = []

    async def notify(self, account):
        if account.timestamp is not None:
            self._account_data.append({"time": account.timestamp, "balance": account.balance})

    def __str__(self):
        if len(self._account_data) == 0:
            return ""
        else:
            time_format = "%Y-%m-%d %H:%M:%S"
            oldest_time = self._account_data[0]["time"]
            newest_time = self._account_data[len(self._account_data) - 1]["time"]
            time_period = trunc(newest_time - oldest_time)
            oldest_balance = self._account_data[0]["balance"]
            newest_balance = self._account_data[len(self._account_data)-1]["balance"]

            balance_string = ""
            for currency, balance in newest_balance.items():
                if currency in oldest_balance:
                    old_currency_balance = oldest_balance[currency]
                else:
                    old_currency_balance = 0
                balance_string += f"* {currency} : {old_currency_balance:8.4f} -> {balance:8.4f}\n"

            return (f"ACCOUNT {self._name}\n"
                    f"Time     : {time.strftime(time_format, time.localtime(newest_time))}\n"
                    f"Period   : {str(datetime.timedelta(seconds=time_period))}\n"
                    f"Balances\n{balance_string}")


class OrderMonitor(Observer):
    def __init__(self, order, order_name):
        super().__init__(order)
        self._name = order_name
        self._order_data = []

    async def notify(self, order):
        if order.timestamp is not None:
            self._order_data.append({"time": order.timestamp,
                                     "type": order.order_type,
                                     "amount": order.amount,
                                     "price": order.price,
                                     "value": order.executed_value})

    def __str__(self):
        time_format = "%Y-%m-%d %H:%M:%S"
        s = f"ORDERS {self._name}\n"
        for order in self._order_data:
            order_time = time.strftime(time_format, time.localtime(order["time"]))
            order_type = order["type"]
            amount = order["amount"]
            price = order["price"]
            value = order["value"]
            s += f"Time     : {order_time}\n" \
                 f"Type     : {order_type}\n" \
                 f"Amount   : {amount:8.4f}\n" \
                 f"Price    : {price:8.4f}\n" \
                 f"Value    : {value:8.4f}\n"

        return s


class Transactions:
    def __init__(self, name, fee=None):
        self._name = name
        self._fee = fee
        self._number = 0
        self._amount = 0.0
        self._value = 0.0
        self._total_fee = 0.0

    def add(self, filled_size, executed_value):
        self._amount += filled_size
        self._value += executed_value
        self._number += 1
        if self._fee is not None:
            self._total_fee += (executed_value * self._fee)

    @property
    def amount(self):
        return self._amount

    @property
    def value(self):
        return self._value

    @property
    def number(self):
        return self._number

    @property
    def total_fee(self):
        return self._total_fee

    def __str__(self):
        return (f"TRANSACTIONS {self._name}\n"
                f"Number  : {self._number:4d}\n"
                f"Amount  : {self._amount:4.4f}\n"
                f"Value   : {self._value:6.2f}\n"
                f"Fee     : {self._total_fee:6.2f}\n")
