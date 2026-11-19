from pathlib import Path
import hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/build12';N=L.parent
def local(s):
    s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/(?:wm|wn2|wn3|w10|w9f)(?=/|[\x27\x22\s])',str(L),s)
    s=re.sub(r'/scratch/jjyeung/orch_n30/tree_rebuild(?=/|[\x27\x22\s])',str(L),s)
    return s.replace('work/merge11','work/build12')
src=N/'wm/work/build10';dest=L/'work/build10';dest.mkdir(exist_ok=True)
for p in src.iterdir():
    if p.is_file() and p.suffix in ('.py','.sh'):(dest/p.name).write_text(local(p.read_text()))
for sub in ('eat1','eat1_clean'):
    for p in (src/sub).rglob('*'):
        if p.is_file() and p.suffix in ('.py','.json','.txt','.toml','.md'):
            q=dest/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(local(p.read_text()))
# Copies hold harness source only. The C8r fixture's RGB inputs stay read-only.
for name in ('c8r','gf1'):
    source=N/'wm/work/build7/proofs/eat1'/name
    for p in source.rglob('*'):
        if p.is_file() and (p.suffix in ('.jsonl','.json','.png','.jpg')):
            q=L/'work/build7/proofs/eat1'/name/p.relative_to(source)
            q.parent.mkdir(parents=True,exist_ok=True)
            if not q.exists():q.symlink_to(p.resolve())
for name in ('c8r','gf1','eat1/c8r/run','eat1/gf1/run'):
    (B/'proofs'/name).mkdir(parents=True,exist_ok=True)
# C8r is the requested final clause-table replay. Other receipts are disclosed as inherited.
p=dest/'final_eat10.py';s=p.read_text().replace("for name in ('gf1','c8r'):","for name in ('c8r',):")
s=s[:s.index("before=temporary_size()\nresult=subprocess.run",s.index("for name in"))]
p.write_text(s)
# Update delivery label without changing its exact-input frozen runner.
p=L/'work/n1fix2/make_delivery.py';s=p.read_text().replace('tree_rebuild_b11_','tree_rebuild_b12_')
s=s.replace("members.append(L/'work/build12/legacy9fix_source.py')", "members.append(L/'work/build12/legacy9fix_source.py')\nmembers.append(L/'work/merge11/legacy9fix_source.py')")
p.write_text(s)
# Selected helpers must not write through a foreign hard-coded workspace.
names=[L/'work/n1fix2'/n for n in ('test_runner.py','stage9.py','seal.py','make_delivery.py','package.py','packet_final.py','compare.py')]
names += [B/'sweep.py',dest/'final_eat10.py',dest/'monitor_eat10.py']
issues=[]
for p in names:
    for i,line in enumerate(p.read_text().splitlines(),1):
        if re.search(r'/tree_rebuild_w/(?:wm|wn2|wn3|w10|w9f)/',line):issues.append(dict(file=str(p),line=i,text=line))
(B/'SELECTED_PATH_AUDIT.json').write_text(json.dumps(dict(files=[str(p.relative_to(L)) for p in names],issues=issues),indent=2))
assert not issues
cfg=json.loads((L/'work/n1fix2/inputs/config.json').read_text())
print(json.dumps(dict(init=cfg['init_artifact'],r1_keys=list(cfg['r1_training']))))
