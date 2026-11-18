"""Source-authenticated monitoring for the actual bounded loader and config check."""
import ast,hashlib,json,os,runpy,sys,types
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';T=L/'work/tree_r1';O=B/'proofs/loader_audit'
sys.path[:0]=[str(T),str(B)]
from compact_tmp import inventory
module=ast.parse((B/'test_runner.py').read_text())
node=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='code_digest')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(B/'test_runner.py'),'exec'))
snapshots={};expected={};hits={}
for p in T.rglob('*.py'):
    if set(p.relative_to(T).parts)&{'artifacts','__pycache__','.git'}:continue
    raw=p.read_bytes();snapshots[str(p.relative_to(T))]=hashlib.sha256(raw).hexdigest()
    try:pending=[compile(raw,str(p),'exec',dont_inherit=True)]
    except SyntaxError:continue
    expected[str(p)]=set()
    while pending:
        code=pending.pop();expected[str(p)].add(code_digest(code));pending.extend(v for v in code.co_consts if isinstance(v,types.CodeType))
mon=sys.monitoring;mon.use_tool_id(4,'loader-proof')
def started(code,offset):
    if code.co_filename in expected and code_digest(code) in expected[code.co_filename]:mon.set_local_events(4,code,mon.events.LINE)
    return mon.DISABLE
def line(code,number):
    hits.setdefault(str(Path(code.co_filename).relative_to(T)),set()).add(number);return mon.DISABLE
mon.register_callback(4,mon.events.PY_START,started);mon.register_callback(4,mon.events.LINE,line);mon.set_events(4,mon.events.PY_START)
records=[]
for script in ('loader_audit.py','native_cfg_check.py'):
    before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
    runpy.run_path(str(B/script),run_name='__main__')
    after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
    records.append(dict(proof=script,before_bytes=before,after_bytes=after))
mon.set_events(4,0)
for name,value in [('source_hashes',snapshots),('hits',{k:sorted(v) for k,v in hits.items()}),
 ('results',dict(tests=len(records),passed=[r['proof'] for r in records],failures=[],errors=[],skips=[],
                 complete=True,fatal=None,coverage_code_filter='compiled-source fingerprint',records=records))]:
    (O/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
