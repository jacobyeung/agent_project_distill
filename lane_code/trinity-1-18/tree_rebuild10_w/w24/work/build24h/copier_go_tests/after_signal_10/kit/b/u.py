from pathlib import Path
import json,signal,sys,time
r=Path(sys.argv[1]);stop=[False]
signal.signal(signal.SIGUSR1,lambda *_:stop.__setitem__(0,True))
(r/'ready').write_text('ready')
end=time.monotonic()+4
while not stop[0] and time.monotonic()<end:time.sleep(.02)
if stop[0]:
 time.sleep(.25)
 d=r/'r/m100';d.mkdir(parents=True)
 (d/'w').write_bytes(b'final export')
 (d/'artifact.json').write_text(json.dumps({'step':100}))
 (r/'t.log').write_text('export after USR1')
raise SystemExit(7)
