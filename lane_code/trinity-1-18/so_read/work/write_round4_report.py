"""Write the current delivery contract and include exact CPU command output."""
import json,re,shlex,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out';C=O/'checks'
results=json.loads((C/'RESULTS.json').read_text());manifest=json.loads((O/'patches/MANIFEST.json').read_text())
cost=json.loads((C/'CACHE_COST3.json').read_text())
count=lambda entries:sum(int(re.search(r'Ran (\d+) tests?',(C/e['output']).read_text()).group(1)) for e in entries)
workspace=count(results['results']);applied=count(manifest['applied_cpu_suites'])
stamp=subprocess.check_output(['date','-u'],text=True).strip()
size=int(subprocess.check_output(['du','-sb',str(L)],text=True).split()[0])
base=manifest['base_pin']['sha256']
old=(L/'out_round4/REPORT.md').read_text()
profile=old[old.index('## Measured profile and forecast'):old.index('## Equality, memory and adoption')]
benchmark='\n'.join('| '+str(c['parameter_count'])+' | '+str(c['parameter_tensors'])+' / '+str(c['buffer_tensors'])+' | '+str(c['weight_and_buffer_bytes'])+' | '+f"{1000*c['before_per_call']['median_seconds']:.3f}"+' | '+f"{1000*c['after_per_call']['median_seconds']:.3f}"+' | '+f"{c['after_install_seconds']:.3f}"+' | '+f"{c['boundary']['median_seconds']:.3f}"+' |' for c in cost['cases'])
report=f'''VERDICT: DONE The round-4 packaging, adoption-profile and return-validation fixes pass CPU checks; GPU adoption remains gated.

Measured validation: **{workspace} workspace tests pass**, including every prior suite. All requested fail-before regressions reproduce. **{applied} tests pass from a fresh patch application**: the OFF, round-4 integration and comparator suites. Every applied file matches the tested workspace bytes; every original reader file remains unchanged. Five patches apply with zero fuzz.

The A4 build preserves its reviewed run keys, Python-3.6-compatible submit helper and export-admission code. It requires a target export binding, including the whole-archive size/hash. Its CPU fixture builds a synthetic step-600 cache-only package, runs A4's real CPU-proof helper, bootstrap and job.main, completes 636 stub items, and verifies five ordinary weight journals. No real step-600 export was supplied or claimed.

Measured environment: torch {results['torch']}, transformers {results['transformers']}, {results['torch_threads']} torch threads, CUDA hidden. The suite driver's maximum child RSS was {results['max_child_rss_bytes']:,} bytes. The CPU benchmark's peak RSS was {cost['max_rss_bytes']:,} bytes. The workspace occupies {size:,} bytes including directory metadata, below 3,000,000,000 bytes. All compute used nice -n 10 and the required thread/environment limits. No Git, SSH, scheduler, GPU, paid API, deletion or input-tree edit ran. Network access read official library documentation only.

The untouched delivery backup is [out_round4](../out_round4/). Work began at Thu Nov 19 13:02:02 UTC 2026; the deadline is 14:32:02 UTC. This report was generated at {stamp}.

## Review round 4: finding -> fix -> test

| Finding | Fix | Evidence |
|---|---|---|
| 1 MEDIUM: step-600 build drops A4 run keys, export binding and compatible helper | The explicit a19 builder uses cont_ops' build_r1-style post-processing over A4's authenticated payload. It retains 8.py, admission/vendor bytes and every A4 run key, installs the ON overlays, and seals the reviewed target binding into 9.json. It retargets A4's fill-helper object/size/hash constants and rebuilds every affected pin. The incomplete a12 operator route is refused. | test_f1 checks target binding, payload pins, A4 keys and helper bytes/compatibility. The real admission rejects changed run, step, member, lineage, object, config, archive or preparation hashes. The fill helper rejects changed whole-tar identity/receipt. The documented reviewed build fails this test on the missing stage1 rule. |
| 2 LOW: hand-built action config and generic profile hide adoption failures | A4's CPU-proof helper propagates read_extensions into the real 7.py rehearsal. The test reads packaged 9.json as-is and runs real job.main to construct a/0.json and a/1.json; it only translates namespace paths and stubs storage/device/model work. | test_f2 runs real preparation, rehearsal, bootstrap admission, operator and runner/action-2 dispatch. MEMORY.json contains 12,884,901,888 cache bytes. All 636 items complete in five ordinary journals, each with verified=true; no atomic commit store or canonical merge exists. The old route fails preparation. Independently, the original CPU-proof helper fails with None != 12884901888. |
| 3 LOW: cache-only return accepts unchecked weights | With read_extensions=true, unpack_return refuses an existing WEIGHTS.json unless verified is exactly JSON true. OFF retains its existing path. | The same test accepts missing/true receipts, refuses false/null/0/1/string values, and retains OFF behavior. All five invalid-value assertions fail on reviewed code. The real authenticated unpack entry accepts a verified partial return and rejects an unverified partial return. |
| 9 INFO: non-delivery paths, B5 base claim, proof-field wording | README uses explicit delivery/source/scratch variables; the kit is A4-only. It distinguishes the generated cache-memory proof from unchanged bootstrap admission. | The CPU integration uses the delivered Python tools and asserts the generated cache allowance. The kit authenticates complete A4 inventories; B5 applicability is limited to the separate patch-application check. |

The requested findings are fixed. The new builder adapts the reviewed packaging logic because build_r1.py itself hard-codes step-200 bindings and output paths outside this writable workspace. It preserves the inspected A4 package instead of rebuilding unported helpers. Binding generation and production staging remain owner operations; the builder cannot manufacture review evidence.

The round-4 before output contains seven assertion failures across the three required regressions: two packaging/profile failures and five weight-state subtests. The one skipped test is the new builder's OFF/processor-only interface, which does not exist in the reviewed baseline. A separate old-node-helper run fails the memory-field assertion. Exact outputs are included below.

## Delivered build and adoption contract

**Step 600 is a single-card, cache-only candidate on general with no requeue, after the GPU gate.** Apply reader patches 01–03 to the full A4/src copy and operator patches 04–05 to an A4 directory copy. Follow the exact preparation/build/fill/proof commands in [README.md](kit_parity50/README.md). The explicit build command is:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

The binding must include run, step, member directory, lineage, object, configuration/base/frame identities, preparation hashes and whole-archive size/hash. Add --processor-only for a 4 GiB processor cache; the full cache profile uses 12 GiB. Both profiles disable atomic journals and scene sharding. The builder copies A4's numeric CPU/fill/fetch helpers, keeps a/ private, invalidates old input/export receipts, and carries no old CPU proof or submission ledger. Its output includes the exact tower_sequence.py that the unpacker hashes.

A4's descriptors still bind 636 items. A different item set requires a separately reviewed schedule and proof. No multi-card A4 operator is delivered. The two/four-shard estimates below require one and are not step-600 launch instructions. Real persistent-storage requeue remains required before any preempt/sharded adoption.

The actual CPU proof comes from a/5.py invoking 7.py with rehearsal and measure_memory. It must bind the new payload, plan, inputs and operator; require both bundle/entry checks and fits=true. Inspect read_cache_bytes: 12,884,901,888 for all caches or 4,294,967,296 for processor-only. The unchanged bootstrap verifies proof binding and fits, but does not independently require that field. The fixed CPU helper emits it and the regression checks it.

Cache-only returns use ordinary per-type journals. The ON unpacker refuses unverified weight receipts even in an authenticated partial return. The separate generic atomic validation path retains its nested archive at metadata/reads/0/metadata/u0/answer_trace_return.tgz.

## Equality and mutation limits

The ordinary reader imports no extension and parses no new settings. The OFF fixture compares complete output files/stdout, including source hashes and controlled timing fields, against the original without exclusions. [OFF_BYTES.json](checks/OFF_BYTES.json) records the byte proof. The operator memory/return additions are guarded by read_extensions, whose default is OFF.

The 50-item CPU fixture compares original/OFF/processor+vision/processor-only answers and traces exactly with stub generation. Separate SAM fixtures check cached values, geometry recomputation and mutation rejection. Production adoption requires the unrun ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates, useful hits in every enabled cache, and **zero answer/trace byte differences**. Only clocks and explicit telemetry are excluded; equal scores cannot hide changed answers. No batching implementation or numeric tolerance is delivered.

Calls check every parameter/buffer identity, pointer and version. Full hashes run at installation and type boundaries. Persistent .data/NumPy/raw-storage writes fail at boundaries; a raw write restored before the next boundary can evade detection. Private tensor attributes and arbitrary non-tensor module state are outside the guard's coverage. Models must remain frozen. A hard worker death can leave WEIGHTS.json false; graceful stops validate it. Processor-only runs install no weight guard.

ON eagerly constructs SAM outside inference mode; OFF constructs it lazily inside inference mode. This changes load timing and potentially RNG use. Only the GPU byte gate can clear the difference. Per-item timing omits installation and boundary costs; judge net performance using RUN.json worker_wall_seconds. The sample overstates reuse: its ten distance items share one clip, while A4 has 150 distance items over 60 clips (review finding 7). No production saving is credited.

## Measured CPU guard overhead

Each stub has bf16 parameters of shape 2048×1024 and one 1024-element bf16 buffer per tensor, with 128 or 256 child modules. Forward returns a 32-element tensor without model-sized matrix work. Each implementation runs a miss and warm hit, then seven timed hits; the boundary figure is the median of three hashes. These are CPU validation/cache costs, not GPU speedups.

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Reviewed per-call hash ms | Boundary-guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
{benchmark}

Exact samples and environment: [CACHE_COST3.json](checks/CACHE_COST3.json). The filename retains its test lineage; this task reran the benchmark. Actual H100 hash/copy/synchronization costs and full-process host/GPU memory remain unmeasured.

{profile}
## Framework evidence

The implementation's framework contract and installed file:line citations are in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md). This task reread TensorImpl.h:291–305, 413–418 and 2050–2054, autograd/graph.py:242–258 and optim/sgd.py:378–380 under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/`. Tracked in-place operations increment counters; detach shares them; .data/storage replacement need not share/increment them. The pointer guard catches new storage; boundary hashes cover persistent untracked writes. Inference tensors lack counters and are refused for model caching.

The official [increment_version documentation](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html) and [inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html) were checked on 2026-11-19. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun operation probes and installed-source hashes. No new framework assumption was needed for the packaging/return fixes.

## Earlier required review sections

### Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage retain passing tests. All eight reviewed-baseline regressions fail as expected.

### Review round 2: finding -> fix -> test

Isolated entry, path policy, bounded array retries, pinned overlays, SAM capacity, deadline counts, lock waits, cache bypass accounting, source-root checks and worker setup retain passing tests. All thirteen reviewed-baseline regressions reproduce, including both CLI variants.

### Review round 3: finding -> fix -> test

Install/type-boundary hashes and cheap fatal live guards, processor-only mode, operator memory/overlay dispatch, full base authentication, behavioral lock/worker regressions and the OFF import guard retain passing tests. The generic operator test checks the atomic nested merge; the round-4 test checks the actual cache-only adoption profile. The OFF guard now includes a0–a19. All round-3 failing baselines reproduce.

These audit sections retain finding history only because the dispatch explicitly requires it. Other sections state the delivered behavior and current evidence.

## Patches and measured resource bounds

A4 base SHA256: `{base}` over {manifest['base_pin']['files']} files. B5 archive SHA256: `{manifest['b5_base_archive_sha256']}`. The B5 check proves reader-patch applicability, not kit compatibility. [MANIFEST.json](patches/MANIFEST.json) binds all patches, file inventories, operator inputs and delivery bytes.

| Patch | Bytes | SHA256 |
|---|---:|---|
'''
for name,info in manifest['patches'].items():report+=f"| [{name}](patches/{name}) | {info['bytes']} | `{info['sha256']}` |\n"
report+='''
Patches 01–03 are additive under src/u0. Patches 04–05 apply from the A4 operator directory: tower_sequence.py, unpack_return.py and package/a/5.py. The bootstrap remains byte-identical to A4. Tests ship in patch 03. The explicit A4 builder and fixture are new; the generic a12 operator route rejects incomplete builds.

All workspace suites were rerun once against final source bytes. To remain below 3 GB without deleting files, fresh-application testing repeats only OFF, round-4 integration and comparator suites. Every other applied file is authenticated byte-for-byte against the already-tested source. This avoids a redundant full fixture corpus; it does not skip a requested test.

The original timing profile was recomputed from supplied journals. The cache caps are configured cache-owned storage bounds, not measured process peaks. The small allocation receipt remains in MEMORY.json; its 3 GiB capacity regression simulates accounting without allocating that tensor. Preserve full-process host/GPU headroom.

## What could go wrong and how to notice

| Risk | Detection/action |
|---|---|
| Wrong export, archive, preparation or stale helper | Required target binding, sealed fill constants, payload/plan/package pins and real export-admission checks refuse mismatches. Never reuse the test binding. |
| A4 proof omits the ON memory allowance | Generate proof through the patched a/5.py and inspect read_cache_bytes; unchanged bootstrap admission alone is insufficient for this field. |
| Untracked weight mutation or hard worker death | Boundary checks leave false receipts; ON unpack/resume/merge/comparison refuse unchecked journals. Use fresh output after an unverified hard kill. |
| GPU kernels, layouts, eager SAM load or RNG affect bytes | Require the complete zero-tolerance GPU gate before adoption. |
| Hashes/copies/cache misses erase savings | Require useful hits and lower complete worker wall time; credit no savings from the CPU ratios. |
| Cache allowance understates whole-process memory | Measure real host/GPU peaks; cache caps do not cover model/caller working storage. |
| Real namespace, transport, return capacity or requeue differs from stubs | Exercise production restore/storage/envelope checks; keep general/no-requeue until persistent-storage requeue passes. |

## Not done

No real step-600 binding/export build, real weight restore, production bwrap/storage/transport, GPU parity/performance/memory, scheduler action, upload, return publication or persistent-storage requeue ran. No multi-card operator or batching is delivered. The array policy remains approved=false. The synthetic CPU fixture is not a staging package or production proof.

No delivered CPU suite or single-GPU parity pass requires a local OS socket; StageOneSocket is a Python callback. Socket-backed integration remains unrun. These limits do not waive the zero-tolerance GPU gate.

## Commands and exact outputs

Commands below ran from `/scratch/jjyeung/orch_n30/so_read`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then executes nice -n 10 with the required Python -I -s -B. Tests call torch.set_num_threads(8). Child commands inherit that environment and priority. Workspace tests also receive READ_INPUT_SRC and READ_TEST_TMP; fresh-application tests additionally receive READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE from MANIFEST's verification root.

'''
def block(cmd,output):
 global report
 report+='```bash\n'+cmd+'\n```\n\nExact output:\n\n```text\n'+(C/output).read_text().rstrip()+'\n```\n\n'
