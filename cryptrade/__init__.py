import asyncio


class Observerable:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    async def notify(self):
        await asyncio.wait([observer.notify(self) for observer in self._observers])


class Observer:
    def __init__(self, observable):
        observable.attach(self)

    async def notify(self, observable):
        print(observable)


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
