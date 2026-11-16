import ast,hashlib,json,os,shutil,stat,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';errors=[]
for root in (L/'work/tree_r1/student_pilot',L/'work/tree_r1/launch_r2',L/'work/tree_r1/tests',B):
    for p in root.glob('*.py'):
        try:ast.parse(p.read_text())
        except SyntaxError as e:errors.append(dict(file=str(p.relative_to(L)),error=str(e)))
protected=json.loads((L/'work/build5/proofs/artifact_locations/PROTECTION.json').read_text())['paths']
protection=[]
for row in protected:
    p=L/row['path'];mode=stat.S_IMODE(p.stat().st_mode)
    protection.append(dict(path=row['path'],mode=mode,expected=row['mode'],unchanged=mode==row['mode']))
totals={'lane':0,'temporary':0};files=0;t=time.monotonic()
for root,dirs,names in os.walk(L,followlinks=False):
    dirs[:]=[d for d in dirs if not (Path(root)/d).is_symlink()]
    for name in names:
        p=Path(root)/name
        if p.is_symlink():continue
        size=p.stat().st_size;totals['lane']+=size;files+=1
        if p.is_relative_to(L/'work/tmp'):totals['temporary']+=size
pins={}
for name in ('work/tree_r1/student_pilot/trace_grammar.py','work/tree_r1/student_pilot/r2_dev_merged.json'):
    pins[name]=hashlib.sha256((L/name).read_bytes()).hexdigest()
result=dict(syntax_errors=errors,storage_bytes=totals,scratch_free_bytes=shutil.disk_usage('/scratch').free,
            inventory_files=files,inventory_seconds=time.monotonic()-t,protected=protection,pins=pins)
(B/'STATIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='protected'}))
assert not errors and totals['lane']<=4_000_000_000
assert all(r['unchanged'] for r in protection)
assert pins['work/tree_r1/student_pilot/trace_grammar.py']=='a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268'
assert pins['work/tree_r1/student_pilot/r2_dev_merged.json']=='a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'
