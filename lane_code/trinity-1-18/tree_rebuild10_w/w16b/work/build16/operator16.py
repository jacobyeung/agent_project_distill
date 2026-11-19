"""Publish the exact available staging inventory and unresolved host inputs."""
from pathlib import Path
import json,hashlib,sys,ast
L=Path(__file__).resolve().parents[2];B=L/'work/build16';T=L/'work/tree_r1';O=B/'proofs/operator';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,file_pin
cfg=load(B/'inputs/kit_config.json');pins={};seen=set()
def visit(v,depth=0):
    if isinstance(v,dict):
        if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):
            p=Path(v['path']);key=(str(p),v['sha256'])
            if key in seen:return
            seen.add(key)
            allowed=p.is_relative_to(L) or p.is_relative_to(Path('/scratch/jjyeung/n30_mirror')) or p.is_relative_to(L.parent/'ext') or p.is_relative_to(L.parent/'inputs')
            available=allowed and p.is_file()
            pins[str(p)]=dict(local_source=str(p),staged_name='u/'+hashlib.sha256(str(p).encode()).hexdigest(),sha256=v['sha256'],
                bytes=p.stat().st_size if available else None,status='available' if available else 'not rerun: input absent ('+str(p)+')')
            if available and depth<6 and p.suffix in ('.json',) and p.stat().st_size<20_000_000:
                try:child=load(p)
                except (ValueError,UnicodeError):return
                visit(child,depth+1)
        for x in v.values():visit(x,depth)
    elif isinstance(v,list):
        for x in v:visit(x,depth)
visit(cfg)
visit(file_pin(B/'inputs/kit_config.json'))
records=sorted(pins.values(),key=lambda p:p['staged_name'])
(O/'STAGING.json').write_text(json.dumps(records,indent=2))
pcfg={}
for name,path in [('A',L.parent/'ext/r1_ops/work/snap_fac07052/out/config.json'),
                  ('C',L.parent/'ext/r1_ops/work/snap_6a5c7d00/out/config.json'),
                  ('Cprime',L.parent/'inputs/p_configs/cprime_31abe087.json')]:
    c=load(path)
    pcfg[name]=dict(config=file_pin(path),output=c['output'],preparation_output=c['preparation_output'],continuation=c.get('continuation'),milestones=c.get('milestones'))
(O/'P_LOCATIONS.json').write_text(json.dumps(pcfg,indent=2))
old=L.parent/'w15/work/tree_r1/launch_r1/p_handover_receipt.py'
new=T/'launch_r1/p_handover_receipt.py'
assert old.read_bytes()==new.read_bytes()
(O/'P_PRODUCER_EQUALITY.json').write_text(json.dumps(dict(byte_equal=True,old=file_pin(old),current=file_pin(new)),indent=2))
kit=B/'kits/r1'
(O/'j.sh').write_bytes((kit/'b/q.sh').read_bytes())
request=dict(config=None,staged_pins=[],room_audit=None,frame_roots=[],weights=False)
(O/'REQUEST_TEMPLATE.json').write_text(json.dumps(request,indent=2))
lines=['# Production proof operator packet','','GO=false. No submission has run. The q mode is separate from training and emits RESULT.json. The complete host proof remains unqualified; see BUILD16_REPORT.md.','',
'## Files to stage','',
'STAGING.json lists every reachable pinned local input with its exact size, SHA-256, source path and opaque staged name. Missing inputs retain their expected pins and null sizes; they are not invented. Stage the source and control files from the fresh r1 kit according to its SHA256SUMS.txt. Keep this human-readable packet off the job-visible kit.','',
'| Source | Opaque staged name | Bytes | SHA-256 |','|---|---|---:|---|']
lines += [f"| `{r['local_source']}` | `{r['staged_name']}` | {r['bytes'] if r['bytes'] is not None else 'ABSENT'} | `{r['sha256']}` |" for r in records]
lines += ['','## P allocation persistence','',
'Run the unchanged build-15 launch_r1.p_handover_receipt producer inside P’s allocation after export publication. Pin h.json from the trusted ledger outside the received bundle. Preserve the original JSON bytes; map each hash to N’s local path in r1_training.persisted_files. Do not rewrite the absolute paths inside P’s JSON.','',
'Copy artifact.json; binding.json; the actual persisted runtime config; the preparation receipt; every referenced stream receipt and index; checkpoint complete.json with layouts; each rng file; and h.json. Keep checkpoint state shards in P’s tmpfs at step 400. The reader reports their absent paths and retained hashes without reading the shards. At step 600 the run archive can retain those shards, but N’s export initialization still does not read them. Export heads and full_weights travel in the one operator-provided tar. The tar’s hashes and sizes cannot be listed until a real export is supplied.','',
'The reader verifies the export manifest, index, shards and heads against h.json when weights are supplied. A metadata-only result explicitly reports export_bytes_verified=false and records absent export files. The native initializer ignores C1_INIT_LOCAL shortcuts inside the authenticated relocation scope and verifies the resolved export again.','',
'P_LOCATIONS.json pins the supplied A/C/Cprime configs. Their output and preparation_output are logical roots; the runtime config and h.json determine the job-local locations. The native trainer writes binding.json at the runtime output root, m400 or m600 exports, and checkpoint_000400 or checkpoint_000600 directories with an optional UUID suffix. Do not infer a relocated filename from the nominal job path. Sources: student_pilot/carrier_c1_run.py run_steps/checkpoint/train, the supplied drv_cp/README.md and pre1_light.sh.','',
'## Required initialization evidence','',
'The preserved build-15 keep-opener gate also requires a routing_vocabulary witness v.json bound to the export and lineage. P’s mandated persistence list does not include this witness. Reconstructing it requires the model manifest named by P’s preparation plus its pinned tokenizer/config metadata and the parent artifact. Those inputs are not all in h.json’s direct closure. Without independently available exact replicas, the full initialization must refuse; metadata handover admission does not waive this requirement. Native trainable-group verification also reads that model manifest and config.json. No real P export was supplied, so their existence outside P’s tmpfs was not checked.','',
'## Invocation and outputs','',
'The operator resolves REQUEST_TEMPLATE.json with a pinned N runtime config, every staged pin, frame roots, and a complete room audit bound to the same row_sources and remove_files. The current local positive-hit subset is not a complete room audit. The request’s weights field enables the full CPU forward only after all export bytes verify. After native preparation and population binding, the mode derives a pinned handover_mapping and continuation identity from the authenticated donor and final N inputs; optimizer differences still refuse.','',
'Run from the staged kit: `bash b/q.sh /tmp/<opaque-new-root> /tmp/<opaque-request>.json`. The supplied j.sh requests one general-partition CPU task, eight CPUs and 20 GiB allocation, with a 20 GiB process address-space ceiling. No GPU is requested. Full 9B CPU fit has not been measured; no GPU fallback has been justified or run.','',
'Expected outputs: RESULT.json; p/ native admission outputs; b/ bound population/config/indices; a/ loader audit; h/ final continuation mapping, preparation receipt and config; and f.json with every rank’s first resumed batch, per-stream loss summaries and peak RSS when weights are supplied. Native routing build and composition run inside s1_admission before prepare. Named refusals leave status=REFUSE and GO=false.','',
'The CPU witnesses cover persisted handover, native export loading and the resumed full-forward reader path separately. A single successful native s1_admission → bind_prepared → production_audit → handover → forward fixture remains unproven. Do not treat this packet as production qualification.']
(O/'OPERATOR.md').write_text('\n'.join(lines)+'\n')
print('Inventory entries',len(records),'available',sum(r['status']=='available' for r in records))
