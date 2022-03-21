import datetime

# A simple way to log stuff when in fullscreen mode
LOG = []


class PeriodicTimer:
    def __init__(self, delay: datetime.timedelta):
        self.delay = delay
        self.last_time = datetime.datetime(2000, 1, 1, 0, 0, 0)

    def should_do_now(self):
        now = datetime.datetime.now()

        if now > self.last_time + self.delay:
            self.last_time = now
            return True
        else:
            return False
