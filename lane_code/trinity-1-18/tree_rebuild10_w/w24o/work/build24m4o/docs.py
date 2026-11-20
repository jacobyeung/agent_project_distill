from common import *
base=J.load(D/'BASELINE.json');plan=J.load(D/'MODE_R_PLAN_TEST.json')
usage='''Case b: the current sealed kits still refuse N's processor. `TREE_CHANGE_NEEDED_24M4K.md` identifies the required tree review. These helpers do not apply the patch or override a kit config. The explicit-pixel candidate fails handover and is not an uploadable configuration.

The helper delta is `UPLOADS_24M4K.json/.list`, against the recorded Orchard 24m4j kit seals and the fixed `16be8a21…` launcher. It contains only `rcj/rcj.sh` and `rcj/x.py`; no kit or database is uploaded. `UPLOADS_24M4K_GO.json` is empty for case b.

Both modes use preempt, one node, 16 CPUs, 128 GB, two hours, no GPU and no requeue. Library threads are capped at eight. The shell creates a fresh job-local directory under `SLURM_TMPDIR` or `/tmp`; its EXIT trap publishes after the sandbox exits. The inner `run` never publishes. `/dev` and `/proc` are bound in both modes. The existing `/project/community/jjyeung/c7d31ddd/venvs` mountpoint must remain present.

Submit commands for the operator, after the relevant review:

```bash
cd /project/community/jjyeung/okh7/x_22c714e1/qd
sbatch --job-name=q24k ../rcj/rcj.sh b
```

Mode `b` is the existing P-only rebuild. Omitting the argument also selects `b`. It retains the 65-pin reconstruction closure and its runtime assets, excluding checkpoint weights and frame payloads. It runs the native isolated P reconstruction and the complete `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84` gate.

```bash
cd /project/community/jjyeung/okh7/x_22c714e1/qd
sbatch --job-name=q24kr ../rcj/rcj.sh r
```

Mode `r` runs the kit's own `a.py r → pl.py → rb.py → rg.py` path, including P's base build, N's selection build and P's comparison reconstruction. It never advances into mode q or training. The authenticated resolver and `pl.plan_payload(..., regeneration=True)` supply its staging list; `pins.json` records the exact runtime entries, requested hashes, generated outputs and export parts. A planning pass stages requested inputs before the native entrypoint executes its own planner. The runtime uses the pinned venv, NumPy/fla overlays, closure and site aliases with the kit's `-s -B` startup behavior. P's child retains its isolated import probe. The native source tree is loaded once per process; the planning tree is not added to the mode-r import path.

Mode r excludes RGB payload archives, base-model tensor files and the independent initialization mirror. It retains frame-map/plan/FPS metadata, native row stores, selection inputs, removal lists, source archives and processor metadata. Unlike mode b, the unchanged native planner requires the authenticated export archive and its weight members; this helper does not omit them. The two unpinned frame-root arguments have empty read-only mountpoints because mode r never decodes RGB. A job-local read-only mount supplies processor metadata at its native path. The runtime assets, host and publication destination remain read-only inside the producer sandbox; only job storage and its logical alias are writable.

Publication writes `o/<job>/receipt.json`, `materialization.json`, `import_probe.json`, `db_bytes.json` and `timings.json`. Mode r also writes `routing_selection.json` and `k_*` aliases for native selection/base/comparison receipts, materializations and refresh records. `timings.json.files` records each existing artifact's source path, size and SHA256. Missing files receive `UNAVAILABLE`. Each artifact and each database record is attempted independently; publication errors retain a local `publication.json` even when the destination itself is read-only. A failed build keeps its nonzero exit status after publication.

`db_bytes.json` contains whole-file SHA256, size and the 16-byte header for P's base and N's selection databases in mode r, or the sole P database in mode b. `equal_target` applies to P's base. No SQLite file is copied into the project filesystem. Mode-r databases remain under job-local `dr/p/q/{base,selection,pr}/`; mode b uses `r/rows.sqlite`.

When both mode-r databases exist and P's full hash matches, the outside publisher verifies `rdiff.py` against `bc2db7747322d4c3eda8372ce4c9a3e74d457baa609f2798c465bf4054e75d92` and invokes it with N's database, P's base, C's staged tree, `q/n.json`, `--base q`, and `--out o/<job>/rd0`. A separate read-only evidence sandbox restores the native logical paths and exposes only the output directory as writable. The command never overrides rdiff's full P hash gate. `timings.json` records `staging_seconds`, `mode_r_seconds` or `build_seconds`, `rdiff_seconds`, and the rdiff/publication exit status. Comparison failures propagate through the EXIT trap.

If `rcj/P_SAMPLE_I.json` exists, it must be a JSON list of nonnegative integer row ordinals, or an object with an `i` list and optional `seed`. Duplicate ordinals, booleans and nonintegers refuse. After P's complete hash gate passes, the publisher reads `SELECT i,row,target FROM rows WHERE i IN (...)` in bounded batches and writes a JSON array of triples to `o/<job>/p_sample.json`, sorted by i. The seed is metadata; it does not choose additional rows. Missing ordinals contribute no rows. The complete serialized output must be at most 5,000,000 bytes, including JSON escaping. Oversize results refuse before opening the output. A failed P gate writes no sample. The sample can be published even when N fails after P's successful rebuild.

Local evidence: `RCJ_K_TESTS.json` covers samples, failed gates, independent success/refusal/stage-failure publication and actual read-only targets. `MOUNT_TESTS.json` covers the actual nested launch mounts. `RDIFF_MOUNT_TEST.json` covers the pinned comparison script and its full-hash refusal; `RCJ_CONTRACT_TESTS.json` also runs a successful synthetic row comparison. `MODE_R_PLAN_TEST.json` records the native planner's metadata walk against the supplied staging inventories, with unavailable payload checks and refresh explicitly stubbed. No production rebuild, Orchard execution or row review ran here. The supplied Orchard measurements are 18 seconds staging and 145 seconds P rebuild for 173660; they are not measurements of this new whole-mode-r helper.
'''
replace(L/'out/RCJ_USAGE.md',usage)
p=L/'out/ARM_ROUTING_USAGE.md';s=p.read_text().replace('w24j','w24k').replace('work/build24m4j','work/build24m4o')
start=s.index('The armed q/n delta declares')
end=s.index('\n\n',start)
s=s[:start]+'''The armed q/n delta declares the exact Orchard 24m4j q/n baseline recorded in `work/build24m4o/BASE_SEALS.json` and `BASE_FILES.json`. It explicitly carries `k/c.json`, `k/n.json`, `k/8.json` and `k/s.json`, and its hashes replay to the complete armed kits. `UPLOADS_24M4K.json` carries only the CPU helpers in case b; its GO manifest is empty. The current sealed configs cannot complete N regeneration until the separately proposed tree change is authorized, reviewed and sealed.'''+s[end:]
replace(p,s)
replace(L/'out/IMPORT_AUDIT.md','''The P reconstruction import audit is `work/build24m4j/IMPORT_AUDIT.md`: 75 explicit imports across 67 P modules, with the pinned source inventory and unchanged shadow/missing-module guards. The sealed `rb.py` bytes are unchanged in all four kits.

Mode b keeps the fixed launcher's isolated venv/overlay setup. Mode r additionally stages the pinned closure and runtime record, restores the discovery import-path order and site aliases under `-s -B`, binds processor metadata read-only at the native location, and invokes the kit's own `a.py r`. The planning pass imports C from job-local `c`; the execution process instead lets `a.py` load its sealed source. P's subprocess continues to use `-I -s -S -B` and its own import probe. The CPU helper publishes that probe independently on exit.

All local test interpreters ran through `work/build24m4o/run.sh`, which mounts the host read-only, binds only this workspace writable, uses the requested isolated p1cpu interpreter, and installs a hook that rejects superseded-workspace code. Runtime libraries were not downloaded or installed. Local tests do not establish Orchard package versions or instantiate its unavailable processor assets.
''')
files=[]
for p in sorted((L/'out/rcj').iterdir()):
 target=D/'upload/rcj'/p.name;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert J.sha(target)==J.sha(p)
 else:os.link(p,target)
 files.append(dict(name='rcj/'+p.name,local_path=str(target),sha256=J.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),action='replace'))
