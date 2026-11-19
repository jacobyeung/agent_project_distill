"""Write the handover from measured receipts; never run workloads."""
import json
from pathlib import Path
import re
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
C=json.loads((O/'checks/RESULTS.json').read_text())
M=json.loads((O/'patches/MANIFEST.json').read_text())
P=json.loads((O/'profile.json').read_text())
B=json.loads((O/'checks/OFF_BYTES.json').read_text())
H=json.loads((O/'checks/MEMORY.json').read_text())
assert all(r['returncode']==0 for r in C['results']+M['applied_cpu_suites'])
assert B['passed'] and B['exclusions']==[]
def count(result):
    return int(re.search(r'Ran (\d+) tests?',(O/'checks'/result['output']).read_text()).group(1))
n=sum(map(count,C['results']));a=sum(map(count,M['applied_cpu_suites']))

findings=[
('1 HIGH: isolated ON entry','Add the extension directory to the entrypoint path before activation.','F1 runs the actual loader as an isolated script, with and without opaque mode; both variants fail before and pass after.'),
('2 MEDIUM: Orchard paths','Accept the established user/package prefixes followed by neutral tokens, and apply the production forbidden-word screen.','F2 exercises settings sealing, array validation, and the output grammar on all established roots; forbidden words and traversal fail.'),
('3 MEDIUM: array submission','Derive argv from submit_argv; retain account, export=NONE, /dev/null logs, and approved job names. Require explicit owner approval of preempt and a bounded attempt policy. Pin the config; use the neutral staged entry and bounded exit-75 requeue.','F3 checks argv/script opacity, approval and lifetime GPU-hour limits, and shell exits 0/2/75 using a fake scheduler function. No scheduler is invoked.'),
('4 MEDIUM: production integration','Provide an additive opt-in builder that packs/pins u0 and selects entry, job, runner, and preparation overlays. Route ON through a8, count scene shards, and bind the canonical merge inside the existing metadata return envelope.','Three F4 regressions build real CPU packages and verify every payload pin, compare original/OFF package bytes, exercise dispatch, and compare integrated multi-shard versus single-shard canonical returns.'),
('5 MEDIUM: cost and capacity — PARTIAL','Set the SAM-ON default to 12 GiB, including the kit and production package. Keep full content hashing: the suggested version-only optimization violates the required raw-mutation invalidation contract. Net speed and memory remain unmeasured.','F5 models a 3 GiB reservation without allocating it: 4 GiB rejects it and 12 GiB admits a hit. A real .data mutation leaves id/pointer/version unchanged while changing the content identity. The capacity regression fails before; hashing cost remains unresolved.'),
('6 LOW: non-atomic deadline','Count existing committed JSONL rows under the writer lock and publish initialized progress without creating a commit store.','F6 checks completed=1, initialized=True, lock ownership during the read, unchanged JSONL bytes, and no committed directory.'),
('7 LOW: shared-storage lock','Wait with backoff for at most 60 seconds, then return 75 for the generated script to handle.','F7 holds a real second descriptor lock, verifies bounded timeout using a simulated clock, releases it, and verifies acquisition. F3 verifies bounded retry handling.'),
('8 LOW: processor bypass','Count unsupported-key bypasses in processor statistics.','F8 makes two unsupported calls, verifies two bypasses and no cached entries.'),
('9 LOW: independent roots','Reject equal resolved roots or an extension-bearing original root; authenticate the complete patched extension inventory against the manifest-derived pins before any arm starts.','F9 checks a valid independent pair, equal roots, a changed file, and an extra file. Stage-kit tests authenticate the token-only inventory.'),
('10 LOW: weak regressions','Require the exact missing-scale error and exact no-hit reason. Include behavioral lock, public-boundary, and full OFF-byte tests in the round-1 suite.','F10 injects an unrelated ValueError, which must fail the test, and checks that the lock regression is included. The round-1 suite now runs 17 tests.'),
('16 INFO: environment name','Remove the descriptive settings environment assignment. An in-process --settings argument preserves the original native-tree selection.','F16 checks both removal and the replacement selection mechanism. The ordinary original files remain unchanged.'),
]
table='| Finding | Fix or disposition | Regression evidence |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in findings)

