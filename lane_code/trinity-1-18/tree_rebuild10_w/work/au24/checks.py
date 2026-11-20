from pathlib import Path
import importlib.util,json,copy,io,tarfile,types,gzip
A=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('au',A/'orchard/au.py');au=importlib.util.module_from_spec(sp);sp.loader.exec_module(au)
w=A/'checks';w.mkdir(exist_ok=True);pool=w/'k_p';pool.mkdir(exist_ok=True)
data=b'abc\n';h=au.hashlib.sha256(data).hexdigest()
with tarfile.open(pool/'k_a','w') as t:
 m=tarfile.TarInfo('k_0');m.size=len(data);t.addfile(m,io.BytesIO(data))
spec={'sha256':h,'bytes':len(data),'paths':[],'archive':{'paths':['k_a'],'member':'k_0','sha256':au.sha(pool/'k_a')}}
p,e=au.stage_pin(pool,w,spec);assert p.read_bytes()==data
bad=copy.deepcopy(spec);bad['sha256']='0'*64
try:au.stage_pin(pool,w,bad)
except ValueError as e:assert str(e).startswith('E_HASH')
else:raise AssertionError('hash acceptance')
# The boot path writes both failure reports before returning an error.
m=au.read(A/'orchard/k.json');m['pool']=str(pool)
assert au.stage(w/'k_w',w/'o',m)==1
for label in ['C','P']:
 r=au.read(w/'o'/('AUDIT_TREE_'+label+'.json'));assert r['status']=='ERROR' and 'E_RUNTIME_MIRROR' in r['error']
# Success-only transformed counts and full example cap, using a small counter oracle.
api=types.SimpleNamespace(direct_transform=lambda raw:(raw,raw['changed']),routing=types.SimpleNamespace(direct_row=lambda raw:None))
frames=types.SimpleNamespace(resolve=lambda raw:({},{}))
with gzip.open(w/'k_r','wt') as f:
 for i in range(2):f.write(json.dumps({'qid':str(i),'changed':bool(i)})+'\n')
r=au.empty_result('C',m['trees']['C']);out=w/'au_1.json'
def persist():au.rankings(r);au.dump(out,r)
au.audit(api,frames,w/'k_r',r,persist);assert (r['rows'],r['passed'],r['transformed'],r['deferred'])==(2,2,1,0)
# A fatal parse error preserves previous counts through the worker's final handler.
state=au.read(A/'dry3/k_0.json');fatal=w/'k_f';fatal.mkdir();au.extract_tree(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out/kit_qd/k/t_e047002134f979bd.tar'),fatal/'k_C',m['trees']['C'])
with gzip.open(A/'dry3/k_r','rt') as f:first=f.readline()
with gzip.open(fatal/'k_r','wt') as f:f.write(first+'invalid\n')
state['pins']['rows']={'path':str(fatal/'k_r'),'sha256':au.sha(fatal/'k_r')};au.dump(fatal/'k_0.json',state)
assert au.worker(fatal,fatal/'o',m,'C')==1
r=au.read(fatal/'o/AUDIT_TREE_C.json');assert r['status']=='ERROR' and r['rows']==2 and r['deferred']==1
print(json.dumps({'archive_member_hash':'PASS','bad_hash_refused':'PASS','boot_error_persisted':'PASS','success_counters':'PASS','fatal_partial_counts':'PASS'}))