manifest=dict(schema='build24m4k-delta-v1',case='b',baseline='Orchard current 24m4j kits; fixed rcj launcher 16be8a21',baseline_kit_seals=base['kits'],baseline_helpers={n:J.sha(W/'work/rcj24m4j4'/n) for n in ('x.py','rcj.sh')},files=files,total_files=len(files),total_bytes=sum(v['bytes'] for v in files),kit_changes=False,tree_patch_applied=False,GO=False,upload_authorized=False,launch_authorized=False,production_mode_r_blocked='P_EXPORT_CONFIG_DIFFERENCE:max_pixels; tree review required',stream_root=str(D/'upload'))
replace(L/'out/UPLOADS_24M4K.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
replace(L/'out/UPLOADS_24M4K.list',''.join(v['name']+'\n' for v in files))
replace(L/'out/UPLOADS_24M4K_GO.json',json.dumps(dict(schema='build24m4k-go-delta-v1',case='b',files=[],total_files=0,total_bytes=0,GO=False,reason='No new GO kit: tree change requires authorization and review',baseline_kit_seals=base['kits']),sort_keys=True,indent=2)+'\n')
print('helper delta',manifest['total_files'],manifest['total_bytes'],'bytes; mode-r planner',len(plan['all_pins']),'u entries and',len(plan['requested']),'resolver requests')
