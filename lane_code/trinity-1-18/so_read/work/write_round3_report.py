"""Publish the current contracts, measured evidence and exact validation outputs."""
import hashlib,importlib.util,json,re,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
manifest=json.loads((O/'patches/MANIFEST.json').read_text())
assert len(manifest['patches'])==4
results=json.loads((C/'RESULTS.json').read_text());cost=json.loads((C/'CACHE_COST3.json').read_text())
def count(paths):
 return sum(int(re.search(r'Ran (\d+) tests?',(C/p).read_text()).group(1)) for p in paths)
workspace=count([r['output'] for r in results['results']]);applied=count([r['output'] for r in manifest['applied_cpu_suites']])
assert all(r['returncode']==0 for r in results['results'])
assert workspace==91 and applied==88,(workspace,applied)
assert 'PASS: all 10 CPU suites pass' in (C/'build_patches3.txt').read_text()
stamp=subprocess.check_output(['date','-u'],text=True).strip()
profile=(O/'profile.json').read_text();old=(L/'out_round3/REPORT.md').read_text()
profile_section=old[old.index('## Measured profile and forecast'):old.index('## Equality, memory and deployment contracts')]
patch_table='\n'.join(f"| [{name}](patches/{name}) | {spec['bytes']} | `{spec['sha256']}` |" for name,spec in manifest['patches'].items())
cost_table='\n'.join(f"| {r['parameter_count']:,} | {r['parameter_tensors']} / {r['buffer_tensors']} | {r['weight_and_buffer_bytes']:,} | {r['before_per_call']['median_seconds']*1000:.3f} | {r['after_per_call']['median_seconds']*1000:.3f} | {r['after_install_seconds']:.3f} | {r['boundary']['median_seconds']:.3f} |" for r in cost['cases'])
review='''## Review round 3: finding -> fix -> test

| Finding | Fix or disposition | Fail-before / pass-after evidence |
|---|---|---|
| 1 MEDIUM: per-call weight hashing | Hash each module at cache install and at type-journal entry/exit. Check every parameter/buffer id, data_ptr, version, dtype/device/shape/stride and gradient flag per call. Preserve option/execution/input keys. Mutations fail the run through a latched BaseException; they do not become cache misses. Add processor-only settings/build switches. | test_round3.py rejects per-call weight reads, replacement, in-place updates, .data reassignment, persistent .data/NumPy writes, and counterless inference tensors. It verifies boundary failure, resume/merge rejection, and graceful-deadline/public-merge success. The fixed 50-item stub fixture also exercises processor-only and exact bytes. CPU overhead is measured below. |
| 2 MEDIUM: A4 operator path and memory | Build an a12 ON payload and dispatch A4's decoded 0.py/7.py. The patched 7.py activates overlays in its fresh action-1 process. The operator adds read_cache_bytes to its host bound only with read_extensions enabled. Optional builder arguments package the authenticated A4 bootstrap/sequence. | test_operator_round3.py runs real bootstrap admission (including rejection of a failed CPU proof) and action-0 settings/artifact construction with heavy restore/export-admission scans stubbed, then real operator/runner/action-2 dispatch with stub model workers for all 636 items. It checks pins, overlays, memory receipt and the archive under metadata/reads/0/metadata/u0. Both operator regressions fail before and pass after; the baseline specifically fails “Operator overlay not active”. |
| 3 LOW: unauthenticated base | Authenticate both non-u0 inventories against MANIFEST base_pin before any arm; the staged u4.json carries the same pin. | Both equally wrong bases, changed bytes and extra files fail. The fresh-application check authenticates all 927 original and patched base files, not only a small fixture. |
| 4 LOW: weak regressions | Run the identical behavioral lock test against round-1-before a4. Add a type-deadline test that attempts a second flock during recovery. Replace F16's evidentiary dependence on a string check with an actual worker-setup test. | lock3_before.txt records two failures: missing recovery and BlockingIOError not raised after lock release. lock3.txt passes both. The actual kit worker mutates the settings environment on the F16 baseline and fails; delivered worker setup passes. |
| 7 INFO: OFF import guard | Extend the one-line range from a0–a10 to a0–a18. | All eight omitted modules fail the guard regression before and are rejected after. The full original/OFF byte-and-source-hash fixture still passes. |

All requested findings have a fix and regression evidence. Finding 2 uses the dispatch's permitted single-card alternative: no multi-card operator variant is delivered. A standalone variant preserving preparation, fixed descriptors, card-bound identities, scheduling and memory-proof handling is estimated to exceed about 80 lines; no validated smaller implementation is claimed. Sharded reads need that operator. Step 600 remains single-card ON with caches only.

INFO 5 is handled operationally: source trees travel as archives, extract node-locally, and the kit requires --public. The README states these rules. INFO 6 remains unvalidated because the array path has no production staging/requeue exercise or owner approval; its example stays approved=false. INFO 8's existing checks are rerun; INFO 9's integrity receipt is regenerated. No scheduler, upload or deployment ran.
'''
report=f'''VERDICT: DONE The requested round-3 fixes pass CPU verification; GPU adoption remains gated.

Measured validation: **{workspace} workspace tests and {applied} fresh-application tests pass**. All prior report suites were rerun, including the eight round-1 and thirteen round-2 failing baselines. The requested round-3 failures reproduce on their reviewed implementations. Three additive reader patches and one default-OFF A4 operator patch apply with zero fuzz. Reader source files and complete ordinary OFF outputs remain byte-identical to the inputs.

Measured CPU cache-hit overhead falls from **{cost['cases'][0]['before_per_call']['median_seconds']*1000:.1f} to {cost['cases'][0]['after_per_call']['median_seconds']*1000:.1f} ms** for a 268,435,456-parameter stub, and from **{cost['cases'][1]['before_per_call']['median_seconds']*1000:.1f} to {cost['cases'][1]['after_per_call']['median_seconds']*1000:.1f} ms** for a 536,870,912-parameter stub. These measure validation/cache overhead on CPU, not GPU inference speedup. Credit no production saving until the complete GPU gate passes.

Measured resources: torch {results['torch']}, transformers {results['transformers']}, eight torch threads, CUDA hidden. Peak child RSS in the suite driver was {results['max_child_rss_bytes']:,} bytes; the model-sized benchmark peaked at {cost['max_rss_bytes']:,} bytes. Workspace size at the suite check was {results['workspace_bytes']:,} bytes, below 3 GB. Commands use nice -n 10; the benchmark recorded effective niceness {cost['nice']}. No Git, SSH, scheduler, GPU, paid API or input-tree modification ran. Network access read official library documentation only.

The backup is [out_round3](../out_round3/). Work started at Thu Nov 19 12:04:06 UTC 2026; the two-hour deadline is 14:04:06 UTC. Report generated at {stamp}.

{review}
## Measured cache cost and mutation contract

Each stub has bf16 parameters of shape 2048×1024 and one 1024-element bf16 buffer per parameter tensor. The stubs have 128 or 256 child modules. Their forward returns a 32-element tensor and performs no model-sized matrix work. Both implementations run a miss and a warm hit, then seven timed hits. The boundary statistic is the median of three hashes. The same frozen-state guards protect vision and SAM; the benchmark invokes the vision wrapper to isolate their shared validation cost.

| Parameters | Parameter / buffer tensors | Weight+buffer bytes | Before ms/call | After ms/call | After install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{cost_table}

Exact samples, environment and peak RSS: [CACHE_COST3.json](checks/CACHE_COST3.json). The full weight hash still costs time at install and boundaries; GPU transfer/synchronization costs are unmeasured. No forecast below credits these CPU ratios.

The torch counter tracks in-place data/size changes, not arbitrary storage writes: [TensorImpl.h:291](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:291). Views/detach share it; .data does not: [TensorImpl.h:303](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:303). Data reassignment preserves the destination counter: [TensorImpl.h:2051](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:2051). The pointer guard catches reassignment to new storage. The installed SGD step calls an in-place parameter update at [sgd.py:379](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/optim/sgd.py:379); the measured foreach=False test increments the counter.

Persistent .data mutations, NumPy writes and custom pointer writes may leave the tuple unchanged. Full boundary hashes guard those persistent changes. The official [increment_version documentation](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html) and installed [graph.py:242](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/autograd/graph.py:242) explain untracked writes. Counterless inference tensors are refused, consistent with [TensorImpl.h:413](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:413) and the official [inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html). [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) records actual ids, pointers, counters and source-file SHA256s. Other framework evidence is in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md).

Models must remain frozen. A raw write followed by restoration before the next boundary can evade detection; this is outside the supported ownership contract. The guards do not claim otherwise. A mismatch raises a fatal, latched exception and leaves WEIGHTS.json unverified. Resume, merge and the comparator refuse such journals. Graceful deadlines verify weights before lock-held recovery and can resume; hard termination before validation requires a fresh journal. Processor-only runs install no weight guard and retain the ordinary journal-resume contract.

{profile_section}
## Equality, memory and adoption

The ordinary entrypoint imports no extension and reads no new settings. The OFF fixture compares all generated files and stdout, including source hashes and controlled timing fields, with no field exclusions. [OFF_BYTES.json](checks/OFF_BYTES.json) records its proof. The three reader diffs only add u0 files. The operator diff leaves its OFF memory receipt equal to the original; its activation flag defaults OFF.

The 50-item CPU fixture compares ORIGINAL/OFF/processor+vision ON/processor-only answers and traces exactly with stub generation. Separate SAM fixtures verify cached values, geometry recomputation and mutation rejection. This does not establish production GPU equality. The unrun kit requires independent authenticated roots, ORIGINAL/OFF/OFF_REPEAT/ON plus journal/shard runs, all requested switches ON, useful hits in each enabled cache, memory receipts and zero semantic byte differences. Only clocks and explicit telemetry are excluded. No answer/trace tolerance is allowed. Batched generation is not delivered because changed padding/kernel shapes have no bit-equality guarantee.

The cache cap is 12 GiB when SAM is enabled and 4 GiB otherwise, unless read_cache_bytes explicitly overrides it. The operator ON proof adds that cache cap to the existing G3T/runtime allowance. This is a configured bound, not a measurement of full process memory. [MEMORY.json](checks/MEMORY.json) contains the measured small allocation fixture; the 3 GiB capacity regression simulates accounting without allocating that tensor. Actual H100 host/GPU headroom remains unmeasured.

**Step-600 candidate: single-card ON with caches only.** Build with --enable-extensions --caches-only and the A4 operator inputs described in the [README](kit_parity50/README.md). Add --processor-only to enable just the processor cache; direct settings can use read_processor_only="on", which overrides both model-cache switches. The builder's processor-only profile also turns atomic journals and scene sharding OFF. Generic ON still enables those features for their separate validation gates.

The delivered A4 operator keeps its fixed 636-item descriptors; the owner must bind the target read's descriptors/counts and regenerate the payload, operator and CPU-proof pins for a different item set. No multi-card operator is included. The two/four-shard forecasts require one and are not step-600 launch plans. Real preemption/requeue also remains a separate gate.

The operator test validates the canonical archive at **metadata/reads/0/metadata/u0/answer_trace_return.tgz** when atomic journals are enabled. The unchanged transport includes that nested subtree, and the existing unpacker still binds operator_sha256. Cache-only adoption keeps the ordinary type journals and requests no canonical merge. Full transport/envelope capacity remains a deployment check.

## Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen model identity, lock-held recovery, token transport and bounded cache storage all retain passing regressions. The eight original failing baseline tests reproduce. Model changes now fail a guarded run; persistent raw writes are checked at boundaries under the explicit round-3 contract.

## Review round 2: finding -> fix -> test

Isolated entry, approved paths, array policy/retry, production packaging/pins, SAM capacity, deadline counts, bounded lock waits, processor bypass counts, root checks and worker settings selection all retain passing regressions. All thirteen reviewed-baseline tests fail as expected. The per-call hashing and operator-path findings are covered by the round-3 tests above.

## Patches and base pins

Apply 01–03 in numeric order from a fresh full src tree using patch --batch --fuzz=0 -p1. Apply 04 from a separate A4 operator directory containing tower_sequence.py. Do not apply 04 from src. Tests are included in patch 03 and run against the patched operator through READ_OPERATOR_SOURCE. [MANIFEST.json](patches/MANIFEST.json) pins files, diffs, kit, operator, bases and application receipts.

A4 base SHA256: `{manifest['base_pin']['sha256']}` over {manifest['base_pin']['files']} non-bytecode files. B5 input archive SHA256: `{manifest['b5_base_archive_sha256']}`. Operator base SHA256: `{manifest['operator_base_pin']['sha256']}`. The delivered operator/0.py is byte-identical to the bootstrap decoded from the pinned A4 BATCH.sh.

| Patch | Bytes | SHA256 |
|---|---:|---|
{patch_table}

## What could go wrong and how to notice

| Risk | Detection/action |
|---|---|
| Boundary hashes, copies or cache misses erase savings | Require useful hits and a net complete-run time reduction on the GPU sample; retain the no-saving forecast until then. |
| GPU preprocessing/storage layouts/kernels change an answer | Require all-arm byte equality, not equal scores. The CPU environment lacks production torchvision/CUDA/FLA coverage. |
| Model storage mutates | Tracked changes fail on the next call; persistent raw changes fail at boundaries. Refuse unverified journals. Keep all model mutation outside guarded reads. |
| Host/GPU memory exceeds the operator allowance | Measure full-process peaks; cache caps exclude model/caller working storage. The CPU proof alone is insufficient. |
| Wrong base, payload, operator or item schedule | Kit inventories, payload/plan hashes, operator_sha256 and regenerated CPU proof must match before decode. |
| A hard kill leaves an unchecked journal, or remote locks/requeue differ | Refuse unchecked weighted journals. Verify real persistent-storage restart before preempt/sharded adoption. |
| Return capacity or public-content rules fail | Check the full production envelope, source archives, token-only staging and mandatory --public before launch. |

## Not done

No GPU parity/performance/memory run, real weight restore, bwrap isolation, scheduler action, persistent-storage requeue, remote return publication or array approval ran. No multi-card operator or batching implementation is delivered. The array helper remains an inert, separately gated prototype. These limitations do not waive the zero-tolerance acceptance gate.

No delivered CPU suite or single-GPU kit pass requires a local OS socket. StageOneSocket is a Python callback. Socket-backed distributed/transport integration remains unrun.

The named review sections retain finding history only because the dispatch explicitly requires that audit trail. Other sections state the delivered behavior and current evidence.

## Commands and exact outputs

All commands run from `{L}`. work/cpu.sh sets CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads to 8, TOKENIZERS_PARALLELISM=false and PYTHONDONTWRITEBYTECODE=1, then invokes nice -n 10 and the required Python -I -s -B. Tests call torch.set_num_threads(8). work/round3_env.sh also sets the read-only input and local fixture roots.
'''
def exact(command,path):
 return '\n```bash\n'+command+'\n```\n\nExact output:\n\n```text\n'+(C/path).read_text().rstrip()+'\n```\n'
