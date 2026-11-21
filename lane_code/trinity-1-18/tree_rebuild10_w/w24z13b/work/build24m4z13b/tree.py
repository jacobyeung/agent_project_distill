import os,sys,time,signal,subprocess,json
from pathlib import Path
c=Path(os.environ['T_CASE']);level=int(sys.argv[1]);child=None
code={'TERM':37,'USR1':38}
def stop(s,_):
    name=signal.Signals(s).name.removeprefix('SIG')
    (c/('signal.'+['parent','child','grandchild'][level])).write_text(name+'\n')
    if child:
        child.send_signal(s);rc=child.wait(timeout=5)
        assert rc==code[name],rc
    print('C'+str(code[name]),flush=True)
    raise SystemExit(code[name])
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGUSR1,stop)
(c/('pid'+str(level))).write_text(str(os.getpid()))
if level<2: child=subprocess.Popen([sys.executable,'-I','-s','-B',__file__,str(level+1)])
if level==2:
    (c/'tree.ready').write_text(json.dumps({str(i):int((c/('pid'+str(i))).read_text()) for i in range(3)}))
if not os.environ['T_SIGNAL']:
    if os.environ['T_TICKS']=='1':
        while not (c/'release').exists():time.sleep(.02)
    if child: assert child.wait(timeout=5)==23
    print('C23',flush=True);sys.exit(23)
while True:time.sleep(.02)
