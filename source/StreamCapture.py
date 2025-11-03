import io
import sys
import threading
import os
import time

class ThreadSafeBuffer(io.StringIO):
    _lock = threading.Lock()

    def __init__(self, stdout):
        super().__init__()
        self._stdout = stdout

    def write(self, s):
        with self._lock:
            
            super().write(s)
            self._stdout.write(s)

    def getvalue(self):
        with self._lock:
            return super().getvalue()

    def clear(self):
        with self._lock:
            self.seek(0)
            self.truncate(0)

log_buffer = ThreadSafeBuffer(sys.stdout)

sys.stdout = log_buffer
