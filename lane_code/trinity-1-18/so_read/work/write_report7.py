"""Write the delivered contract, measurements and literal verification outputs."""
import json,re,shlex,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
m=json.loads((O/'patches/MANIFEST.json').read_text());r=json.loads((C/'RESULTS.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text());storage=json.loads((C/'STORAGE7.json').read_text())
old=(L/'out_round7/REPORT.md').read_text();readme=(O/'kit_parity50/README.md').read_text()
count=lambda rows:sum(int(re.search(r'Ran (\d+) tests?',(C/x['output']).read_text()).group(1)) for x in rows)
workspace=count(r['results']);applied=count(m['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip();size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
review=readme.split('## Review round 7: finding -> fix -> test',1)[1]
equality=old[old.index('## Equality and mutation limits'):old.index('## Measured profile and forecast')]
profile=old[old.index('## Measured profile and forecast'):old.index('## Measured CPU guard overhead')].replace('This is not a step-600 measurement.','This does not measure the selected export.')
patches='\n'.join('| ['+name+'](patches/'+name+') | '+str(pin['bytes'])+' | `'+pin['sha256']+'` |' for name,pin in m['patches'].items())
bench='\n'.join('| '+str(v['parameter_count'])+' | '+str(v['parameter_tensors'])+'/'+str(v['buffer_tensors'])+' | '+str(v['weight_and_buffer_bytes'])+' | '+f"{v['before_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_per_call']['median_seconds']*1000:.3f}"+' | '+f"{v['after_install_seconds']:.3f}"+' | '+f"{v['boundary']['median_seconds']:.3f}"+' |' for v in cost['cases'])
report=f'''VERDICT: DONE All requested round-7 fixes pass CPU verification; production adoption still requires the selected-export H100 byte-parity gate.

**Measured validation:** {workspace} workspace tests and {applied} fresh-application tests pass. The eight round-7 tests produce ten expected assertion failures on the reviewed implementation and pass on the delivered implementation. All eleven retained before-fix controls reran. Five diffs apply with zero fuzz. All original reader files and original/OFF output bytes remain unchanged; ON CPU fixtures retain exact answers and traces. GPU byte equality remains unmeasured and mandatory.

**Default export, read from supplied pins:** step **400**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. The gate's `--bound-export` parameter selects a different reviewed export.json. The default compares the complete supplied export identity, including artifact, head, full-weight and preparation pins. The builder accepts positive reviewed steps; the gate requires the selected identity. The synthetic step-600 fixture passes only with an explicit selection.

**Measured resources:** the suite's largest child-process RSS was {r['max_child_rss_bytes']:,} bytes; the separate guard benchmark peaked at {cost['max_rss_bytes']:,} bytes. The workspace measured {size:,} unique-inode bytes at report generation, below 3,000,000,000. The suite recorded {r['workspace_bytes']:,} bytes before completed-fixture sharing. [STORAGE7.json](checks/STORAGE7.json) records {storage['unique_bytes_shared']:,} identical bytes shared across {storage['changed_files']:,} completed pre-task fixture paths; each replacement preserved bytes and path. No workspace-cap violation was observed.

**Estimates:** the supplied A4 timing supports **7,351.824 s for its 636-item schedule**, with zero credited cache saving. The separate **Package D** estimate is **13,813.069 s for 580 distance items**; a19 has **no ON route** for Package D. Neither estimate measures the selected export on a GPU.

Work started at **16:27:18 UTC on 2026-11-19**; the deadline is **17:42:18 UTC**. This report was generated at {stamp}. [out_round7](../out_round7/) preserves the entire reviewed delivery. CPU tests used torch {r['torch']}, transformers {r['transformers']}, eight torch threads, CUDA hidden and `nice -n 10` (the benchmark observed effective nice {cost['nice']}). No Git, SSH, scheduler action, GPU execution, paid API, input-tree edit or deletion command ran. Network access read only official PyTorch documentation.

## Review round 7: finding -> fix -> test
{review}

## Staging and adoption contract

The selected implementation archives assets **inside the existing CPU-proof job**. This uses its already-prepared files and READY receipt, so a separate staging job cannot diverge from the CPU proof. When `read_extensions is True`, `a/5.py` opens the named shared staging path **`$P/a/4.tar`** with exclusive creation outside bwrap and runs `tar -chf - -C logical/d .` through **`J.namespace(root)`**, streaming to that descriptor. Tar dereferences symlinks. The helper flushes/fsyncs the file, hashes it in 1 MiB chunks, and records its path, logical root, SHA256 and byte count in CPU.json. CPU.json is written only after tar succeeds. OFF does not call the helper or create an archive.

The archive lives in the package's shared staging area, outside the 75 MB return pool. Reserve capacity before the CPU job. A failed staging attempt leaves an incomplete archive and no successful CPU.json; a new attempt needs inspection and a fresh package token. The CPU job also copies exact a/1.json into the evidence directory. The gate verifies that file against CPU.json.inputs and verifies EXPORT_PIN.json against its export_pin.sha256 and bytes before GPU work.

**Measured fixture staging:** the real A4 CPU helper emitted a **20,480-byte fixture archive** before CPU.json. The integration check made the original fixture data path unavailable, extracted the archive, and recovered READY-identical assets. Its model/storage/namespace inputs are synthetic; 20,480 bytes is not a production-size estimate. No real large archive was created here.

On the H100 host, **`/scratch/jjyeung` must physically exist and be writable outside bwrap**. The package's exact logical root must be absent before extraction; currently it is `/scratch/jjyeung/b01ec87a6f29b`. A4's namespace-only `/scratch` creation cannot satisfy this host requirement. The [README](kit_parity50/README.md) supplies the owner-only `salloc ... srun` command for one GPU, eight CPUs, 200G, five hours, general/no-requeue, plus CPU-bound archive verification and extraction. Preserve the allocation's actual CUDA_VISIBLE_DEVICES. Device checks require exactly **NVIDIA H100 80GB HBM3**, **132 SMs**, capability **9.0**, and **79–86 billion bytes** of device memory. PCIe, wrong-SM, NVL, MIG and other device types refuse.

Follow the README for patch application, `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`, matching EXPORT_BINDING/BOUND_EXPORT selection, generated operations, placement, detached fill, CPU proof, GPU gate, receipt handoff, submit and unpack. The delivered `operations/binding.default.json` derives its identity from the supplied export pin, its archive byte count from the four a/1.json part sizes, and its operation paths/base identity/frame layout from the reviewed bind400_partial.json. [DEFAULT_EXPORT_PROVENANCE.json](operations/DEFAULT_EXPORT_PROVENANCE.json) pins all four supplied files and the template. This is metadata verification, not a new restore of step-400 weights.

The fill wait requires PACKAGE_TOKEN, checks the PID from 0.txt on the launch host when 1.txt is absent, and has a **14,400-second maximum**. It polls at most once per minute and shortens its final sleep to the remaining deadline. A missing PID, exited worker without a receipt, timeout or nonzero exit receipt fails; it never retries a killed attempt.

The package embeds driver/comparator SHA256 values and the deterministically sealed sample SHA256 derived from MANIFEST kit_files. The driver, workers and receipt writer check their actual bytes. The token-only ue.json carries those hashes, and SUBMIT_CHECK compares them with the immutable package's MANIFEST-derived pins. The public-kit integration changes each staged file in turn and confirms refusal. It also confirms that a failed synthetic receipt cannot authorize submit. Receipt serialization in CPU tests is explicitly synthetic and does not certify a GPU run.

Submit retains cont_ops' CPU assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality. It also requires the cache allowance, both dry checks, an empty general queue, the bounded return pool, and a successful gate for the same plan/profile/assets/device/kit. The original loader still verifies all pinned checkpoint components before model loading. Every gate worker rechecks staged receipt bytes and the manifest hash.

A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**, and complete=false remains partial. The command uses **-s -E -B** from the operator directory: sibling imports work while PYTHONPATH/PYTHONHOME are ignored. GPU receipt transport uses an explicit H100-host archive path.

{equality}
{profile}
## Measured CPU guard overhead

Each stub uses bf16 parameters shaped 2048×1024 and a 1024-element buffer per module. Its forward returns a 32-element tensor without model-sized matrix work. Each implementation runs one miss and a warm hit, then seven timed hits; boundary cost is the median of three hashes. These measurements compare per-call full hashing with the delivered boundary/live-metadata guard on CPU. They do not measure GPU speedup. Exact samples are in [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hashing ms/call | Delivered guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{bench}

## Framework evidence

[FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) cites the installed torch/transformers source for every retained framework assumption. The device guard uses [torch/cuda/__init__.py:673](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/cuda/__init__.py:673), which initializes CUDA, validates the index and returns native properties. [torch/_C/__init__.pyi:12448](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_C/__init__.pyi:12448) declares name, capability, SM count and memory; multi_processor_count appears at line 12452. The official [PyTorch 2.11 device-properties documentation](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html) was reread on 2026-11-19. [SOURCE_EVIDENCE7.json](checks/SOURCE_EVIDENCE7.json) pins the installed files and cont_ops assertion source. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun mutation-counter probes. Device tests use stubs; no local CUDA query ran.

## Patches and authentication

The A4 base is `{m['base_pin']['sha256']}` over **{m['base_pin']['files']} files**. The reviewed A4 payload is `{m['a4_payload_pin']['sha256']}` ({m['a4_payload_pin']['bytes']} bytes). B5 base archive: `{m['b5_base_archive_sha256']}`. B5 checks establish patch applicability; the GPU kit authenticates A4.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patches}

Reader patches add **37 files** under u0/, including regression tests; all original reader bytes remain unchanged. Operator patches remain behind read_extensions. Fresh applied OFF/round-4/5/6/7/comparator suites pass. MANIFEST pins the complete original inventories, additional copied A4 members, base batch/decoded bootstrap, patched operators, extensions, kit, default-export provenance and operation files. The 85 original files in the development source copy and all 927 originals in the fresh applied tree match their input hashes.

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Archive staging fails, storage fills or a namespace disappears too early | checked_run fails before CPU.json; preserve the failed attempt for inspection and use a fresh token. |
| H100 host lacks the logical directory's writable parent | Explicit host checks fail before extraction; provision the path before gate work. |
| Fill dies without an exit receipt or PID is reused | PID check catches the missing worker; the four-hour deadline bounds even a reused PID. |
| Wrong export or changed filled pin | Exact CPU input/READY checks and selected-export identity refuse before GPU execution; runtime component hashes check actual weights. |
| Stale or changed driver/comparator/sample | Runtime hashes and submit's package-bound expected hashes refuse. |
| Different H100 variant | Exact name, 132 SMs, capability and memory checks refuse before model loading. |
| Changed input/operator/batch or incomplete CPU proof | Builder pins and the full cont_ops submit assertion block refuse. |
| GPU kernels or eager SAM alter answer/trace bytes | Zero-difference gate fails; equal aggregate scores cannot waive it. |
| Cache cost erases savings or whole-process memory exceeds the cache cap | Compare full worker wall time and actual host/GPU peaks; the cache cap excludes model/caller working memory. |
| A raw write is restored between boundaries | Frozen ownership remains required; this sequence is outside the guard. |
| A refused/partial return is scored | Require unpack success output and inspect complete status. |

## Not done

No production GPU parity, throughput, peak-memory measurement, scheduler allocation, large pull/staging archive, real bwrap isolation/restore, transport, upload, submit, return publication or persistent-storage requeue ran. No numeric tolerance, batching or multi-card A4 operator is delivered. The array prototype remains approved=false. CPU suites need no local OS sockets. The H100 host path and production interpreter/storage capacity are owner-side preconditions, not verified here.

## Review round 6: finding -> fix -> test

The documented unpack subprocess runs; detached fill retains its lock/PID/log/exit status; submit embeds every cont_ops CPU assertion; copied A4 members, batch and bootstrap are pinned; CPU receipts bind checkpoint assets. The round-6 suite passes and its reviewed-snapshot control still produces 31 expected assertion failures. The round-7 gate uses the selected export parameter and exact SXM admission described above.

## Review round 5: finding -> fix -> test

The built batch equals cont_ops wrap_batch and passes the real bundle guard. Builder tests refuse changed payload/operators/extensions before output. Operation, profile, pool, forecast and unpack-success tests pass. The reviewed-snapshot control reproduces eleven expected failures.

## Review round 4: finding -> fix -> test

The A4 builder retains run keys, binding, fill admission and compatible helpers. The real CPU fixture executes preparation, rehearsal, bootstrap, job/action dispatch and all 636 stub reads in five verified ordinary journals. Return tests reject invalid weight receipts and retain OFF behavior. Its explicit alternate-export fixture uses step 600; this is not the default decision export. Both the reviewed route and original CPU-helper controls reproduce their expected failures.

### Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage pass their regressions; all eight baseline regressions fail as expected.

### Review round 2: finding -> fix -> test

Isolated entry, path policy, bounded array attempts, pinned overlays, SAM capacity, deadline counts, lock waits, accounting, source-root checks and worker setup pass. The baseline reproduces thirteen assertions plus the expected CLI import error.

### Review round 3: finding -> fix -> test

Install/type-boundary hashes and cheap fatal live guards, processor-only mode, operator memory/overlay dispatch, full-base authentication, lock/worker behavior and OFF import checks pass. The generic operator test checks its nested atomic merge; the A4 adoption fixture checks the cache-only single-card profile. All baseline controls reproduce.

These named review sections are retained because the binding prompts explicitly request them. Test-output names containing step600 identify synthetic alternate-export fixtures, not an operational default.

## Commands and exact outputs

Commands ran from `{L}`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then executes the approved Python with `nice -n 10 -I -s -B`. Child processes inherit those limits. The documented unpack command intentionally uses -s -E -B for its sibling import. Fixture storage shares immutable bytes and detaches shared files before edits.

Test commands additionally set READ_INPUT_SRC={m['base']} and READ_TEST_TMP={L/'work/test-artifacts'}. Applied suites also set READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE under `{m['verification_root']}/operator`. All outputs below are literal; before-fix failures are expected controls. No cluster kill or automatic relaunch occurred.

'''
def block(command,name):
    return '```bash\n'+command+'\n```\n\nExact output:\n\n```text\n'+(C/name).read_text().rstrip()+'\n```\n\n'
for command,name in [('bash work/cpu.sh work/run_checks.py','run_checks7.txt'),
    ('bash work/cpu.sh work/run_fixture5.py work/build_patches.py','build_patches7.txt'),
    ('bash work/cpu.sh work/gate_integration7.py','gate_integration7.txt'),
    ('bash work/cpu.sh work/profile.py','profile_rerun.txt'),('bash work/cpu.sh work/torch_versions3.py','torch_versions3.txt'),
    ('bash work/cpu.sh work/benchmark_round3.py','cache_cost3.txt'),('bash work/cpu.sh work/docs_check7.py','docs7.txt'),
    ('bash work/cpu.sh work/share_storage7.py','storage7.txt')]:report+=block(command,name)
report+='The patch-application subprocess output from build_patches.py is retained verbatim:\n\n```text\n'+(C/'patch_application.txt').read_text().rstrip()+'\n```\n\n'
for row in [*r['results'],*m['applied_cpu_suites']]:report+=block(shlex.join(row['command']),row['output'])
for name,script,var,args in [('round1_before','test_round1.py','READ_REVIEW_BEFORE',[]),
    ('round2_before','test_round2.py','READ_ROUND2_BEFORE',[]),('round3_before','test_round3.py','READ_ROUND3_BEFORE',[]),
    ('operator3_before','test_operator_round3.py','READ_ROUND3_BEFORE',[]),('lock3_before','test_lock_round3.py','READ_LOCK_BEFORE',[]),
    ('round4_before','test_round4.py','READ_ROUND4_BEFORE',[]),('round5_before','test_round5.py','READ_ROUND5_BEFORE',[]),
    ('round6_before','test_round6.py','READ_ROUND6_BEFORE',[]),('round7_before','test_round7.py','READ_ROUND7_BEFORE',[]),
    ('node4_before','test_round4.py','READ_NODE4_BEFORE',['Round4Tests.test_f2_step600_real_job_and_rehearsal_memory']),
    ('f16_behavior_before','test_round3.py','READ_F16_BEFORE',['Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect'])]:
    report+=block(var+'=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/'+script+(' '+shlex.join(args) if args else ''),name+'.txt')
report+='The final seal runs `bash work/cpu.sh work/integrity7.py`; its exact output is [integrity7.txt](checks/integrity7.txt). [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins the report, note, MANIFEST, diffs and evidence. Seal output stays external to avoid a report/hash cycle.\n'
(O/'REPORT.md').write_text(report)
note=(O/'NOTE_FOR_CONT_OPS.md').read_text();first=note.splitlines()[0]
note=note.replace(first,f'VERDICT: DONE All round-7 fixes pass {workspace} workspace and {applied} fresh-application CPU tests; production H100 byte parity remains required.',1)
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
with (L/'work/STATUS.md').open('a') as f:f.write(stamp+f'\nAll {workspace} workspace and {applied} applied tests pass. Archive reconstruction, public-kit tamper checks and full gate/submit integration pass with synthetic GPU controls. Source probes/profile/benchmark/documentation reran. REPORT and NOTE rewritten; final integrity seal pending.\n')
print('Report written:',workspace,'workspace tests;',applied,'fresh-application tests;',len(report.encode()),'bytes.')
print('Measured workspace bytes before report:',size,'UTC:',stamp)