for command,path in [('bash work/cpu.sh work/profile.py','profile_rerun.txt'),
                     ('bash work/cpu.sh work/benchmark_round3.py','cache_cost3.txt'),
                     ('bash work/cpu.sh work/torch_versions3.py','torch_versions3.txt'),
                     ('bash work/cpu.sh work/run_checks.py','run_checks3.txt'),
                     ('bash work/cpu.sh work/build_patches.py','build_patches3.txt')]:report+=exact(command,path)
report+='\n### Workspace suites\n'
for row in results['results']:
 report+=exact('bash work/round3_env.sh '+str(Path(row['command'][-1]).relative_to(L)),row['output'])
report+='\n### Fresh-application suites\n'
for row in manifest['applied_cpu_suites']:
 prefix='READ_OPERATOR_SOURCE='+str(Path(manifest['verification_root'])/'operator/tower_sequence.py')+' '
 report+=exact(prefix+'bash work/round3_env.sh '+row['command'][-1],row['output'])
report+='\n### Reviewed-baseline regressions (expected failures)\n'
for env,script,args,path in [
 ('READ_REVIEW_BEFORE=1','test_round1.py','','round1_before.txt'),
 ('READ_ROUND2_BEFORE=1','test_round2.py','','round2_before.txt'),
 ('READ_ROUND3_BEFORE=1','test_round3.py','','round3_before.txt'),
 ('READ_ROUND3_BEFORE=1','test_operator_round3.py','','operator3_before.txt'),
 ('READ_LOCK_BEFORE=1','test_lock_round3.py','','lock3_before.txt'),
 ('READ_F16_BEFORE=1','test_round3.py',' Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect','f16_behavior_before.txt')]:
 report+=exact(env+' bash work/round3_env.sh work/src/u0/tests/'+script+args,path)