for script,output in [('profile.py','profile_rerun.txt'),('torch_versions3.py','torch_versions3.txt'),
                       ('benchmark_round3.py','cache_cost3.txt'),('run_checks.py','run_checks4.txt'),('build_patches.py','build_patches4.txt')]:
 block('bash work/cpu.sh work/'+script,output)
for entry in results['results']:
 block(shlex.join(entry['command']),entry['output'])
for entry in manifest['applied_cpu_suites']:
 block(shlex.join(entry['command']),entry['output'])
for var,script,output,extra in [
 ('READ_REVIEW_BEFORE','test_round1.py','round1_before.txt',''),
 ('READ_ROUND2_BEFORE','test_round2.py','round2_before.txt',''),
 ('READ_ROUND3_BEFORE','test_round3.py','round3_before.txt',''),
 ('READ_ROUND3_BEFORE','test_operator_round3.py','operator3_before.txt',''),
 ('READ_LOCK_BEFORE','test_lock_round3.py','lock3_before.txt',''),
 ('READ_F16_BEFORE','test_round3.py','f16_behavior_before.txt',' Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect'),
 ('READ_ROUND4_BEFORE','test_round4.py','round4_before.txt',''),
 ('READ_NODE4_BEFORE','test_round4.py','node4_before.txt',' Round4Tests.test_f2_step600_real_job_and_rehearsal_memory')]:
 block(var+'=1 bash work/round3_env.sh work/src/u0/tests/'+script+extra,output)
