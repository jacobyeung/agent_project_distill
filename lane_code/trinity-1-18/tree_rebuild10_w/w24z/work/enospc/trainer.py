from pathlib import Path
import sys,time
p=Path(sys.argv[1])
for i in range(150):
 with (p/'steps.local').open('a') as f:f.write(str(i)+'\n')
 if i==8:(p/'checkpoint.local').write_bytes(b'q'*4096)
 time.sleep(.1)
