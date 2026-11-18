from pathlib import Path
import ast,json,hashlib,os,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1';G=L.parent/'wn2/work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=(G/'student_pilot/carrier_c1_run.py').read_text();new=(T/'student_pilot/carrier_c1_run.py').read_text()
fn=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.lineno<=966<=n.end_lineno)
other=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name==fn.name)
a=ast.get_source_segment(old,fn);b=ast.get_source_segment(new,other);assert a==b
record=dict(function=fn.name,before_line=fn.lineno,current_line=other.lineno,identical=True,sha256=hashlib.sha256(a.encode()).hexdigest())
(B/'INIT_UNCHANGED.json').write_text(json.dumps(record,indent=2)+'\n')
same=[]
for name in ('student_pilot/r1_handover.py','student_pilot/r1_training.py','student_pilot/row_text_audit.py','launch_r1/build.py','launch_r1/entry.py'):
    assert sha(T/name)==sha(G/name);same.append(dict(file=name,sha256=sha(T/name)))
(B/'N_BEHAVIOR_PRESERVED.json').write_text(json.dumps(same,indent=2)+'\n')
def size(root):
    total=0;pending=[root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for p in entries:
                if p.is_symlink():continue
                if p.is_dir(follow_symlinks=False):pending.append(p.path)
                elif p.is_file(follow_symlinks=False):total+=p.stat(follow_symlinks=False).st_size
    return total
sizes=dict(workspace=size(L),temporary=size(L/'work/tmp'),lane=size(L.parent))
assert sizes['workspace']<=8_000_000_000 and sizes['temporary']<=200_000_000 and sizes['lane']<=14_000_000_000,sizes
(B/'STORAGE.json').write_text(json.dumps(sizes,indent=2)+'\n');print(json.dumps(dict(init=record,storage=sizes)))