(O/'REPORT.md').write_text(report)
first=cost['cases'][0]
note=f'''VERDICT: DONE The round-4 fixes pass CPU verification; adopt only after the GPU byte gate.

Measured: **{workspace} workspace tests and {applied} fresh-application tests pass**. Five patches apply exactly; original reader files and complete OFF output bytes remain unchanged. The backup is out_round4/. The CPU fixture completes 636 synthetic reads with five verified ordinary journals through real A4 preparation, rehearsal, bootstrap and job.main.

Measured existing distance time is **23.60 s/item**. Estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. Ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. Measured CPU guard/cache overhead on a 268M-parameter bf16 stub is **{1000*first['after_per_call']['median_seconds']:.1f} ms/call**. This is not a GPU saving.

## Review round 4: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Incomplete step-600 package | a19 uses A4 build_r1-style post-processing, preserving 8.py, run keys and admission. It requires the reviewed target export/whole-archive binding and seals the fill helper. Wrong binding/receipt checks fail; the documented old build fails before. |
| 2. Adoption profile not exercised | Real job.main constructs actions 0/1 from packaged 9.json. Real 7.py rehearsal produces MEMORY.json with 12 GiB cache allowance. Stub workers produce five verified ordinary journals. The old CPU-proof helper fails the allowance test. |
| 3. Unchecked cache-only return | ON unpack rejects non-true WEIGHTS receipts. Invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |
| 9. README nits | Commands use explicit delivery/source roots; kit pin is A4-only; README states what bootstrap admission actually checks. |

**Step 600: one card, caches only, general/no-requeue.** Apply 01–03 to a full A4/src copy and 04–05 to an A4 operator copy. Define the local roots using [README](kit_parity50/README.md), then build:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

The required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. The CPU task has no real step-600 export; its test binding is synthetic. The generic a12 operator build is refused. Add --processor-only for the 4 GiB processor cache; otherwise the cache allowance is 12 GiB. Both disable atomic journals and sharding. A4's fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.

Use the generated fill helper, regenerate CPU proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. Exact fill/proof commands are in README. Require read_cache_bytes in MEMORY/CPU.json, along with payload/plan/inputs/operator binding and fits=true. The unchanged 0.py admission does not independently require that field. Cache-only returns retain ordinary journals; ON unpack refuses unchecked weights even on partial returns.

Before adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/GPU/envelope headroom. ON's eager SAM construction and boundary hashing need the GPU gate. The sample overstates reuse. Keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. Hard kills can require fresh journals. Validate persistent-storage requeue before any preempt/sharded use. Stage source trees as archives and run the kit with --public. No launch ran; preserve step-400 deliveries.

Exact commands, outputs, citations and limits: [REPORT](REPORT.md). Patch/base pins: [MANIFEST](patches/MANIFEST.json).
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
print(f'PASS: REPORT and NOTE describe round-4 delivery; {workspace} workspace and {applied} applied tests; exact outputs embedded.')
print('UTC: '+stamp)
