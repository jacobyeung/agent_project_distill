import json,sys,time
from pathlib import Path
p=Path(sys.argv[1])
def event(kind):
    with p.open('a') as f:
        f.write(json.dumps(dict(who=sys.argv[2],kind=kind,time=time.monotonic()))+'\n')
event('start')
time.sleep(0.6)
event('end')
