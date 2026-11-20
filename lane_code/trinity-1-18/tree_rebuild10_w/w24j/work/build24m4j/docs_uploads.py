from common import *
import copy
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
seals={n:verify(kit(n)) for n in NAMES}
assert seals==J.load(D/'SEALS.json')
assert digest(inventory(T))=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
assert len({J.sha(kit(n)/'b/rb.py') for n in NAMES})==1
for n in NAMES:
 assert J.load(kit(n)/'k/a.json')['GO']==J.load(kit(n)/'BUILD.json')['GO']==(n=='n_go')
base=J.load(D/'BASE_FILES.json');base['qd']=J.load(L/'work/build24m4i/ORIGINAL_KITS.json')['qd']
baseseals=J.load(D/'BASE_SEALS.json');baseseals['qd']=J.load(L/'work/build24m4i/BASE_SEALS.json')['qd']
assert baseseals['qd']=='62d8a7f54be1c5783c41d7904ae8362ed35566d15d3a1c28068f63098002d79d'
final={n:{str(p.relative_to(kit(n))):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in kit(n).rglob('*') if p.is_file()} for n in NAMES}
rows=[];upload=D/'upload';upload.mkdir()
def record(p,name):return dict(name=name,sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),local_path=str(p),action='replace',transfer='local-upload')
for n in ('q','n','qd'):
 for rel,v in sorted(final[n].items()):
  if v!=base[n].get(rel):
   q=upload/n/rel;q.parent.mkdir(parents=True,exist_ok=True);os.link(kit(n)/rel,q);rows.append(record(q,n+'/'+rel))
for p in (L/'out/rcj').iterdir():
 q=upload/'rcj'/p.name;q.parent.mkdir(exist_ok=True);os.link(p,q);r=record(q,'rcj/'+p.name);r['action']='add';rows.append(r)
replay=copy.deepcopy(base)
for row in rows:
 n,rel=row['name'].split('/',1)
 if n in replay:replay[n][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
assert all(replay[n]==final[n] for n in ('q','n','qd'))
assert {'qd/k/c.json','qd/k/n.json','qd/k/8.json','qd/k/s.json','qd/k/p.json'}<={r['name'] for r in rows}
up=dict(schema='build24m4j-upload-diff-v1',baseline='Orchard q and n at 24m4i after the lane overlay; qd at 24m4h 62d8a7f5 with the 24m4i qd delta not yet applied',baseline_kit_seals={n:baseseals[n] for n in ('q','n','qd')},files=rows,total_files=len(rows),total_bytes=sum(r['bytes'] for r in rows),stream_root=str(upload),kits={n:seals[n] for n in ('q','n','qd')},GO=False,n_go_upload_authorized=False,uploaded=False,launch_authorized=False,qd_delta_includes_24m4i=True,shared_u_baseline='24m4i shared u files are already staged by the q/n overlay; P tree u/e5be8157 was present in 173626',outside_kit_files=['rcj/rcj.sh','rcj/x.py'])
J.write(L/'out/UPLOADS_24M4J.json',up);(L/'out/UPLOADS_24M4J.list').write_text(''.join(r['name']+'\n' for r in rows))
go=[record(kit('n_go')/rel,'n/'+rel) for rel,v in final['n_go'].items() if v!=final['n'][rel]]
assert {r['name'] for r in go}=={'n/k/a.json','n/BUILD.json','n/SHA256SUMS.txt'}
J.write(L/'out/UPLOADS_24M4J_GO.json',dict(schema='build24m4j-go-diff-v1',base_kit_seal=seals['n'],kit_seal=seals['n_go'],files=go,total_files=len(go),total_bytes=sum(r['bytes'] for r in go),upload_authorized=False))
J.write(D/'UPLOAD_REPLAY.json',dict(status='PASS',baseline_kit_seals=baseseals,final_kit_seals=seals,all_three_kits_exact=True,ordinary_delta_files=len(rows),ordinary_delta_bytes=up['total_bytes'],qd_against_24m4h=True,GO_excluded=True))
payload=json.loads((kit('n_go')/'k/c.json').read_text());config=J.load(kit('n_go')/'k/c.json')
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=digest(inventory(T)),kits=seals,rb_sha256=J.sha(kit('qd')/'b/rb.py'),n_go_payload_sha256=payload['sha256'],n_go_identity=identity(config),GO='false except out/kit_n_go',full_database_gate='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84',P_selection='5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))
helpers=sum(p.stat().st_size for p in (L/'out/rcj').iterdir())
(L/'out/RCJ_USAGE.md').write_text(f'''Apply `UPLOADS_24M4J.json` from its declared mixed baseline. Its qd delta is against 24m4h `62d8a7f5`; it includes the unapplied 24m4i qd configuration changes. The shared `u/` files from the q/n 24m4i overlay and the authenticated P archive must already exist.

Copy the manifest's kit files to `/project/community/jjyeung/okh7/x_22c714e1/`. Copy these two helpers to the same root ({helpers} bytes total):

- `out/rcj/rcj.sh` → `rcj/rcj.sh`
- `out/rcj/x.py` → `rcj/x.py`

Ensure `/project/community/jjyeung/okh7/x_22c714e1/j/` exists. Submit once from the qd directory:

```bash
cd /project/community/jjyeung/okh7/x_22c714e1/qd
sbatch --job-name=q24j ../rcj/rcj.sh
```

The command overrides `JOBNAME_PLACEHOLDER`. The script requests preempt, 16 CPUs, 128 GB and two hours, with no GPU or requeue. It creates a fresh directory under `SLURM_TMPDIR` (or `/tmp`), uses eight library threads, and runs offline.

The helper uses the qd resolver, handover reader and pinned staging implementation for 65 pins in the recipe/source closure, plus the Python runtime and staging helpers. It stages tokenizer/config metadata, the legacy database and row inputs; it does not stage checkpoint weights or frame payloads. It runs P's native reconstruction through rb.py and retains the complete `4e8e6c04…` file-hash gate.

The job writes `receipt.json`, `materialization.json`, `db_bytes.json`, `import_probe.json` and `timings.json` under `x_22c714e1/o/${{SLURM_JOB_ID}}/`. Missing artifacts receive an `UNAVAILABLE` record. Publication attempts each artifact independently before propagating failure. The database record contains its whole-file SHA256, byte size and 16-byte header in hex; the SQLite file stays in node-local `r/rows.sqlite`. Logs go to `x_22c714e1/j/` through the kit's name filter.

173626 staged from 05:09:40Z to 05:29:24Z (1184 s). Its first non-frame staging interval ended at 05:13:26Z (226 s); the remaining 958 s included frame and initialization work. Budget 3–6 minutes for this reduced staging as a heuristic, then measure `staging_seconds` and `build_seconds`. No Orchard execution or measured reconstruction time is claimed.
''')
print('DELTA',len(rows),up['total_bytes'],'helpers',helpers,'GO',len(go));print('SEALS',seals)
