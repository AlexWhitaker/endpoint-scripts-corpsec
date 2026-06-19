import time
import threading


class RateLimiter:
    """
    Rate limiter that allows a certain number of requests per interval.
    """

    def __init__(self, limit: int, interval: int):
        self.limit = limit
        self.interval = interval

        self.requests = []
        self.lock = threading.Lock()

    def can_call(self) -> bool:
        """
        Returns True if a call can be made, False otherwise.
        """

        with self.lock:
            return self._can_call_no_lock()

    def record_hit(self, sleep_if_needed: bool = False):
        """
        Records a hit. If sleep_if_needed is True, the function will block until a call can be made.
        """

        while sleep_if_needed:
            with self.lock:
                if self._can_call_no_lock():
                    self.requests.append(int(time.time()))
                    return

                time_to_sleep = (
                    (self.requests[0] + self.interval) - time.time() if len(self.requests) > 0 else self.interval
                )
                if time_to_sleep <= 0:
                    time_to_sleep = self.interval

            time.sleep(time_to_sleep)

        with self.lock:
            if not self._can_call_no_lock():
                raise TooManyRequestsError()
            self.requests.append(int(time.time()))

    def _can_call_no_lock(self) -> bool:
        """
        Returns True if a call can be made, False otherwise.
        Note: This function should be called with the lock held.
        """
        if self._limit_reached_no_lock():
            if not self._purge_old_no_lock() or self._limit_reached_no_lock():
                return False

        return True

    def _purge_old_no_lock(self) -> bool:
        """
        Purges requests that are older than the interval.
        Note: These should be atomic operations, but still only call w/ a lock held.
        """
        original_len = len(self.requests)
        now = time.time()
        self.requests = [r for r in self.requests if r >= now - self.interval]
        return original_len != len(self.requests)

    def _limit_reached_no_lock(self) -> bool:
        """
        Returns True if the rate limit has been reached, False otherwise.
        """
        return len(self.requests) >= self.limit


class TooManyRequestsError(Exception):
    """Exception raised when the rate limit is reached."""

    status = 429
