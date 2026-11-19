"""Write the final contract with current measurements and exact CPU outputs."""
import json,re,shlex,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
m=json.loads((O/'patches/MANIFEST.json').read_text());r=json.loads((C/'RESULTS.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text())
old=(L/'out_round6/REPORT.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip()
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
review=readme.split('## Review round 6: finding -> fix -> test',1)[1]
equality=old[old.index('## Equality and mutation limits'):old.index('## Measured profile and forecast')]
profile=old[old.index('## Measured profile and forecast'):old.index('## Measured CPU guard overhead')]
audit=old[old.index('## Review round 4: finding -> fix -> test'):old.index('## Commands and exact outputs')]
review5=old[old.index('## Review round 5: finding -> fix -> test'):old.index('The wrapper is vendored')]
patches='\n'.join('| ['+name+'](patches/'+name+') | '+str(pin['bytes'])+' | `'+pin['sha256']+'` |' for name,pin in m['patches'].items())
bench='\n'.join('| '+str(v['parameter_count'])+' | '+str(v['parameter_tensors'])+'/'+str(v['buffer_tensors'])+' | '+str(v['weight_and_buffer_bytes'])+' | '+f"{v['before_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_install_seconds']:.3f}"+' | '+f"{v['boundary']['median_seconds']:.3f}"+' |' for v in cost['cases'])
report=f'''VERDICT: DONE All five LOW findings and the two actionable INFO items pass CPU verification; production adoption requires the bound H100 GPU byte gate.

Measured validation: **{workspace} workspace tests and {applied} fresh-application tests pass**. The nine round-6 regressions fail on the reviewed snapshot with **31 expected assertion failures**, then pass on the delivered implementation. The baseline includes the actual `ModuleNotFoundError` from the README unpack subprocess. All retained before-fix controls reran. Five diffs apply with zero fuzz; all original reader files and original/OFF output bytes remain unchanged. ON CPU fixtures retain exact answers and traces. GPU ON/OFF equality remains unmeasured and mandatory.

Measured resources: the suite's largest child-process peak RSS was **{r['max_child_rss_bytes']:,} bytes**; the separate guard benchmark peak was **{cost['max_rss_bytes']:,} bytes**. These are process peaks, not GPU memory measurements. The workspace measured **{size:,} unique-inode bytes** at report generation, below 3,000,000,000. Immutable completed fixtures share identical bytes through hard links; all paths were preserved. [STORAGE6.json](checks/STORAGE6.json) and [storage6.txt](checks/storage6.txt) record the sharing. The task observed no workspace-cap violation.

The supplied existing A4 timings support an **estimate** of **7,351.824 s for the 636-item read**, with zero credited cache saving. The separate Package D estimate is **13,813.069 s for 580 distance items**; a19 has **no ON route** for Package D. Neither number measures a step-600 GPU run.

Work began at **15:13:03 UTC on 2026-11-19**; the deadline is **16:13:03 UTC**. This report was generated at {stamp}. The original delivery is preserved in [out_round6](../out_round6/). CPU execution used torch {r['torch']}, transformers {r['transformers']}, eight torch threads, nice -n 10, and CUDA hidden. No Git, SSH, scheduler action, GPU execution, paid API, input-tree edit or deletion command ran. Network reads covered official PyTorch documentation only.

## Review round 6: finding -> fix -> test
{review}

The two remaining INFO notes stay documented. `done` and `prep_paths` are inert, authenticated operation metadata; removing them would disrupt the operation plan without improving admission. Restored-between-boundary raw writes cannot be caught by the reviewed identity/counter checks; detecting them would require stronger interception or per-call content hashing, which changes the reviewed cost contract. Existing path-preservation and weight-guard regressions still run.

The detached fill is a single attempt. Its permanent `a/0.lock` prevents concurrent or repeated launches; nohup detaches the entire pull/fill/dry sequence; the EXIT trap records success or failure in `a/1.txt`. Tests exercise the generated launcher, lock, log and exit trap with tiny success/failure commands. They do not fetch the roughly 21.6 GB production export. A hard kill can leave no exit receipt; the owner inspects the log and starts a fresh token rather than retrying the same attempt.

The submit checker embeds the complete assertion block from `cont_ops17/work/o_sub_A4.sh:7-37` verbatim. It retains cache-budget and return-pool checks. The added GPU receipt is token-only and binds success, plan, profile, restore/binding/export pins and the H100 80 GB requirement. The CPU integration uses the actual fixture CPU proof, verifies its emitted asset receipts, exercises receipt serialization and proves that a failed GPU receipt refuses submission. Its synthetic receipt is a test control, not GPU evidence.

The gate checks exact RESTORE.json and artifact-binding hashes against CPU READY, plus run/step/member/lineage/object/config/archive/preparation identity against the adopted binding. Workers recheck staged receipt bytes and the manifest hash. The original loader then verifies every pinned checkpoint/component file before model loading (`b/e2e_reader/parity.py:190-196`, `b/e2e_reader/artifact.py:109-120`). Preserving the CPU logical root keeps those pinned paths valid. The README stages a neutral byte-identical binding alias at `d/7.json`; private settings must map to the same file.

Device checks use the CUDA properties for device 0 and refuse a non-H100 name, a capability other than 9.0, or total memory outside 79–86 billion bytes. This is a production device-class policy; MIG and the 94 GB NVL variant fail closed. CPU tests supply explicit property stubs. Actual H100 compatibility and performance remain unrun.

## Adoption contract

Follow [README](kit_parity50/README.md) in order. Apply reader patches 01–03 and operator patches 04–05 to fresh A4 copies. Derive the real reviewed step-600 binding; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; generate and place the pinned operations; run detached fill and require exit 0; obtain the allocated CPU proof and emitted receipts; stage the same assets; pass the GPU gate; authenticate/install its `ue.json` as `a/g.json`; submit; fetch and unpack.

The default profile is A4's 636 items, one GPU, general/no-requeue, caches only, with a 12 GiB host-cache allowance. `--processor-only` selects 4 GiB and requires its own gate. Both leave scene sharding and atomic journals disabled. No multi-card A4 operator is delivered. Owner transport, allocations, the real target binding and storage capacity remain external inputs.

A refused unpack leaves its extracted tree behind. Scorers must use only success output after unpack exit status 0; `complete=false` remains partial. The documented command runs `-s -B` from the operator directory and gates its handoff with `&&`.

{equality}
{profile}
## Measured CPU guard overhead

Each stub uses bf16 parameters shaped 2048×1024 and a 1024-element buffer per module. Forward returns a 32-element tensor without model-sized matrix work. Each implementation runs one miss and a warm hit, then seven timed hits; boundary cost is the median of three hashes. These are CPU cache costs, not GPU speedups. Exact samples are in [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Per-call hashing ms | Boundary guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{bench}

## Framework and source evidence

[FRAMEWORK_EVIDENCE](FRAMEWORK_EVIDENCE.md) provides installed torch/transformers file:line citations and official documentation links. The new device guard relies on `torch/cuda/__init__.py:641-695` and `torch/_C/__init__.pyi:12448-12453`. [SOURCE_EVIDENCE6.json](checks/SOURCE_EVIDENCE6.json) pins those files and the cont_ops submit reference. The official [device-properties](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html) and [capability](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_capability.html) pages were checked on 2026-11-19. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun mutation-counter probes. No GPU property was queried locally.

## Patches and authentication

A4 source base: `{m['base_pin']['sha256']}` over {m['base_pin']['files']} files. Reviewed payload: `{m['a4_payload_pin']['sha256']}` ({m['a4_payload_pin']['bytes']} bytes). B5 base archive: `{m['b5_base_archive_sha256']}`. B5 validation proves applicability; the GPU kit authenticates A4.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patches}

Reader patches add 36 files under `u0/`, including the regression tests. Operator patches remain behind `read_extensions`; the ON CPU helper additionally exports the small asset receipts. The original bootstrap bytes remain unchanged. MANIFEST records the six additional copied-member pins, base batch and decoded-bootstrap pins, patched operator hashes, complete source inventories, kit and operation files. The builder requires all those applicable pins before copying. Fresh-application OFF, round-4/5/6 and comparator suites pass; the applied extension bytes equal the workspace-tested bytes.

The development source copy contains 85 original reader files; their bytes match the base, and tests obtain the remaining immutable resources through READ_INPUT_SRC. The fresh applied source contains and authenticates all 927 original files. The final seal checks both inventories explicitly.

## What could go wrong and how we would notice

| Risk | Detection and action |
|---|---|
| Wrong A4 member, base batch, bootstrap or extension | Builder refuses the pin mismatch before creating output. |
| Interrupted fill or duplicate launch | Permanent attempt lock refuses duplicates; log and exit receipt distinguish completion. Missing receipt requires inspection and a fresh token. |
| Stale CPU proof or jointly resealed batch/package | Full cont_ops receipt assertions compare the proof with current batch, dispatch, guard, input, operator and memory bytes. |
| Wrong checkpoint or modified staged files | READY/identity checks, per-worker receipt/manifest checks and original component hash verification refuse. |
| Missing, failed or unrelated GPU evidence | Submit requires `a/g.json` for this plan/profile/assets/device. A CPU proof alone cannot authorize the read. |
| Namespace or alias differs from CPU staging | Path validation, asset checks or the original loader fails before reading; preserve the logical root and neutral alias bytes. |
| GPU kernels or eager SAM change answer/trace bytes | Require zero byte differences; equal scores do not waive the gate. |
| Cache overhead erases savings or process memory exceeds cache caps | Compare full worker wall time and measure host/GPU peaks on the real allocation. |
| Raw tensor write restored between boundaries | Frozen ownership remains required; that sequence is outside guard coverage. Persistent raw writes fail a boundary check. |
| Refused or partial return is scored | Require unpack exit 0 and success JSON, then inspect complete status. |

## Not done

No real step-600 export/binding, large pull, production restore, namespace/transport/storage run, GPU parity/performance/memory measurement, scheduler submission, upload, return publication or persistent-storage requeue ran. No batching or multi-card A4 operator is delivered. The array policy remains approved=false. Delivered CPU suites need no local OS sockets.

The first complete-suite attempt caught a non-opaque path in the staging example; [run_checks6_development.txt](checks/run_checks6_development.txt) retains that failure. The corrected example passes the full rerun. No cluster kill or automatic relaunch occurred. The requested review audit sections below are retained because the binding prompts explicitly require them.

## Required review audit sections

{review5}
{audit}
## Commands and exact outputs

Commands ran from `{L}`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then executes the required Python with `nice -n 10 -I -s -B`. Tests set eight torch threads. Child commands inherit priority and environment. Fixture storage shares identical immutable input bytes and detaches shared files before edits.

The README unpack subprocess intentionally uses `-s -B` without `-I`, as finding 1 requires, so the authenticated sibling helper can import. Its interpreter, CPU environment and priority remain the same.

Test commands additionally use READ_INPUT_SRC={m['base']} and READ_TEST_TMP={L/'work/test-artifacts'}. Applied commands use READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE from the fresh verification root. Every output below is literal; baseline failures are expected regression controls.

'''
def block(command,name):
    return '```bash\n'+command+'\n```\n\nExact output:\n\n```text\n'+(C/name).read_text().rstrip()+'\n```\n\n'
for command,name in [('bash work/cpu.sh work/run_checks.py','run_checks6.txt'),
    ('bash work/cpu.sh work/run_fixture5.py work/build_patches.py','build_patches6.txt'),
    ('bash work/cpu.sh work/gate_integration6.py','gate_integration6.txt'),
    ('bash work/cpu.sh work/profile.py','profile_rerun.txt'),
    ('bash work/cpu.sh work/torch_versions3.py','torch_versions3.txt'),
    ('bash work/cpu.sh work/benchmark_round3.py','cache_cost3.txt'),
    ('bash work/cpu.sh work/docs_check6.py','docs6.txt'),
    ('bash work/cpu.sh work/share_storage6.py','storage6.txt')]:report+=block(command,name)
for row in [*r['results'],*m['applied_cpu_suites']]:report+=block(shlex.join(row['command']),row['output'])
for name,script,var,args in [('round1_before','test_round1.py','READ_REVIEW_BEFORE',[]),
    ('round2_before','test_round2.py','READ_ROUND2_BEFORE',[]),('round3_before','test_round3.py','READ_ROUND3_BEFORE',[]),
    ('operator3_before','test_operator_round3.py','READ_ROUND3_BEFORE',[]),('lock3_before','test_lock_round3.py','READ_LOCK_BEFORE',[]),
    ('round4_before','test_round4.py','READ_ROUND4_BEFORE',[]),('round5_before','test_round5.py','READ_ROUND5_BEFORE',[]),
    ('round6_before','test_round6.py','READ_ROUND6_BEFORE',[]),
    ('node4_before','test_round4.py','READ_NODE4_BEFORE',['Round4Tests.test_f2_step600_real_job_and_rehearsal_memory']),
    ('f16_behavior_before','test_round3.py','READ_F16_BEFORE',['Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect'])]:
    report+=block(var+'=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/'+script+(' '+shlex.join(args) if args else ''),name+'.txt')
report+='The final seal is verified by `bash work/cpu.sh work/integrity6.py`; its exact output is [integrity6.txt](checks/integrity6.txt). [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins the documents, MANIFEST, diffs, kit, operations and evidence. The seal output stays external to avoid a report/hash cycle.\n'
(O/'REPORT.md').write_text(report)
note=(O/'NOTE_FOR_CONT_OPS.md').read_text().replace('The round-6 adoption fixes pass targeted CPU tests;',
    f'The round-6 adoption fixes pass {workspace} workspace and {applied} fresh-application CPU tests;')
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
with (L/'work/STATUS.md').open('a') as f:f.write(stamp+f'\nAll {workspace} workspace tests and {applied} applied tests pass; all baseline controls reran. Five patches and MANIFEST regenerated; real CPU evidence feeds bound asset and submit checks. Report and NOTE include exact outputs and unrun GPU requirements. Final integrity seal pending.\n')
print('Report written:',workspace,'workspace tests;',applied,'fresh-application tests;',len(report.encode()),'report bytes.')
print('Workspace sample:',size,'bytes; report time:',stamp)