r=f'''VERDICT: PARTIAL Findings 1–4, 6–10 and 16 have CPU-verified fixes; finding 5's hashing cost remains unresolved and production adoption remains NO-GO.

**Measured:** {n} workspace tests pass; {a} tests pass from a fresh patch application. All 13 round-2 regressions fail on the reviewed bytes and pass on the delivered bytes; the entrypoint test has two failing baseline variants. All eight round-1 regressions also fail on their reviewed baseline. Three additive patches apply with zero fuzz to A4/B5, and original reader/evaluator/production source files remain unchanged.

**Estimated:** Retain 23.60 seconds per distance item and 3 h 50 min per 580-item read. Ideal simultaneous two/four-shard wall times remain 1 h 56 min / 59 min. These estimates credit no cache saving and exclude queues, staging, preemptions and scene imbalance. Step 600 is the earliest adoption candidate.

**Measured test resources:** torch {C['torch']}, transformers {C['transformers']}, eight torch threads, CUDA hidden, nice 10. Peak child RSS was {C['max_child_rss_bytes']:,} bytes. Workspace size at the CPU-suite check was {C['workspace_bytes']:,} bytes, below the 3 GB limit. No GPU, Git, SSH, Slurm command, paid API, upload or input-tree edit ran. Network reads accessed official library documentation only.

## Review round 2: finding -> fix -> test

'''+table+'''

Finding 5 is deliberately not described as fixed. Reusing a hash based only on id, data_ptr, and _version would return stale values after the mutation exercised by F5 and the existing raw-storage regressions. The installed torch source explains that untracked data changes need explicit version updates: [graph.py:242](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/autograd/graph.py:242), with the official [increment_version reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html). No safe faster implementation or GPU speed measurement is delivered. All caches remain OFF through ordinary entrypoints; net savings must be measured before adoption.

The array example records approved=false. The generated plan requires the owner to approve the exact preempt partition, count, duration and attempt limit. The example proposes two one-hour shards with at most two attempts each, an estimated allocation upper bound of four GPU-hours. The helper rejects plans above five GPU-hours across allowed attempts. It generates files only. Approval, real scheduler behavior and persistent-storage behavior remain unverified.

INFO 11–15: the ordinary OFF path, cache safety, durable journal/shard invariants, non-vacuous parity gate and forecast remain covered by rerun tests and source checks. No numeric tolerance is permitted for answers or traces.

## Review round 1: finding -> fix -> test

| Finding | Verified implementation | Rerun evidence |
|---|---|---|
| Key collisions | Typed, length-delimited nested values. | Mapping/stale-processor regression fails before and passes after. |
| Vacuous parity | Exactly 50 expected unique IDs, full trace schema, scale, served responses and useful hits for each enabled cache. | Empty/malformed/all-miss traces fail; no-hit reasons and missing-scale messages are asserted. |
| OFF provenance | Additions live outside original source-hash trees. | Complete files/stdout and real provenance hashes match the original under controlled clocks; no fields are excluded. The package build also matches original/OFF bytes. |
| Model lifetime | Live identity/content/options bind vision and SAM keys; hooks bypass. | Replacement, raw writes, options, autocast, returned-value mutation and hook tests pass. |
| Deadline ownership | Repair matching journals while holding writer.lock. | A second descriptor cannot acquire the lock during recovery; interrupted initialization resumes correctly. |
| Public boundary | Token metadata/IDs, neutral names, hashed logs and private authenticated restoration. | Public/private canonical returns match; every production forbidden word is rejected in staged paths. |
| Memory | Reserve payloads, keys, containers and transient copies; evict before snapshot allocation. | Oversized values/keys bypass; owning-thread checks and measured small-memory fixtures pass. |

## Measured profile and forecast

The profile was recomputed from the supplied journals. These are existing step-200 GPU measurements, not new GPU runs. Exact recomputation output is in [profile_rerun.txt](checks/profile_rerun.txt); [profile.json](profile.json) records each source path and SHA256.

| Package/type | Items | Mean s/item | Median | p90 | Tokens/item: total / ordinary | Calls/item | G3T s/item | Factory load s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
'''
for package,data in P['packages'].items():
    for kind,d in data['types'].items():
        g=d['timings'].get('g3t_s',{}).get('mean')
        r+='| '+' | '.join([package+'/'+kind,str(d['items']),f"{d['seconds']['mean']:.3f}",
            f"{d['seconds']['median']:.3f}",f"{d['seconds']['p90']:.3f}",
            f"{d['tokens_including_forced']['mean']:.2f} / {d['ordinary_sampled_tokens']['mean']:.2f}",
            f"{d['calls']['mean']:.2f}",'0 (no call)' if g is None else f'{g:.3f}',
            f"{d['factory_load_s']:.3f}" if d['factory_load_s']>.01 else '0 (reused)'])+' |\n'
