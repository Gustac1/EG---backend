import time, threading
from typing import Callable, Dict

class Scheduler:
    def __init__(self):
        self.jobs: Dict[str, threading.Thread] = {}
    def start(self, key: str, seconds: float, on_start: Callable, on_end: Callable):
        if key in self.jobs: return False
        def _run():
            on_start(); time.sleep(seconds); on_end(); self.jobs.pop(key, None)
        t = threading.Thread(target=_run, daemon=True); self.jobs[key]=t; t.start(); return True
    def running(self, key:str)->bool: return key in self.jobs
