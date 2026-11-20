import sys,time
from pathlib import Path
p=Path(sys.argv[1])
for i in range(10000):
 with p.open('a') as f:f.write(str(i)+'\n')
 print('q'*1024,flush=True)
