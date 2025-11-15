import time

class RateLimiter:
    def __init__(self, rate_limit, time_period):
        self.rate_limit = rate_limit
        self.time_period = time_period
        self.calls = []

    def allow(self):
        now = time.time()
        self.calls = [t for t in self.calls if now - t < self.time_period]
        if len(self.calls) < self.rate_limit:
            self.calls.append(now)
            return True
        return False
