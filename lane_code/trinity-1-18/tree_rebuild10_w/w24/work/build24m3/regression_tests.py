from pathlib import Path
import ast, copy, hashlib, importlib.util, json, os, sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m3';F=D/'regressions';F.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'out/kit_n_go/b'),str(L/'work/build24'),str(L/'work/tree_r1')]
import rv, rg, rd, joblib as J
from student_pilot.p3_provenance import digest
from student_pilot.r1_persisted import scope

def bad(k):return k in {'frame','frames','frame_index','frame_indices','frame_id','timestamp','timestamps'} or '_frame' in k
def keys(v):
    if isinstance(v,dict):
        for k,x in v.items():yield k;yield from keys(x)
    elif isinstance(v,list):
        for x in v:yield from keys(x)
def leaves(v,path=()):
    if isinstance(v,dict):
        for k,x in v.items():
            if not bad(k):yield from leaves(x,path+(k,))
    elif isinstance(v,list):
        for i,x in enumerate(v):yield from leaves(x,path+(i,))
    else:yield path,v
rows={}
for name in ('e0','e1','e2','e3'):
    original=J.load(L/'work/build24k/retained_evidence'/f'{name}.json')
    after=copy.deepcopy(original)
    for item in after['sample']:item['row']=rv.strip_frames(item['row'])
    assert len(after['sample'])==len(original['sample'])==40
    assert {k:v for k,v in after.items() if k!='sample'}=={k:v for k,v in original.items() if k!='sample'}
    for before,item in zip(original['sample'],after['sample']):
        assert not any(bad(k) for k in keys(item['row']))
        assert list(leaves(before['row']))==list(leaves(item['row']))
        assert {k:v for k,v in before.items() if k!='row'}=={k:v for k,v in item.items() if k!='row'}
    J.write(F/(name+'.json'),after)
    rows[name]=dict(samples=40,admitted_rows=original['admitted_rows'],removed_keys=sum(bad(k) for x in original['sample'] for k in keys(x['row'])))
probe={'qid':'keep','text':'frame 7 at timestamp 4','nested':[dict(frame=1,frames=[1],frame_id=1,frame_indices=[1],frame_index=1,timestamp=1,timestamps=[1],partner_frame=1,total_num_frames=2,foo_frame_bar=3,answer='keep')]}
assert rv.strip_frames(probe)=={'qid':'keep','text':'frame 7 at timestamp 4','nested':[dict(answer='keep')]}
J.write(D/'FRAME_TESTS.json',dict(status='PASS',counts_unchanged=True,identifiers_and_text_unchanged=True,streams=rows,arbitrary_depth=True))

# P's actual saved selection is stale against the sealed producer.
from student_pilot.s1_pool import implementation
receipt=J.load(L/'work/build22/upload/u/ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984')
material=L.parent/'ext/m400real/files'/receipt['materialization']['path'].lstrip('/')
recipe=J.load(material);selection=L.parent/'ext/m400real/files'/recipe['inputs']['selection']['path'].lstrip('/')
assert J.sha(material)==receipt['materialization']['sha256']
assert J.sha(selection)==recipe['inputs']['selection']['sha256']
assert J.load(selection)['implementation']!=implementation()
J.write(D/'P_RECIPE_AUDIT.json',dict(status='PASS',materialization=receipt['materialization'],selection=recipe['inputs']['selection'],saved_implementation_sha256=digest(J.load(selection)['implementation']),current_implementation_sha256=digest(implementation()),refresh_required=True,production_equality='NOT_RUN'))

# Compare reads must use read-only SQLite URIs; output writes stay in the job.
source=Path(rg.__file__).read_text()
calls=[x for x in ast.walk(ast.parse(source)) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='sqlite3' and x.func.attr=='connect']
assert len(calls)==3 and all('?mode=ro' in ast.unparse(x) and 'uri=True' in ast.unparse(x) for x in calls)
for name in ('q','n','n_go'):
    k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
    assert all(p.stat().st_mode&511==0o755 for p in [k/'job.sh',*k.glob('b/*.sh')])
    assert J.load(k/'k/a.json')['GO']==(name=='n_go')
J.write(D/'STATIC_TESTS.json',dict(status='PASS',sqlite_reads='mode=ro; no writable connection on input stores',shell_modes='0755 in q,n,n_go',GO='false except n_go',binaries=J.load(L/'out/kit_n_go/k/h.json')['binaries']))
print('frame stripping, real P recipe, SQLite URI and executable tests PASS')
