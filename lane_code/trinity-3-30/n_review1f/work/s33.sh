R=/scratch/jjyeung/orch_n30/n_review/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ; cd $R; cat runt2.done 2>&1
cd $R/tcpt && nice -n 10 env PYTHONDONTWRITEBYTECODE=1 $PY -I -s -B - <<'PY' > $R/exempt_probe.txt 2>&1
import sys; sys.path.insert(0,'.')
from student_pilot.extent_receipt import Extents
import student_pilot.extent_receipt as er
L=['T0_room_gaps','U_Faithful']
def row(qid,src,typ='object_abs_distance',r1=None):
    r=dict(qid=qid,routing=dict(question_type=typ),s1_source=dict(name=src) if src else None)
    if r1: r['r1_source']=r1
    return r
# no-receipt instance for the probe (pin None): required rows must refuse unless exempt
def run(e,r,s='routing'):
    try: e.check(r,s); return 'PASS'
    except Exception as x: return type(x).__name__+':'+str(x)
e=Extents(None,L)
cases=[('P pool row',row('q1','U_Faithful')),('a0_ slice row, listed source',row('a0_units_q1','U_Faithful')),
 ('r1_source row, listed source',row('q2','T0_room_gaps',r1={'x':1})),('unlisted source',row('q3','OTHER')),
 ('no s1_source (legacy) abs',row('q4',None)),('legacy camera type',row('q5',None,'camera_rotation'))]
for n,r in cases: print(n,'->',run(e,r))
print('vqa stream listed source ->',run(e,row('q6','U_Faithful'),'vqa'))
print('exempted',e.exempted)
print('empty list ->',run(Extents(None,[]),row('q1','U_Faithful')))
print('None list ->',run(Extents(None,None),row('q1','U_Faithful')))
for bad in ('U_Faithful',[''],[1],{'a':1}):
    try: Extents(None,bad); print('bad',bad,'accepted')
    except Exception as x: print('bad',repr(bad),type(x).__name__,str(x))
PY
cat $R/exempt_probe.txt
