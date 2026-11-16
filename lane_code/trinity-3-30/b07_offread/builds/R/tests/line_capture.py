"""Capture executed source lines in a local fixture subprocess."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys

@contextmanager
def capture(output):
    root=str(Path(__file__).resolve().parents[1])+'/'
    lines={}
    def trace(frame,event,arg):
        name=frame.f_code.co_filename
        if not name.startswith(root) or not name.endswith('.py'):return None
        if event=='line':lines.setdefault(name,set()).add(frame.f_lineno)
        return trace
    sys.settrace(trace)
    try:yield
    finally:
        sys.settrace(None)
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({n:dict(sha256=hashlib.sha256(Path(n).read_bytes()).hexdigest(),lines=sorted(v)) for n,v in lines.items()},indent=1)+'\n')