(O/'REPORT.md').write_text(report)
note=f'''VERDICT: DONE The five requested round-3 findings are fixed and CPU-verified; GPU adoption remains gated.

Measured validation: **{workspace} workspace tests and {applied} fresh-application tests pass**. All report suites and failing baselines were rerun. Four patches apply exactly; ordinary OFF bytes remain unchanged. The backup is out_round3/.

Measured CPU validation/cache overhead falls from **{cost['cases'][0]['before_per_call']['median_seconds']*1000:.1f} to {cost['cases'][0]['after_per_call']['median_seconds']*1000:.1f} ms/call** on a 268M-parameter bf16 stub; **{cost['cases'][1]['before_per_call']['median_seconds']*1000:.1f} to {cost['cases'][1]['after_per_call']['median_seconds']*1000:.1f} ms/call** on a 537M-parameter stub. These are not GPU speedups. Weights hash at install/type boundaries; calls check ids, pointers and counters. Persistent raw writes fail at boundaries. Raw writes restored between boundaries remain unsupported.

Measured distance time remains **23.60 s/item**. Estimated 580-item times, with no cache saving credited: **3 h 50 min** on one card; **1 h 56 min / 59 min** for ideal two/four shards. These estimates exclude queues, staging, preemption and scene imbalance.

## Review round 3: finding -> fix -> test

| Finding | Fix and evidence |
|---|---|
| 1. Weight cost | Install/boundary hashes and fatal mutation guards; no per-call weight reads. Processor-only settings/build switches. Mutation, journal/resume/public-merge, 50-item exact-byte and timed stub tests pass. |
| 2. Operator path | Real bootstrap admission/preparation/dispatch and stub workers validate 636 items and the nested return. ON adds read_cache_bytes; OFF memory proof is equal. Both regressions fail before. |
| 3. Base source | Both complete 927-file inventories authenticate against MANIFEST. Equal wrong bases and altered inventories fail before any arm. |
| 4. Weak tests | Both behavioral deadline/lock tests fail against round-1-before a4 and pass after. Actual worker setup fails on the F16 baseline and passes after. |
| 7. OFF guard | The guard lists a0–a18. All eight omitted modules fail before; OFF byte tests still pass. |

**Step 600 uses single-card ON with caches only**, after the GPU gates. Build with --enable-extensions --caches-only and the delivered A4 operator inputs. Add --processor-only to adopt only the processor cache; it disables both model caches and journal/shard extensions. Sharded reads need a multi-card operator, which is not delivered within the requested approximately 80-line limit. The two/four-shard estimates are conditional, not launch plans.

Apply 01–03 from src and 04 from a separate A4 operator copy. Rebuild payload/operator/CPU-proof pins and bind the target item schedule; the supplied operator retains 636 items. The atomic merge uses metadata/reads/0/metadata/u0; cache-only adoption keeps ordinary journals. The host bound includes the 12 GiB SAM cache allowance; full-process memory remains unmeasured.

Before adoption, run ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates with every switch ON and **zero answer/trace byte differences**, positive hits, net time savings and memory/envelope headroom. Require real persistent-storage requeue before any preempt/sharded adoption. Unverified weight journals fail closed; graceful verified deadlines can resume. Source trees must stage as archives and the kit must use --public. Array approval stays false; no launch ran. Preserve step-400 deliveries.

Exact commands, outputs, source citations and limits: [REPORT.md](REPORT.md). Build and gate commands: [README.md](kit_parity50/README.md). Patch/base pins: [MANIFEST.json](patches/MANIFEST.json).
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
with (L/'work/STATUS.md').open('a') as f:f.write(stamp+'\nRound 3 report and handover rewritten with exact outputs, measured CPU costs, source citations, patch/base pins and explicit unrun GPU/multi-card gates.\n')
print(f'PASS: REPORT and NOTE state {workspace} workspace / {applied} applied tests and all five requested findings; exact outputs embedded.')
