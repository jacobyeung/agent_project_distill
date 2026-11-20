from pathlib import Path
import sys,time,signal
p=Path(sys.argv[1]);p.mkdir(exist_ok=True)
def stop(*_):
 (p/'complete.json').write_text('{"step":9}\n')
 raise SystemExit(0)
signal.signal(signal.SIGUSR1,stop)
(p/'ready').write_text('1')
for i in range(100):
 with (p/'steps').open('a') as f:f.write(str(i)+'\n')
 print('q',i,flush=True)
 time.sleep(.1)
