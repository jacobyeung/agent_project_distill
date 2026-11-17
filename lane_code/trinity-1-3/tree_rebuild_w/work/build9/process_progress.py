"""Report CPU progress only for this lane's active native test runner."""
import json,os
from pathlib import Path
L=str(Path(__file__).resolve().parents[2])
for path in Path('/proc').iterdir():
 if not path.name.isdigit():continue
 try:
  if path.stat().st_uid!=os.getuid():continue
  args=(path/'cmdline').read_bytes().split(b'\0')
  if not any(L.encode() in arg and arg.endswith(b'/work/build9/test_runner.py') for arg in args):continue
  fields=(path/'stat').read_text().split(') ',1)[1].split()
  print(json.dumps(dict(pid=int(path.name),state=fields[0],cpu_seconds=(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'))))
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
