from pathlib import Path
import signal,sys,time
D=Path(__file__).resolve().parent;L=D.parents[1];root=D/'rehearsal4'
sys.path.insert(0,str(D))
from live import Copier,put
from live_tests import WRITER
home=root/'sessions';home.mkdir(exist_ok=True);put(home/'sess.json',{})
writer=root/'writer.py';writer.write_text(WRITER)
c=Copier(L/'out/kit_n_go',root,'rehearsal',target=root/'target',train=root/'train',home=home,writer=writer)
c.names['objects']['m2']=c.names['objects']['m100']
stop=[False]
signal.signal(signal.SIGTERM,lambda *_:stop.__setitem__(0,True))
while not stop[0]:
    c.pass_once();time.sleep(1)
c.pass_once(final=True)