r+='''
Total tokens include forced tool responses and budget tokens. Factory loading covers processor/model restore/setup, not deferred tower loading. A4 reuses one generator across five types. G3T timings cover lookup/restore or fresh execution; they do not measure SAM or total tower time. SAM has no independent timer.

A4 records 7,351.824 seconds from start to exit: 7,224.888 in items, 75.446 in loading, 1.729 in journal/control windows, and 49.761 outside type timers. B5 records 645.735 seconds, including 528.164 in items and 78.961 in loading. Residual wall time does not establish GPU idle time.

The distance profile retains one unexplained 648.397-second, 2,056-token item. There are 88 routed and 62 direct distance items. Source inspection implies 88 SAM encodes and 176 raw-name detections; those call counts are inferred. Camera items each serve one move/turn call; room items serve none.

A4 already records 461 G3T memo hits and 77 misses, retaining 128,553,354 payload bytes. This saving cannot be counted again. The new caches store video processor outputs, visual outputs and raw SAM values. They do not store question text, language/KV/recurrent state, own-depth scale, geometry or full tool responses.

**Estimated forecast:** 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds gives 13,813.069 / 6,969.138 / 3,547.173 seconds for one/two/four balanced simultaneous shards. Whole scenes stay together, so the largest shard sets elapsed time. The fixed 50-item sample stresses reuse and does not establish representative throughput.

## Equality, memory and deployment contracts

Ordinary entrypoints never import or parse extension settings. The real OFF launcher fixture compares every byte of environment.json, item_mapping.json, items.jsonl, timings.jsonl, writer.lock and stdout, including real source hashes and controlled timing fields. No field is dropped. See [OFF_BYTES.json](checks/OFF_BYTES.json). Model generation in this fixture is stubbed.

The GPU kit requires separate authenticated original and patched roots. ORIGINAL, OFF, OFF_REPEAT, ON, ON_JOURNAL and sharded runs execute in fresh isolated processes. It compares all semantic fields byte for byte and requires positive processor, vision, SAM-feature and SAM-detection hits when enabled. It excludes only measured clocks and explicit audit/cache telemetry; audit violations fail. Equal scores cannot conceal changed answers. The supplied GPU kit is unrun.

Batched generation is not included. The installed SDPA and linear-attention sources do not establish bit equality under changed batching or padding. Framework file:line evidence and official references are in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md). The numerical-accuracy limitation is documented by [PyTorch](https://docs.pytorch.org/docs/2.11/notes/numerical_accuracy.html).

The SAM-ON default cap is 12 GiB; other cache configurations default to 4 GiB. An explicit read_cache_bytes overrides that default. The bound covers cache-owned keys, containers, retained snapshots and snapshot/restore transients. Admission reserves B + held + 2R before copying, with B=262,144 bytes. Model memory, old memo storage and caller-owned outputs are outside this cache cap.
'''
r+=f'''
**Measured memory fixture:** a {H['cap_bytes']:,}-byte cap has a {H['peak_python_bytes']:,}-byte Python allocation peak and {H['peak_reserved_bytes']:,} reserved-byte peak. See [MEMORY.json](checks/MEMORY.json). The separate 3 GiB capacity test simulates reservation accounting; it allocates no large tensor. Production CPU/GPU memory remains unmeasured.

All three diffs add files only under src/u0. The opt-in builder packages these files and chooses authenticated production overlays. The ON preparation pins extension code in the artifact manifest; entry dispatch activates a8; the runner counts scene shards and binds metadata/u0/answer_trace_return.tgz in SUMMARY. The existing return transport includes this metadata subtree. Canonical single/sharded answer/trace archives match in the CPU fixture. Independent transport envelopes still contain variable clocks.

## Patches and base pins

Apply all three patches in numeric order from a fresh full A4/src or B5/src tree with `patch --batch --fuzz=0 -p1`. Tests are included in the patches. [MANIFEST.json](patches/MANIFEST.json) records per-file hashes, patch hashes, kit hashes and application receipts.

A4 non-bytecode source-tree SHA256: `{M['base_pin']['sha256']}` over {M['base_pin']['files']} files. The manifest includes the complete relative-path/hash inventory and the canonical hashing method. B5 archive SHA256: `{M['b5_base_archive_sha256']}`.

| Patch | Bytes | SHA256 |
|---|---:|---|
'''
for name,pin in M['patches'].items():r+=f"| [{name}](patches/{name}) | {pin['bytes']} | `{pin['sha256']}` |\n"
r+='''
Explicit reader ON: `u0/a8.py --enable-extensions`, with cache switches in settings and separate atomic/scene flags. Explicit production build ON: `u0/a12.py --enable-extensions`. Explicit array-plan generation requires a15's enable flag and an approved policy. The [kit README](kit_parity50/README.md) gives full build, staging and acceptance commands. It also describes the inert array template and neutral staged entry.

## What could go wrong and how to notice

| Risk | Detection and required action |
|---|---|
| Hashing/copies cost more than reuse saves | Measure complete item and wall time, useful hits, oversize/eviction counters and memory. Credit no speedup until the GPU gate shows a net gain. |
| 12 GiB cache leaves insufficient host memory | Measure full process peak, including model and caller storage; reduce/disable the cache if needed and rerun the exact gate. |
| GPU preprocessing or kernels change answers | Require ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded byte equality with zero tolerance. CPU/eager fixtures cannot replace this gate. |
| Persistent locks, preemption or requeue lose progress | Run one real persistent-storage interruption and bounded requeue, then verify each expected ID appears exactly once. |
| Stale payload/config/code pins | Rebuild from the pinned input and verify payload, artifact, extension-inventory and array-config hashes before decode. |
| New return artifacts exceed the existing envelope cap | The unchanged publisher rejects oversized returns; dry-check the complete production return before adoption. |
| Invalid public paths or naming leaks | Use approved roots and token-only kit configs, the production word screen, neutral argv/scripts and hashed logs. Retain private maps on Trinity. |

## Not done

Finding 5's full-content hashing cost remains unresolved. No GPU speedup or production-memory claim is made. GPU parity with every switch ON, H100/CUDA speed/memory, production RGB/resize preprocessing, real scheduler requeue, persistent storage, bwrap/weight restore, remote publication and owner approval of the preempt policy remain unrun or pending. Local CPU package builds and simulated return-envelope membership are complete; they are not deployment validation.

The installed video-processor fixture disables unavailable torchvision preprocessing and checks native packing/metadata. The tiny vision fixture uses CPU/eager attention. No delivered CPU suite or single-GPU kit pass needs a local socket; socket-backed transport/distributed integration remains unrun. StageOneSocket is a Python callback.

The named review-round sections are retained because the dispatch explicitly requires finding-by-finding auditability. Other sections state the current implementation and evidence.

## Commands and exact outputs

Run commands from the assigned workspace. `work/cpu.sh` supplies nice 10, CUDA hidden, eight-thread environment variables, bytecode suppression and workspace-local caches. Test files set torch threads to eight. READ_INPUT_SRC and READ_TEST_TMP are supplied by the drivers.

'''
for command,log in [('bash work/cpu.sh work/profile.py','profile_rerun.txt'),
                    ('bash work/cpu.sh work/run_checks.py','final_cpu_run.txt'),
                    ('bash work/cpu.sh work/build_patches.py','final_patch_run.txt')]:
    r+='```bash\n'+command+'\n```\n\nExact output:\n\n```text\n'+(O/'checks'/log).read_text()+'```\n\n'
