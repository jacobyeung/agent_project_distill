# Generate the report from captured measurements and verification artifacts.
import json
from pathlib import Path
import re
from datetime import datetime,timezone
L=Path('/scratch/jjyeung/orch_n30/so_read');O=L/'out'
P=json.loads((O/'profile.json').read_text())
C=json.loads((O/'checks/RESULTS.json').read_text())
M=json.loads((O/'patches/MANIFEST.json').read_text())
B=json.loads((O/'checks/OFF_BYTES.json').read_text())
H=json.loads((O/'checks/MEMORY.json').read_text())
assert all(r['returncode']==0 for r in C['results']+M['applied_cpu_suites'])
assert B['passed'] and B['exclusions']==[]
def count(file):return int(re.search(r'Ran (\d+) tests?',(O/'checks'/file).read_text()).group(1))
n=sum(count(r['output']) for r in C['results']);a=sum(count(r['output']) for r in M['applied_cpu_suites'])
rows=['| Package/type | Items | Mean s/item | Median | p90 | Tokens/item: total / ordinary | Calls/item | G3T s/item | Factory load s |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for package,data in P['packages'].items():
 for kind,d in data['types'].items():
  g=d['timings'].get('g3t_s',{}).get('mean')
  rows.append('| '+' | '.join([package+'/'+kind,str(d['items']),f"{d['seconds']['mean']:.3f}",f"{d['seconds']['median']:.3f}",f"{d['seconds']['p90']:.3f}",f"{d['tokens_including_forced']['mean']:.2f} / {d['ordinary_sampled_tokens']['mean']:.2f}",f"{d['calls']['mean']:.2f}",'0 (no call)' if g is None else f'{g:.3f}',f"{d['factory_load_s']:.3f}" if d['factory_load_s']>.01 else '0 (reused)'])+' |')
fixes=[
('1. Mapping collision','Typed mapping lengths delimit every nesting level.','Distinct nested dictionaries hash differently and cannot return stale processor output.'),
('2. Vacuous parity','Require enabled-cache declarations, positive hits, valid memory receipts, full production output fields, scale even when null, and nested served responses.','Empty/all-miss/incomplete traces, wrong membership, and changed text/tokens/responses fail even when scores agree.'),
('3. Default OFF','Both diffs add files under src/u0, outside original source-hash trees. Ordinary entrypoints import no extension and parse no new setting.','Complete output files/stdout and real source hashes match the original under controlled clocks without dropping fields; the 50-read fixture also compares complete original/OFF records. GPU ORIGINAL/OFF selects separate source roots and original journal/shard defaults.'),
('4. Lifetime','Keys bind tensor identity, pointer, version/content, module/configuration/attention options, backend flags, and processor implementation. SAM checks root/child/global hooks; unsafe dispatch bypasses.','Parameter replacement, raw .data writes, live option/autocast changes, returned-value mutation, and SAM root/global hooks pass.'),
('5. Deadline recovery','The writer guard repairs only a matching established environment, while holding writer.lock. Interrupted unbound startup creates no item projection.','A second file descriptor cannot acquire the lock during recovery; interruptions before/after environment creation resume without unbound or duplicate rows.'),
('6. Orchard opacity','Use neutral public names/paths, numeric selectors, token-only JSON, hashed identities, and hashed arbitrary logs. Keep reverse maps private.','Staging, legacy log contexts, requeue, authenticated Trinity restoration and public/private canonical row/archive equality pass. Every GPU arm uses the same separately hashed explicit public transport wrapper.'),
('7. Cache memory','Charge keys/containers/payloads, reserve snapshot/restore copies, and evict before allocating. Stream keys; bypass unsupported constructors/layouts and require the owning thread.','Oversized keys/containers never snapshot, eviction precedes snapshot allocation, cross-thread calls fail, and the 2,000,000-byte fixture stays below its cap.')]
review='| Finding | Fix | Test |\n|---|---|---|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in fixes)
r=f'''VERDICT: DONE All seven HIGH/MEDIUM findings have fixes and passing CPU regressions; production adoption remains NO-GO until the unrun GPU and persistent-storage gates pass.

**Measured:** {n} CPU tests pass; {a} also pass from a fresh application of the regenerated patches. Eight targeted checks fail against the reviewed implementation and pass against the delivered implementation. Both additive diffs apply with zero fuzz to A4/B5; every original reader/evaluator hash-tree byte remains unchanged.

**Estimated:** Budget 23.60 seconds per distance item and 3 h 50 min per 580-item read. Ideal simultaneous two/four-shard reads estimate 1 h 56 min / 59 min. No cache saving receives credit; live content hashing and copying may cost more than they save. Step 600 remains the earliest adoption point.

## Measured profile

'''+ '\n'.join(rows)+'''

These are supplied step-200 measurements, not new GPU runs. Total tokens include forced tool responses and budget tokens; ordinary tokens use the existing ordinary_sampled_tokens field. The factory window includes processor/model restore/setup, but not deferred tower loading. A4 loads once and reuses its generator across all five types. G3T seconds include lookup/restore or a fresh call; they do not measure SAM, scale, or total tower work. SAM has no independent timer.

'''
for package,data in P['packages'].items():
 r+=package+' measured sources: '+', '.join(f"[{kind}]({d['source']})" for kind,d in data['types'].items())+'. Adjacent timings.jsonl files supply factory-load windows.\n\n'
r+='''A4 records 7,351.824 seconds from start to exit: 7,224.888 seconds in items, 75.446 in initial loading, 1.729 in journal/control windows, and 49.761 outside type timers. B5 records 645.735 seconds, including 528.164 in items and 78.961 in loading. These residuals do not establish GPU idle time.

One distance item takes 648.397 seconds for 2,056 tokens; its cause is unknown and the forecast retains it. Distance has 88 routed items with two served ground calls and one served gap call each, plus 62 direct items. Source inspection implies 88 SAM encodes and 176 raw-name detections for those routed reads; these counts are inferred. Every camera read serves one move/turn call; room reads serve none.

A4 already reuses G3T: 461 hits and 77 misses over 538 accesses, with 128,553,354 retained payload bytes. That gain cannot be counted again. The supplied old memo configuration lists G3T only. Every read still computes own-prefill scale, geometry, selector work and tool responses. The new cache stores no whole prompt, language prefill, recurrent/KV state, own-depth scale, or complete response.

## Review round 1: finding -> fix -> test

'''+review+f'''

INFO 8–10: fsync/rename, ownership checks and deterministic merging remain covered; forecast arithmetic remains unchanged. Framework CPU tests pass with writable local caches. Real persistent-storage requeue and GPU work remain release gates.

## OFF contract, purity and memory

The launcher hashes entire original source directories. Additive files inside those directories would change OFF provenance even without an import. All delivered additions therefore live in src/u0. No original hash is forged or replaced with a baseline constant. Explicit ON execution records extension_code_sha256 alongside baseline hashes.

The production-launcher CPU comparison uses a model fixture and controlled clocks. Every byte of {', '.join(B['files'])} and stdout matches the original; no timing/provenance field is removed and source hashes are real. A fresh-process guard rejects extension imports and new-setting lookups. The 50-read CPU fixture stubs model compute and compares complete original/OFF outputs. These are correctness fixtures, not real-model GPU measurements. Receipt: [OFF_BYTES.json]({O/'checks/OFF_BYTES.json'}).

Processor keys bind ordered input arrays, frame metadata, kwargs, configuration, implementation identity and execution settings. Vision keys also bind live parameter/buffer identity, storage, versions/content, attention implementation and backend controls. SAM keys bind pinned files, ordered RGB pixels, frame indices/slots, live model identity/content, precision/batching settings, backend identity/options, object name and retention contract. Child/global hooks and unsafe dispatch take fresh paths. PID changes reset the generator-owned serial cache. Hits return independent supported values. The new SAM policy rejects simultaneous use of the old SAM memo policy.

The hard cache bound includes cache-owned live payload, keys, containers, allocator allowances and current snapshot/hit-copy transients. B=262,144 bytes reserves bookkeeping/key scratch. Admission evicts until B+held+2R fits before allocating a snapshot; hits reserve their restore copy. R includes payload and conservative key/container allowances. Budgets below 256 KiB are rejected. Unsupported constructors, subclasses/layouts and excessive nesting bypass caching. The bound excludes model working memory, the old G3T memo and outputs the caller continues to own; it is not a whole-process RSS cap.

**Measured memory fixture:** cap {H['cap_bytes']:,} bytes; Python allocation peak {H['peak_python_bytes']:,}; maximum reserved cache peak {H['peak_reserved_bytes']:,}. It exercises hit copying and eviction before the next snapshot. Receipt: [MEMORY.json]({O/'checks/MEMORY.json'}). Full item/wall timings include hashing and copies; internal hit_s counters exclude key construction. Production host/GPU peaks remain unmeasured.

Batched greedy decoding is not included. Padding, batch shape, SDPA and recurrent/chunk kernels cannot receive a bit-equality guarantee; see the installed-source citations in [FRAMEWORK_EVIDENCE.md]({O/'FRAMEWORK_EVIDENCE.md'}) and the official [PyTorch numerical-accuracy note](https://docs.pytorch.org/docs/2.11/notes/numerical_accuracy.html). Equal scores can hide changed answers. The gate compares text, token IDs, calls/responses, heads, scale, finish, scores, budgets and all remaining semantic fields with zero tolerance.

## Patches, test commands and exact outputs

Apply BOTH diffs from a fresh full staged src tree with patch --batch --fuzz=0 -p1. [MANIFEST.json]({O/'patches/MANIFEST.json'}) pins all {sum(len(x['files']) for x in M['patches'].values())} added files and kit assets, proves unchanged original roots, and records fresh-application commands. Ordinary entrypoints remain OFF. Explicit ON uses u0/a8.py --enable-extensions; read_*_cache switches still default off. Atomic journaling and scene sharding additionally require --atomic-journal and --scene-shards; the array requires --enable-array.

```bash
bash work/cpu.sh work/run_checks.py
```

Exact captured output:

```text
'''+(O/'checks/final_cpu_run.txt').read_text()+'''```

```bash
bash work/cpu.sh work/build_patches.py
```

Exact captured output:

```text
'''+(O/'checks/final_patch_run.txt').read_text()+'''```

The individual commands below inherit nice 10, CUDA hidden, eight threads and local writable caches from work/cpu.sh.

'''
for label,results in [('Workspace suites',C['results']),('Fresh-application suites',M['applied_cpu_suites'])]:
 r+='### '+label+'\n\n'
 for result in results:r+='```text\n'+' '.join(result['command'])+'\n```\n\nExact output:\n\n```text\n'+(O/'checks'/result['output']).read_text()+'```\n\n'
r+=f'''The eight expected before-fix failures are retained in [round1_before.txt]({O/'checks/round1_before.txt'}); exact patch-tool output is [patch_application.txt]({O/'checks/patch_application.txt'}). Tests used torch {C['torch']}, transformers {C['transformers']}, eight torch threads and CUDA_VISIBLE_DEVICES="". Measured maximum child RSS: {C['max_child_rss_bytes']:,} bytes; workspace size at CPU verification: {C['workspace_bytes']:,} bytes, below 3 GB.

## Requeue, opacity and return checks

Commits fsync before rename and directory fsync. The JSONL file is a recoverable projection. Recovery validates an established matching environment and executes under writer.lock. An interrupted computation may repeat; a committed answer cannot duplicate. Whole-room assignment preserves disjoint complete membership and manifest order. The merger rejects foreign, missing, duplicate or differently bound rows. Actual persistent-filesystem power-loss/requeue behavior remains untested.

Public staging uses opaque job/log/asset paths, numeric selectors, token-only JSON, hashed IDs and hashed arbitrary logs. The staged kit has neutral filenames and pins its transport wrapper separately. It refuses raw public metadata or descriptive absolute config paths. Private restoration on Trinity authenticates public commits before rebuilding private-ID checksums/filenames. CPU fixtures compare restored-public and private canonical archives byte for byte, and compare decoded public canonical rows exactly. Full payload staging/authentication and real storage/return transport still need orchestrator integration.

GPU ORIGINAL/OFF/OFF_REPEAT use separate source roots and original journal/shard defaults. Cache ON runs separately from journal/shard ON passes. The same explicit public transport wrapper protects every arm; this wrapper belongs to the opt-in experiment, while the ordinary OFF reader imports none of the extensions. Every enabled cache must show positive hits and valid memory receipts; SAM needs both feature and detection hits. Empty/all-miss/incomplete runs fail. ORIGINAL/OFF also compares all production source-hash fields. Raw clock/provenance evidence remains present in token form. Canonical answer/trace returns exclude telemetry; independent real-clock transport envelopes cannot match byte for byte.

## Forecast, failure detection and work not run

**Estimated:** 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds gives **13,813.069 / 6,969.138 / 3,547.173 seconds** for one/two/four shards. This assumes simultaneous balanced execution and excludes queue time, staging, preemptions/reloads and stragglers. Keep 23.60 seconds/item for planning until a representative GPU read establishes a net gain. The fixed 50-item sample stresses reuse, not representative throughput.

| Risk | Detection and release action |
|---|---|
| Missing dependency or nondeterministic GPU output | Require ORIGINAL/OFF/OFF-repeat/ON exact text/token/call/head gates; keep a failing cache OFF |
| Hashing, copies or churn exceed saved work | Check full item/wall time, useful hits, eviction/oversize counters and host/GPU memory; credit no speedup |
| Partial/unbound/overlapping journal writes | Validate lock/binding/checksums/membership, then test one real persistent-storage preemption/requeue |
| Public naming/configuration/log leak | Require neutral staging, token metadata, public log wrapper and authenticated private restoration |
| Stale payload/artifact/code pins | Rebuild and dry-check the approved deployment; rebinding alone cannot install source additions |
| CPU fixtures miss GPU preprocessing/FLA/layout behavior | Pass the actual H100/CUDA kit before step 600; no numeric tolerance waiver |

**Not run:** GPU original/OFF/ON and sharded parity, H100/CUDA speed/memory, production RGB/resize preprocessing, real preemption/persistent storage, deployment package dry checks and return publication. The tiny installed processor CPU fixture disables unavailable torchvision RGB/resize/normalization and checks native packing/metadata; the installed tiny vision fixture uses CPU/eager attention. No GPU, Git, SSH, Slurm, paid API, upload or input-tree edit ran.

**Sockets:** no delivered CPU suite or single-GPU parity pass opens a local OS socket. StageOneSocket is a Python callback. Socket-backed transport/distributed rendezvous integration would require socket access and remains unrun; the sandbox limitation skips no delivered CPU test.
'''
(O/'REPORT.md').write_text(r)
note=f'''Keep adoption NO-GO until GPU and persistent-storage gates pass. Step 600 is the earliest candidate; preserve step-400 deliveries. All seven code findings have fixes. {n} CPU tests pass, and {a} pass again from fresh patches; both diffs apply exactly to A4/B5.

Measured distance time is **23.60 s/item** (median 18.28; p90 29.18), including an unexplained 648.40-second outlier. A4 loads once in 75.45 seconds and already reuses G3T. SAM time is not isolated. Cache savings receive no credit; live hashing may outweigh them.

| Estimated 580-item read | Elapsed time |
|---|---:|
| One GPU | 3 h 50 min |
| Two balanced simultaneous shards | 1 h 56 min |
| Four balanced simultaneous shards | 59 min |

The formula is 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds. It excludes queues, staging, preemptions/reloads and imbalance. Budget **23.60 s/item per GPU**.

## Review round 1: finding -> fix -> test

| Finding | Fix | Test |
|---|---|---|
| 1. Key collision | Delimit mappings by length. | Collision/stale-processor regressions pass. |
| 2. Vacuous parity | Require hits, schemas, scale and responses. | Empty/all-miss/incomplete traces fail. |
| 3. Default OFF | Add files outside original hash trees. | Complete files/stdout and actual hashes match the original under controlled clocks, with no exclusions. |
| 4. Lifetime | Bind live identities/content/options; bypass hooks. | Replacement, raw edits, option changes and SAM hooks pass. |
| 5. Deadline | Recover under the bound writer lock. | Lock/startup interruption tests pass. |
| 6. Opacity | Use neutral names, token JSON/IDs and hashed logs. | Staging, requeue and authenticated Trinity restoration pass. |
| 7. Memory | Reserve keys, containers and transient copies. | {H['peak_python_bytes']:,}-byte Python peak stays below a 2,000,000-byte fixture cap. |

Ordinary OFF imports no extension and parses no new setting. Apply both patches; explicit ON uses u0/a8.py --enable-extensions. The 4 GiB cap covers cache-owned live storage/copies, not model working memory or caller-owned outputs. Unsupported values bypass.

Create the token-only GPU kit on Trinity using its README; keep private maps/fixtures/reports there. Public staging needs approved opaque paths and rebuilt pins. Require ORIGINAL/OFF/OFF-repeat/ON and separate journal/shard checks, identical answers/tokens/calls/responses/heads/scale/scores, matching source hashes, useful hits, lower total item time, memory headroom and canonical return equality. Then prove a real persistent-storage requeue returns every expected ID exactly once.

GPU parity/speed, production memory fit, persistent requeue and deployment dry checks remain **unrun**. No delivered CPU or single-GPU test needs a local socket; socket-backed transport/distributed integration remains unrun. Commands, exact outputs and limits: out/REPORT.md. Pins: out/patches/MANIFEST.json.
'''
(O/'NOTE_FOR_CONT_OPS.md').write_text(note)
(L/'work/STATUS.md').write_text(datetime.now(timezone.utc).isoformat()+f'\nReview round 1 complete: {n} CPU tests pass; {a} fresh-application tests pass. Eight reviewed-code failures reproduced. Patches/MANIFEST regenerated; original hash trees unchanged; A4/B5 zero-fuzz application verified. Reports rewritten. GPU/persistent-storage/deployment checks remain unrun release gates. No socket-dependent CPU test was skipped.\n')
print(f'PASS: reports rewritten; {n} CPU tests and {a} fresh-application tests pass.')
