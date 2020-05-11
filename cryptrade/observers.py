import asyncio


class Observable:
    def __init__(self) -> None:
        self._observers = []

    def attach(self, observer: "Observer") -> None:
        self._observers.append(observer)

    def detach(self, observer: "Observer") -> None:
        self._observers.remove(observer)

    async def notify(self) -> None:
        if len(self._observers) > 0:
            await asyncio.wait([observer.notify(self) for observer in self._observers])


class Observer:
    def __init__(self, observable: Observable) -> None:
        self._observable = observable
        self._observable.attach(self)

    async def notify(self, observable: Observable) -> None:
        pass