for title,results in [('Workspace suites',C['results']),('Fresh-application suites',M['applied_cpu_suites'])]:
    r+='### '+title+'\n\n'
    for result in results:
        r+='```text\n'+' '.join(result['command'])+'\n```\n\nExact output:\n\n```text\n'+(O/'checks'/result['output']).read_text()+'```\n\n'
r+='''### Reviewed-baseline regression runs

Both commands use the same CPU wrapper and READ_INPUT_SRC/READ_TEST_TMP as the drivers. These runs must fail; they establish that the new checks detect the reviewed defects. Exact complete outputs follow.

'''
for mode,script,log in [('READ_REVIEW_BEFORE=1','test_round1.py','round1_before.txt'),
                        ('READ_ROUND2_BEFORE=1','test_round2.py','round2_before.txt')]:
    r+=f'```bash\n{mode} bash work/cpu.sh work/src/u0/tests/{script}\n```\n\n```text\n'+(O/'checks'/log).read_text()+'```\n\n'
(O/'REPORT.md').write_text(r)

note=f'''VERDICT: PARTIAL The review fixes pass CPU tests; weight-hashing cost remains unresolved, so adoption remains NO-GO.

Measured validation: {n} workspace tests and {a} fresh-application tests pass. All 13 round-2 regressions and all eight round-1 regressions fail against their reviewed baselines. Three additive patches apply exactly to A4/B5. Original files and ordinary OFF output bytes remain unchanged; original/OFF package artifacts also match.

Measured distance time is **23.60 s/item** (median 18.28; p90 29.18). A4 loads once in 75.45 seconds and already reuses G3T. SAM time is not isolated. Credit no cache saving.

| Estimated 580-item read | Elapsed time |
|---|---:|
| One GPU | 3 h 50 min |
| Two balanced simultaneous shards | 1 h 56 min |
| Four balanced simultaneous shards | 59 min |

The formula is 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds. It excludes queues, staging, preemptions and scene imbalance. These estimates do not authorize an array allocation.

## Review round 2: finding -> fix -> test

| Finding | Fix and test |
|---|---|
| 1. Isolated entry | Add u0 to the import path; plain/opaque isolated subprocesses pass. |
| 2. Orchard paths | Accept established prefixes and screen forbidden words; all three validation sites pass. |
| 3. Array surface | Generate approved-style argv, neutral script and bounded retry; simulated exit/policy tests pass. Approval stays false. |
| 4. Integration | Add opt-in build/pins/dispatch/scene summary/return overlays; package bytes, pins, dispatch and merge tests pass. |
| 5. Cost/capacity | SAM defaults to 12 GiB; reservation test passes. Full hashing remains because the measured raw mutation defeats version-only invalidation. Performance is unresolved. |
| 6–8. Telemetry/lock | Count non-atomic progress under lock, wait with a bound, and count processor bypasses; regressions pass. |
| 9. Roots | Reject equal roots and inventory/hash changes before arms start; regressions pass. |
| 10. Tests | Assert exact failure reasons and include behavioral lock/public/OFF tests; an unrelated exception cannot pass. |
| 16. Environment | Remove the descriptive variable; preserve native-tree selection through in-process arguments. |

## Review round 1: finding -> fix -> test

Typed keys, non-vacuous parity, unchanged OFF bytes, live model identity, lock-held recovery, token transport and bounded memory all pass their rerun checks. The round-1 suite includes 17 tests.

Apply all three diffs. The explicit production builder packages and pins u0, activates ON workers, counts scene shards and includes the canonical merge inside the existing return envelope. Ordinary entrypoints stay OFF. The SAM-ON cap is 12 GiB; other caches default to 4 GiB. Full process memory is not covered by these caps.

Before adoption at step 600 or later, pass ORIGINAL/OFF/OFF_REPEAT/ON plus journal/sharded GPU gates with every switch ON and zero answer/trace differences. Require useful hits, a measured net time reduction, memory headroom, return-envelope fit and one real persistent-storage requeue with every ID exactly once. The owner must approve the exact preempt policy; no approval or scheduler action occurred here. Preserve step-400 deliveries.

Commands, exact outputs, limitations and framework evidence: [REPORT.md](REPORT.md). Patches/base pins: [MANIFEST.json](patches/MANIFEST.json). Build/staging instructions: [README.md](kit_parity50/README.md).
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
stamp=subprocess.check_output(['date','-u'],text=True)
with (L/'work/STATUS.md').open('a') as f:
    f.write(stamp+f'Rewrote report and handover: PARTIAL for unresolved weight-hashing cost. {n} workspace / {a} applied tests passed; GPU/storage/policy gates remain pending.\n')
print(f'Wrote REPORT.md and NOTE_FOR_CONT_OPS.md: PARTIAL; {n} workspace tests; {a} applied tests.')
