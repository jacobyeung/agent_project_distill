import sys,tempfile,json
T=sys.argv[1]; sys.path[:0]=[T,'/scratch/jjyeung/orch_n30/review_c5/work/tests_r5']
from trace_format.contracts import contract_epoch, response_status
import fixtures_contracts as F
rows=[];dis=0
for on in (True,False):
  for kind in ('landscape','nadir_positive','vertical','small','rolled'):
    for small in (False,True):
      for pv in ('3.14',):
        with contract_epoch(on):
          try:
            s=F.session(F.fixture('landscape' if kind=='small' else kind)[1](), tempfile.mkdtemp(dir='/scratch/jjyeung/orch_n30/review_c5/work/tmp'), small=small or kind=='small', names=('chair','table','lamp'))
          except Exception as e: rows.append((on,kind,small,'session ERR '+str(e)[:80])); continue
          for name in ('chair','table','lamp','chair'):
            try: body=s.execute(f'<ground obj="{name}" mode="box">')
            except Exception as e: rows.append((on,kind,small,name,'EXC '+type(e).__name__+' '+str(e)[:60])); continue
            a=s.box_registry.states.get(name)=='ok'; b=response_status(body)=='ok'
            dis+=a!=b
            rows.append((on,kind,small,name,a,b,body.splitlines()[0][:50]))
for r in rows: print(r)
print('disagreements',dis)
