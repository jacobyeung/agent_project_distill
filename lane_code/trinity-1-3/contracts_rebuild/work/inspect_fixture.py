import sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(L/'work/trees/patched'),str(L/'work/tests')]
from fixtures_contracts import *
geo=fixture()[1]()
s=session(geo,L/'work/tmp/inspect')
for call in CALLS:
    print(call,response(s,call))
from student_pilot.live_trace313 import AuditSession
a=AuditSession(s.queries,'3.14')
for call in CALLS:print('replay',call,a.execute(call))
