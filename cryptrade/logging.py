from pushbullet import PushBullet

# Set debug levels
DEBUG_OFF = 0
DEBUG_BASIC = 1
DEBUG_DETAILED = 2


class LoggerSingleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class Logger(metaclass=LoggerSingleton):
    def __init__(self, level: int) -> None:
        self._level = level

    def log(self, level: int, debug_info: str) -> None:
        if level <= self._level:
            print(debug_info)

    def alert(self, level: int, alert_title: str, alert_msg: str) -> None:
        self.log(level, alert_title)
        self.log(level, alert_msg)


class FileLogger(Logger):
    def __init__(self, level: int, filename: str) -> None:
        super().__init__(level)
        self._fp = open(filename, "w+")

    def log(self, level: int, debug_info: str) -> None:
        if level <= self._level:
            self._fp.write(f"{debug_info}\n")

    def __del__(self) -> None:
        self._fp.close()


class PushBulletLogger(Logger):
    def __init__(self, level: int, api_key: str) -> None:
        super().__init__(level)
        self._pb = PushBullet(api_key)

    def alert(self, level: int, alert_title: str, alert_msg: str) -> None:
        super().alert(level, alert_title, alert_msg)
        try:
            self._pb.push_note("Cryptrade Alert: ", alert_title)
        except Exception:
            self.log(level, "PushBullet notification failed!")
