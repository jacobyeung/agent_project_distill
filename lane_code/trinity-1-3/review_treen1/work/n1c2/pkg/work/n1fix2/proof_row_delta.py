from pathlib import Path
import ast,json,sys,hashlib,os
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/row_delta'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.r2_adapters import normalize
from student_pilot import row_text_audit as current
node=next(n for n in ast.parse((B/'proof_text.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='norm')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(B/'proof_text.py'),'exec'))
source=B/'original/student_pilot/row_text_audit.py';old={'__name__':'old_text_audit'}
exec(compile(source.read_text(),str(source),'exec'),old)
results={}
for name in ('a0_recovery','a0_units','a0_pool_abs_distance_reworded','a0_room'):
    path=L/'work/rows_slices/slices_final'/(name+'.jsonl');count=0;changes=[];h=hashlib.sha256()
    for raw in path.open('rb'):
        h.update(raw);count+=1;assert count<=2000
        row=norm(json.loads(raw));a=old['reasons'](row);b=current.reasons(row)
        def verdict(fn):
            try:fn(row,'routing');return 'admit'
            except ValueError as e:return str(e)
        av=verdict(old['check']);bv=verdict(current.check)
        if a!=b or av!=bv:changes.append(dict(qid=row.get('qid'),old_gate=a,new_gate=b,old_reader=av,new_reader=bv))
    results[name]=dict(source=str(path.relative_to(L)),sha256=h.hexdigest(),rows=count,changed_rows=changes)
(O/'RESULT.json').write_text(json.dumps(dict(old_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),families=results),indent=2))
assert not any(r['changed_rows'] for r in results.values())
monitor.save(O)
print('No original slice row changes in either text-admission check.')
