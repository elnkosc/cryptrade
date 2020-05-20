from cryptrade.observers import Observer
from cryptrade.exchange_api import Ticker, Account, Order


class TickerMonitor(Observer):
    def __init__(self, ticker: Ticker, ticker_name: str, time_window: int) -> None:
        super().__init__(ticker)
        self._name = ticker_name
        self._time_window = time_window
        self._high = 0
        self._low = 0
        self._average = 0
        self._ticker_data = []

    async def notify(self, ticker: Ticker) -> None:
        # remove entries older than time_window
        while len(self._ticker_data) > 0 and \
                (ticker.timestamp - self._ticker_data[0]["time"]).total_seconds() > self._time_window:
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
    def high(self) -> float:
        return self._high

    @property
    def low(self) -> float:
        return self._low

    @property
    def average(self) -> float:
        return self._average

    def __str__(self) -> str:
        if len(self._ticker_data) == 0:
            return ""
        else:
            oldest_time = self._ticker_data[0]["time"]
            newest_time = self._ticker_data[len(self._ticker_data) - 1]["time"]
            time_period = newest_time - oldest_time
            return (f"TICKER {self._name}\n"
                    f"Period : {time_period}\n"
                    f"High   : {self._high:8.4f}\n"
                    f"Low    : {self._low:8.4f}\n"
                    f"Average: {self._average:8.4f}\n")


class AccountMonitor(Observer):
    def __init__(self, account: Account, account_name: str) -> None:
        super().__init__(account)
        self._name = account_name
        self._account_data = []

    async def notify(self, account: Account) -> None:
        if account.timestamp is not None:
            self._account_data.append({"time": account.timestamp, "balance": account.balance})

    def __str__(self) -> str:
        if len(self._account_data) == 0:
            return ""
        else:
            oldest_time = self._account_data[0]["time"]
            newest_time = self._account_data[len(self._account_data) - 1]["time"]
            time_period = newest_time - oldest_time

            oldest_balance = self._account_data[0]["balance"]
            newest_balance = self._account_data[len(self._account_data) - 1]["balance"]

            balance_string = ""
            for currency, balance in newest_balance.items():
                if currency in oldest_balance:
                    old_currency_balance = oldest_balance[currency]
                else:
                    old_currency_balance = 0
                balance_string += f"* {currency} : {old_currency_balance:8.4f} -> {balance:8.4f}\n"

            return (f"ACCOUNT {self._name}\n"
                    f"Time     : {newest_time}\n"
                    f"Period   : {time_period}\n"
                    f"Balances\n{balance_string}")


class OrderMonitor(Observer):
    def __init__(self, order: Order, order_name: str) -> None:
        super().__init__(order)
        self._name = order_name
        self._order_data = []

    async def notify(self, order: Order) -> None:
        if order.timestamp is not None:
            self._order_data.append({"time": order.timestamp,
                                     "type": order.order_type,
                                     "amount": order.filled_size,
                                     "value": order.executed_value})

    def __str__(self) -> str:
        s = f"ORDERS {self._name}\n"
        for order in self._order_data:
            order_time = order["time"]
            order_type = order["type"]
            amount = order["amount"]
            value = order["value"]
            s += f"Time     : {order_time}\n" \
                 f"Type     : {order_type}\n" \
                 f"Amount   : {amount:8.4f}\n" \
                 f"Value    : {value:8.4f}\n"

        return s


class Transactions:
    def __init__(self, name: str, fee: float = None) -> None:
        self._name = name
        self._fee = fee
        self._number = 0
        self._amount = 0.0
        self._value = 0.0
        self._total_fee = 0.0

    def add(self, filled_size: float, executed_value: float) -> None:
        self._amount += filled_size
        self._value += executed_value
        self._number += 1
        if self._fee is not None:
            self._total_fee += (executed_value * self._fee)

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def value(self) -> float:
        return self._value

    @property
    def number(self) -> int:
        return self._number

    @property
    def total_fee(self) -> float:
        return self._total_fee

    def __str__(self) -> str:
        return (f"TRANSACTIONS {self._name}\n"
                f"Number  : {self._number:4d}\n"
                f"Amount  : {self._amount:6.4f}\n"
                f"Value   : {self._value:6.2f}\n"
                f"Fee     : {self._total_fee:6.2f}\n")