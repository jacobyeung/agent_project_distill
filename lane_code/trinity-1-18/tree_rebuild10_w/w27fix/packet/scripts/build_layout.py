# Build a replica of job 174101's namespace layout (paths as the job script binds them).
#   <ns>/q_22c714e1/p/q/u/<sha256>  every pinned small input under its hash name (kit: z.copy_resolved_payload, pl.stage)
#   <ns>/c7d31ddd/runs/aws128p_20261025/models/a32330d0/snapshots/<rev>/<name>  the staged base snapshot (job script tk_stage_model)
# Real bytes: the model manifest, P's receipts/configs (W/ext/m400real/files = the milestone's small-file archive) and the
# nine non-weight model files (fetched from the job's pool). Weight shards are 1-byte placeholders (model load is stubbed).
import sys,os,json,hashlib,tarfile,shutil
from pathlib import Path
ns,proc9,m400=Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3])
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
u=ns/'q_22c714e1/p/q/u';u.mkdir(parents=True,exist_ok=True)
with tarfile.open(proc9) as t:
    for m in t:
        raw=t.extractfile(m).read();assert hashlib.sha256(raw).hexdigest()==m.name
        (u/m.name).write_bytes(raw)
n=0;skipped=[]
for p in sorted((m400/'files').rglob('*')):
    if p.is_file() and not p.is_symlink():
        if p.stat().st_size>80_000_000:skipped.append((str(p)[-60:],p.stat().st_size));continue
        h=sha(p)
        if not (u/h).exists():shutil.copyfile(p,u/h)
        n+=1
for name in ('e.json','r.json'):
    p=m400/name
    if p.is_file():
        h=sha(p)
        if not (u/h).exists():shutil.copyfile(p,u/h)
print('u entries',len(list(u.iterdir())),'from m400real files',n,'skipped big',skipped)
man_sha='cc724d5ee1b0bd62ba759be3eb0831afd009cd7635ea5966ddc0fd26c4599fb7'
man=json.loads((u/man_sha).read_text());root=man['root']
prefix='/project/community/jjyeung/c7d31ddd/'
assert root.startswith(prefix),root
snap=ns/'c7d31ddd'/root[len(prefix):];snap.mkdir(parents=True,exist_ok=True)
real,placeholder=[],[]
for name,h in sorted(man['files'].items()):
    t=snap/name
    if t.exists():continue
    if (u/h).is_file():os.link(u/h,t);real.append(name)
    else:t.write_bytes(b'\0');placeholder.append(name)
print('manifest root',root);print('snapshot replica',snap,'real',real,'placeholder',placeholder)
e=json.loads((m400/'e.json').read_text())
print('e.json schema',e.get('schema'),'step',e.get('step'),'pins',len(e.get('pins',{})))
miss=[k for k,p in e['pins'].items() if not (u/p['sha256']).is_file()]
print('handover pins without real bytes in u (big files):',miss)
json.dump(dict(snap=str(snap),u=str(u),missing=miss),open(ns/'layout.json','w'))
