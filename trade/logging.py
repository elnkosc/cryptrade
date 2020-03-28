from pushbullet import PushBullet

# Set debug levels
OFF = 0
BASIC = 1
DETAILED = 2


class Logger:
    def __init__(self, level):
        self._level = level

    def log(self, level, debug_info):
        if level <= self._level:
            print(debug_info)

    def alert(self, level, alert_title, alert_msg):
        self.log(level, alert_title)
        self.log(level, alert_msg)


class FileLogger(Logger):
    def __init__(self, level, fname):
        super().__init__(level)
        self._fp = open(fname, "w+")

    def log(self, level, debug_info):
        if level <= self._level:
            self._fp.write(f"{debug_info}\n")

    def __del__(self):
        self._fp.close()


class PushBulletLogger(Logger):
    def __init__(self, level, api_key):
        super().__init__(level)
        self._pb = PushBullet(api_key)

    def alert(self, level, alert_title, alert_msg):
        super().alert(level, alert_title, alert_msg)
        try:
            self._pb.push_note("cryptrade Alert", alert_title)
        except:
            self.log(level, "PushBullet notification failed!")
