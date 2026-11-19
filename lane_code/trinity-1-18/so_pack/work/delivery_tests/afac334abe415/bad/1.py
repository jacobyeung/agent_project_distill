import sys,time
from pathlib import Path
stop=Path(sys.argv[1]);ready=Path(sys.argv[2]);end=Path(sys.argv[3])
ready.write_text('ready\n');deadline=time.time()+2
while time.time()<deadline and not stop.exists():time.sleep(0.01)
if stop.exists():end.write_text('slot\n')
raise SystemExit(0 if end.exists() else 7)
