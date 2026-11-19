import sys,time
from pathlib import Path
s=Path(sys.argv[1]);end=time.time()+3
while not s.exists() and time.time()<end:time.sleep(.01)
if s.exists():Path(sys.argv[2]).write_text('slot')
raise SystemExit(0 if s.exists() else 9)
