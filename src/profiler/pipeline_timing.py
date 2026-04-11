from __future__ import annotations

import time


class FrameTimer:
    def __init__(self):
        self.last_time = None

    def tick(self) -> float:
        now = time.time()

        if self.last_time is None:
            self.last_time = now
            return 0.0

        dt = now - self.last_time
        self.last_time = now

        return dt