from pathlib import Path
import json
r=Path(__file__).parent;root=r.parent.parent;src=r/'src';out=src/'out';out.mkdir(exist_ok=True)
baseline=r/'baseline/out';baseline.mkdir(exist_ok=True)
for name in ['NOTE_FOR_CONT_OPS.md','ORCHARD_ONLY_CHECKS.md']:(baseline/name).write_bytes((root/'out'/name).read_bytes())
review='''## Review round 1: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1: fill can outlive its foreground call | Detach with setsid/nohup; exclusive launch lock; write a/1.txt last; poll a/f.log and status at 60-second intervals | test_r1_detached_slow_fill |
| 2: local archives exceed practical defaults | Explicit structural fill uses tiny pinned stand-ins; live identity remains a native Orchard gate | test_r2_structural_without_archive_mirrors, including a planted dropped environment slot |
| 3: D had no complete check | Run every probe on the actual pack-built D delivery and plan its D scripts at 04:00:00 | test_native.py and test_r3_actual_D_integration |
| 4: absent staged inputs spend a token | Read-only size preflight runs before place and its attempt marker | test_r4_readonly_preflight_precedes_place |
| 5: system head rejected | Exempt listed utilities only in command position; scan arguments and retain umask 077 | test_r5_system_command_only |
| 6: operational and Python gaps | Document staging, fill timing and live hashes; execute guard, 8.py submit with stub sbatch, and the pool walk under 3.6.8 | test_r6_login_runtime_guard_submit_pool and test_r6_operational_inventory |
| 7: isolated import differs | Import h1eval.h10.launch as a module with production path roots | test_r7_production_module_import uses a relative import |
| 8: GPU refusal strands passed CPU work | gpu action rechecks completion and receipts; native a/8.txt and an exclusive pre-submit lock prevent duplicate submission | test_r8_gpu_only_retry |
| 9: arbitrary heredoc bypass | Permit only Python stdin heredocs | test_r9_only_python_stdin_heredocs |
| 10: native scorer drift | Keep the native source-consistency refusal; require a coherent generated release | test_native.py and test_07b_native_source_drift_blocks_release |
| 11: login delivery and ledger gaps | Place the recorded BUILD delivery in the login probe; require an operator ledger reservation before place | test_r11_login_exact_delivery and test_r6_operational_inventory |

No HIGH, MEDIUM or LOW finding is deferred. Missing production data and routed harness files are named in REQUIRED_INPUTS.json; check_required_inputs.py refuses absent local groups by name. A structural result does not certify production archive identity or a real full-reader run.
'''
(out/'NOTE_FOR_CONT_OPS.md').write_text('''# Step-600 packaging

The wrapper calls the native builder and checks its delivery before remote execution. Every action requires `--enable`; token adaptation and wrapper normalization default OFF. No production package has been placed or submitted by these tests.

1. Supply the reviewed delivery, items, step-600 binding, timing file and coherent D source/embedded release. Pin them and the native CPU/GPU scripts in the configuration. For r10, supply both original authenticated A/B deliveries and the filled/base A inputs. Run `check_required_inputs.py --manifest out/REQUIRED_INPUTS.json --group production_build` (or `r10` / `routed_harness`) after updating the paths. Missing inputs refuse by name. The raw supplied D scorer mismatch must be repaired by the lane's native generator; pack preserves the refusal.
2. Set `fill_mode: "structural"` explicitly. This runs the native fill and resolver on disposable tiny pinned archives with the required logical paths and preserved dependency slots. It leaves BUILD's delivery unchanged. The default `mirrors` mode authenticates all local bytes and refuses absent mirrors. The reviewed B5 archive sizes total **33,410,549,760 bytes**; the review estimates about **155 GB of reads** for that mode. `max_read_bytes` defaults to 1 GiB and `check_timeout` to 240 seconds per probe; the example explicitly uses 300 seconds with structural mode. Do not copy those large archives through Trinity for this structural check. Any full-mirror plan still needs the cluster's IO authorization and an admin plan above 30 GB.
3. Ensure BATCH.sh sets `umask 077`. `normalize_wrapper: true` adds it and retains the existing optional head-to-sed normalization. The scanner accepts the system `head` command without normalization; it still rejects forbidden words in arguments, paths and environments. The switch defaults OFF and preserves native delivery bytes when disabled.
4. Run `pack.py build --enable --config CONFIG --token HEX`, then `pack.py check --enable --config CONFIG`. Use the specified CPU Python with `-I -s -B`. These commands run isolated imports, frame rows, native guards, traps, fill, receipts, pool predicates and planning. The guard, place, fill, `3.py check` and `8.py submit` stub execute under `/usr/bin/python3` 3.6.8. A CHECK receipt binds the configuration, source and delivery.
5. Have the Orchard lane stage the real export parts, `.done` receipt and preparation files in the opaque directory named by `fill`. Populate `remote_input_pins` with the exact sizes for every fill input. The native `place_fill_d.py` documents verified reuse via `REUSE_PARTS_FROM`, preparation via `PREP_FROM`, and the one-pass GCS pull alternative (lines 66–108). Its conventional names are parts `0..3`, receipt `5`, and preparation `7/8/9`. **The whole native driver also places and fills a package: do not invoke it and pack place for the same token.** For the pack workflow, stage these inputs independently or reuse an already verified input directory. Pack performs no pull. Its read-only preflight checks every fill input and dependency/template/bwrap part before place creates a token directory. It checks sizes; native fill and `job.stage` establish live hashes.
6. Reserve the built token in the **Trinity ledger before place**, recording BUILD's delivery SHA and the token. Pack checks uniqueness at build but does not append the reservation. Keep the configured ledger path unchanged. `place` and `fill` print commands; `--execute-remote` runs them only in an authorized lane. When executing printed scripts manually, run `commands/preflight.sh` successfully before `commands/place.sh`. Fill launches detached, writes `a/1.txt` last, and polls at least 60 seconds apart. Every SSH call is capped at 300 seconds; `fill_wait` defaults to 1800 seconds. Inspect `a/f.log` and `a/f.exit` on failure; a timeout never triggers a relaunch.
7. `submit --enable --config CONFIG --yes --token HEX --execute-remote` submits the CPU check, polls completion, then runs native GPU gates. After a queue/pool refusal before submission, `gpu` with the same flags reuses the passed CPU check. It rechecks `COMPLETED`, `CPU.json`, all native receipt predicates and `a/8.txt`. The persistent `a/g.lock` is acquired immediately before sbatch: if present without a receipt, reconcile the submission manually. Never retry an uncertain transport failure automatically.

The actual export/RGB/environment, routed harness and r10 inputs remain absent. Native full-reader, live archive hashes, GPU work and trainer-rank USR1 behavior still need production evidence. D's native fixture reports a **19,595-second estimate** and `budget_fits=false` for four hours; pack does not override that result. REQUIRED_INPUTS.json and ORCHARD_ONLY_CHECKS.md state the remaining prerequisites.

'''+review)
(out/'ORCHARD_ONLY_CHECKS.md').write_text('''# Checks requiring Orchard or missing production inputs

The local structural check tests packaging logic without authenticating large production archives. CHECK.json records `production_archive_identity: false`. Default mirror mode still requires every pinned local archive. Both modes leave the delivery intact and require all phase scripts to validate before transport.

| Live check | Why it remains live | Failure evidence |
|---|---|---|
| Stage export parts, `.done`, preparation and dependency archives | The packaging command does not fetch them. The native place_fill_d.py uses REUSE_PARTS_FROM / PREP_FROM or a GCS pull; its whole driver owns placement too and must not share a token with pack place | Read-only remote size preflight refuses a missing or wrong-sized input before place; remote_input_pins must name every fill input |
| Fresh token and private modes | The Trinity ledger cannot prove Orchard directory state | Reserve the token in the Trinity ledger before place; atomic package mkdir rejects a used token |
| Fill duration and real export identity | Native a/4.py streams and hashes all export bytes; production duration is unmeasured here | Detached fill, a/f.log, a/f.exit, and final a/1.txt; short calls at least 60 seconds apart, 300-second call timeout, explicit 1800-second default fill_wait. Expiration stops without relaunch |
| Live dependency-archive hashes | Login 3.py check compares sizes only. Matching stand-ins or mirrors do not prove Orchard copies match | Native job.stage checks part, archive and member hashes in the CPU job before GPU submission; inspect a/4.log, a/4.err and CPU.json |
| Allocated node storage, namespace and bwrap support | Mount policy, free disk and real node environment depend on the allocation | Native CPU failure and readable stdout/stderr; no GPU submission without completion and CPU.json |
| Real full-reader/export/RGB/environment checks | Identical production bytes and job environment are absent here; these could run on Trinity if supplied and authorized | Native FULL_READER and MEMORY receipts plus journal; synthetic receipt tests prove predicates only |
| Real return-pool access and persistence | A local temporary pool cannot prove shared storage permissions or quota | Native guarded write and pool refusal before the GPU lock |
| CPU scheduling, sacct and general queue | These are live scheduler state | Short CPU submission/poll/GPU calls. Only explicit sacct-unavailable status 75 is tolerated, at most three consecutive errors; transport errors stop |
| GPU submission and retry ambiguity | Another lane may occupy general; transport can fail after sbatch accepts | gpu action rechecks COMPLETED and CPU.json without resubmitting CPU. Native a/8.txt plus a/g.lock block duplicate or uncertain submission |
| Slurm USR1 delivery and production ranks | Local shell and read-runner signals do not prove --signal=B:USR1@1800 delivery, teardown or trainer-rank cooperation | BATCH EXIT capture stores node, exit status and last 60 lines in a/x<job>; returned journals show partial work |
| Real GPU compute and memory | Tests use CPU only | Production CPU/GPU receipts and measured memory; no timing or GPU-memory claim from stand-ins |

The following checks run on Trinity under the actual `/usr/bin/python3` **3.6.8**: generated place, native fill, `3.py check`, the native CPU guard/dispatch helper, `8.py submit` with a stub `sbatch`, and the native pool-walk heredoc over a temporary pool. The pool test includes a positive directory and an injected oversized stat result. Submit uses the delivered BATCH bytes and records a synthetic job receipt. None of these tests calls Slurm. The full CPU job's model environment remains untested.

All calls retain stdout, stderr and exit status locally. The remote phase EXIT trap exposes the failing line; BATCH's EXIT trap preserves failure text even before a result archive exists. The B4 three-second cause and trainer-rank USR1 defect have no claimed repair.

'''+review)
(out/'PATCHES.md').write_text('''# Patch layout and verification

Apply `patch -p1` for both patches at a writable root corresponding to the supplied input mirror. Patch 01 adds the packaging command, structural probe generator, regression tests, input refusal tool and handoff documents. Patch 02 adds only pack_token.py and test_pack_token.py beside the native r10 and D builders. Neither patch edits native source or embedded scripts.

The top-level delivered files are canonical. TOOL_SHA256.json records their hashes. PATCH_VERIFIED.json records a fresh patch application, exact reconstructed-file equality, adapter-copy equality, source-input hashes and test log hashes. REPORT.md contains exact commands and outputs. Test output directories must be fresh; tests do not delete prior evidence.

Run test_native.py first, then pass its RESULT.json as PACK_NATIVE_RESULT to test_review.py. Run test_pack.py under the specified CPU Python and both additive adapter tests under /usr/bin/python3 3.6.8. Set CUDA_VISIBLE_DEVICES empty, OMP_NUM_THREADS=8, MKL_NUM_THREADS=8, OPENBLAS_NUM_THREADS=8, TOKENIZERS_PARALLELISM=false and PYTHONDONTWRITEBYTECODE=1; prefix commands with nice -n 10. The logged commands in REPORT.md include those settings.

Production actions require --enable. Token override requires --enable-token; wrapper normalization requires normalize_wrapper=true; structural fill requires fill_mode=structural. All default OFF or retain the original mirror path. Native D default-OFF delivery equality is measured. r10 default source equality is measured; its full build refuses missing original inputs. The raw D scorer mismatch remains a release blocker.
''')
inventory=(root/'out/CHECK_INVENTORY.md').read_text()
inventory=inventory.replace('Local mirrors authenticate the same archive bytes and preserve the remote names through a path adapter.','Mirror mode authenticates the same archive bytes; explicit structural mode substitutes tiny pinned stand-ins and defers live identity to native fill and job.stage.')
inventory=inventory.replace('Yes when all bytes are mirrored locally; missing mirrors block release','Mirror mode requires every byte locally; structural mode exercises required member paths and preserved slots with stand-ins')
inventory=inventory.replace('None beyond availability of authenticated mirrors','Mirror mode needs authenticated mirrors; structural mode proves the predicates on stand-ins')
inventory=inventory.replace('production preflight requires authenticated mirrors of all actual bytes and fails when they are unavailable.','structural preflight explicitly does not authenticate production archive bytes. Native Orchard fill and job.stage must establish live identity.')
inventory=inventory.replace('Pure receipt predicates and script sealing run locally; generated receipt tests exercise conditions','Receipt predicates, script sealing, native 8.py submit with stub sbatch, and the temporary pool walk run locally under 3.6.8')
(out/'CHECK_INVENTORY.md').write_text(inventory)
defects=(root/'out/DEFECT_MATRIX.md').read_text().replace('Optional trap normalization removes literal head.','System utility command words are exempt; arguments remain scanned.')
(out/'DEFECT_MATRIX.md').write_text(defects+'\n'+review)
(out/'FRAMEWORK_SOURCES.md').write_bytes((root/'out/FRAMEWORK_SOURCES.md').read_bytes())
cfg=json.loads((root/'out/config_step600.example.json').read_text());cfg['fill_mode']='structural';cfg['check_timeout']=300;cfg['remote']['fill_wait']=1800;cfg['mirrors']={}
cfg['remote_input_pins']={p:dict(bytes=0) for p in cfg['fill']['parts']+[cfg['fill'][k] for k in ('done','config','receipt','data_receipt')]}
cfg['required_inputs']=[dict(name='reviewed source delivery',path='/REPLACE/1.tgz',sha256='REPLACE_SOURCE_SHA256'),dict(name='step-600 binding',path='/REPLACE/binding600.json',sha256='REPLACE_BINDING_SHA256'),dict(name='D item manifest',path='/REPLACE/items.json',sha256='REPLACE_ITEMS_SHA256')]
(out/'config_step600.example.json').write_text(json.dumps(cfg,sort_keys=True,indent=2)+'\n')
items=[]
def required(name,group,path,reason,**extra):items.append(dict(name=name,group=group,path=path,location='local',reason=reason,**extra))
base='/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30'
for name,file,reason in [('reviewed source delivery','1.tgz','Actual reviewed step-600 source delivery and its SHA'),('step-600 binding','binding600.json','Object, four part pins, whole SHA, step, preparation pins'),('coherent D embedded release','o_build_D.sh','Regenerate the native embedded assets to match the current scorer')]:required(name,'production_build',str(root/'in/required'/file),reason)
for name,sha in [('a15_cot_ap1f6dfa8874e49e1e','ca977dd2bc6feb1c14c7c03023eefe7b5e2b67b1cabe838d34effbafd003c765'),('a15_cot_ap5e8d1fa8216c469d','be1f4dec0a2607e0590f0392ef1f7b6c44e3f60c34a06ad6b6a3f3cd551ea3ad')]:required('r10 original '+name,'r10',str(root/'in/required/r10'/name/'1.tgz'),'Native r10 verifies this exact delivery',sha256=sha)
for file in ['test_sequence.py','test_operator_memory.py','test_fixes.py','test_cpu_helper.py','test_room_pair.py','test_room_pair_labels.py']:required('routed '+file,'routed_harness',base+'/cont_ops16/work/c15/r1route/release/b2/work/'+file,'Referenced by run_release_gates.py; full harness assertions cannot run without this file')
for name,path,reason in [('step-600 export parts','fill.parts','Four actual production export parts and exact sizes'),('whole-tar completion receipt','fill.done','Upstream .done object/byte/SHA receipt'),('preparation config/receipt/data receipt','fill.config, fill.receipt, fill.data_receipt','Actual preparation files pinned by the sealed binding'),('dependency archives, template and bwrap','package a/0.json and ORCHARD_ASSETS.json','Real parts checked by remote preflight and native job.stage'),('production reader environment and RGB inputs','package input plan','Required for a real full-reader run')]:items.append(dict(name=name,group='orchard',location='orchard',config_key=path,reason=reason))
(out/'REQUIRED_INPUTS.json').write_text(json.dumps(dict(inputs=items,local_check='check_required_inputs.py --manifest out/REQUIRED_INPUTS.json --group production_build|r10|routed_harness',remote_check='pack place executes a read-only preflight before its placement marker; fill and job.stage verify live identity',production_ready=False),sort_keys=True,indent=2)+'\n')
(r/'review_section.md').write_text(review)
