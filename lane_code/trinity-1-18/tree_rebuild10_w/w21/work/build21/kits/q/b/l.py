import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,screen
k=Path(sys.argv[1]);w=load(k/'k/g.json');h=load(k/'b/wh.json')
for line in sys.stdin:
 sys.stdout.write(screen(line,w,h));sys.stdout.flush()
