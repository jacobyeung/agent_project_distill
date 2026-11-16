# robosuite 1.4.0 hardcodes /tmp/robosuite.log, which another user owns on this shared node: redirect it.
import logging, os
_Orig = logging.FileHandler
class _FH(_Orig):
    def __init__(self, filename, *a, **k):
        if str(filename) == "/tmp/robosuite.log":
            filename = os.path.join(os.environ.get("VLA_LOG_DIR", "/scratch/jjyeung/vla_env/logs"), "robosuite.log")
        super().__init__(filename, *a, **k)
logging.FileHandler = _FH
