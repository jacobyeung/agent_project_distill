from pathlib import Path
import sys
n=Path(sys.argv[1])
for i in range(300):print("q",i,flush=True)
(n/"c.local").write_bytes(b"q"*4096)
