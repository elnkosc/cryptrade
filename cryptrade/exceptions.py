class CryptradeError(Exception):
    def __init__(self, *args) -> None:
        pass


class AuthenticationError(CryptradeError):
    def __init__(self, message) -> None:
        self._message = message

    def __str__(self) -> str:
        return __name__ + ": AuthenticationError, " + self._message


class ProductError(CryptradeError):
    def __init__(self, message) -> None:
        self._message = message

    def __str__(self) -> str:
        return __name__ + ": Unsupported cryptrade-pair specified, " + self._message


class ParameterError(CryptradeError):
    def __init__(self, message: str) -> None:
        self._message = message

    def __str__(self) -> str:
        return __name__ + ": Invalid parameter(s), " + self._message
