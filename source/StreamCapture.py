import io
import sys
import threading

class ThreadSafeBuffer(io.StringIO):
    _lock = threading.Lock()

    def write(self, s):
        with self._lock:
            
            super().write(s)

    def getvalue(self):
        with self._lock:
            return super().getvalue()

    def clear(self):
        with self._lock:
            self.seek(0)
            self.truncate(0)

log_buffer = ThreadSafeBuffer()

sys.stdout = log_buffer
