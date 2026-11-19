import json
from pathlib import Path

L=Path('/scratch/jjyeung/orch_n30/so_read')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src')
P=Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages')
p=json.loads((L/'out/profile.json').read_text())
checks=json.loads((L/'out/checks/RESULTS.json').read_text())

def link(label,path,line=None):return f'[{label}]({path}{":"+str(line) if line else ""})'

rows=['| Package/type | N | Mean s/item | Median | p90 | Tokens: total / ordinary mean | Tool calls/item | G3T s/item | Factory load s |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for package,data in p['packages'].items():
    for kind,d in data['types'].items():
        t=d['timings'].get('g3t_s',{}).get('mean')
        load=f"{d['factory_load_s']:.3f}" if d['factory_load_s']>.01 else '0 (reused)'
        rows.append('| '+ ' | '.join([package+'/'+kind,str(d['items']),f"{d['seconds']['mean']:.3f}",
                    f"{d['seconds']['median']:.3f}",f"{d['seconds']['p90']:.3f}",
                    f"{d['tokens_including_forced']['mean']:.2f} / {d['ordinary_sampled_tokens']['mean']:.2f}",
                    f"{d['calls']['mean']:.2f}",'0 (no call)' if t is None else f'{t:.3f}',load])+' |')

report='''VERDICT: DONE The measured profile, default-off patches, CPU checks, and unrun GPU parity kit are delivered; production speed and GPU parity remain unmeasured.

The measured distance mean is **23.600 s/item**, which predicts about **3 h 50 min for 580 items** including the observed load/startup allowance. Four balanced, simultaneous scene shards predict about **59 min** without reducing per-item compute. Cache savings receive no credit until the GPU kit measures them. Step 600 is the earliest adoption point.

All production measurements below come from the supplied step-200 returns, not from new GPU runs. The workspace ran only CPU fixtures on trinity-1-18, with CUDA hidden, nice 10, and eight torch/BLAS threads.

## Measured profile

'''+ '\n'.join(rows)+'''

“Total” counts every returned token, including injected tool responses and budget-forced tokens. “Ordinary” is the existing `decode_budget.ordinary_sampled_tokens` field. Distance averages 115.00 injected tool tokens/item and 0.20 budget-forced tokens/item. Counts, mean, median, and p90 for total, ordinary, injected, prompt, and non-tool tokens are retained in `profile.json`; p90 interpolates at `(N−1)×0.9`.

The G3T column measures the existing `g3t_s` wrapper, including cache lookup/restore or a fresh tower call. It is **not total tower time**: SAM encoding/detection and scale/geometry have no independent timers. Room's zero comes from its no-call traces and the lazy source path; there is no room `g3t_s` timer. The factory-load window includes processor/model restoration and setup. It excludes deferred G3T/SAM loading inside item generation. A4 reuses one generator across types; the recorded reused-load durations are below 2 microseconds, not fresh model loads.

'''
for package,data in p['packages'].items():
    report+=f"{package} sources: "+', '.join(link(kind,Path(d['source']),1) for kind,d in data['types'].items())+'. Each adjacent `timings.jsonl` supplies the factory-load window.\n\n'
report+='''A4 takes **7351.824 s** from worker start to exit. Its item windows sum to **7224.888 s**, its initial factory load takes **75.446 s**, and **1.729 s** remains inside the type timers for journaling/control. Another **49.761 s** lies outside those timers. B5 takes **645.735 s**, with **528.164 s** in items, **78.961 s** in factory loading, **5.593 s** inside the journal window, and **33.017 s** outside it. These residuals are measured wall-time accounting, not measured GPU idle time.

One distance item, `vsi590k_042644`, takes **648.397 s** for 2056 tokens, including **647.465 s** in `total_s`. Nine other distance items with at least 2000 tokens have a **72.502 s median**. Ten such long items consume **1308.680 s**, or about 37% of distance item time. The mean without the largest outlier is **19.406 s/item**, but the forecast retains the observed outlier. The logs do not distinguish scheduling pauses, throttling, kernel stalls, or actual GPU work; no cause or idle percentage is assigned.

Distance has 88 routed items with exactly two served ground calls and one served gap call each, and 62 items with no tool calls. The respective mean item times are **21.997 s** and **25.875 s**; the latter group's median is only **4.997 s**. The long direct traces explain why its mean is much higher. Every camera item serves one move/turn call; rooms serve none.

## Reuse, batching, and parity decisions

'''
memo=['| Type | G3T accesses | Fresh misses | Reused hits | Mean prefill s | Outer item minus core s |',
      '|---|---:|---:|---:|---:|---:|']
for kind,d in p['packages']['A4']['types'].items():
    memo.append(f"| {kind} | {d['timed_g3t_accesses']} | {d['memo']['misses']} | {d['memo']['hits']} | {d['timings']['prefill_s']['mean']:.3f} | {d['outer_minus_core_s']['mean']:.3f} |")
report+='\n'.join(memo)+'''

A4 already enables G3T memoization: **461 hits and 77 misses over 538 accesses**, ending at **128,553,354 retained payload bytes**. That gain cannot be counted again. The source permits one G3T access per routed item regardless of its number of tool calls. It also retains SAM image features and raw detections within each individual item, but not across items under the supplied `perception_memo_modules=['g3t']` setting. From the 88 served distance traces and the source, **88 SAM clip encodes and 176 raw-name detections are inferred**, not independently measured.

The new caches retain only these functions, within one immutable model/processor lifetime:

| Component | Inputs that determine the cached value | What still runs per item |
|---|---|---|
| Existing G3T memo | Pinned weights/config, device, precision, depth chunk size, ordered decoded pixel bytes/modes/sizes, dense indices, anchor indices and slots | Own-prefill scale/gravity, geometry construction, response formatting |
| New video processor cache | Complete ordered video arrays, metadata including FPS/frame indices, processor configuration and every call kwarg | Prompt text, tokenization, carriers, masks, positions, frame-file reads |
| New Qwen vision cache | Actual processed pixels and grids/kwargs, vision configuration, parameter/buffer versions, device/dtype and autocast state | Every language-model prefill/decode, heads and tools; inner/global hooks force a fresh vision call |
| New SAM feature cache | Pinned SAM files, ordered pixels and frame indices/slots, device/precision and native image batching settings | Geometry-dependent lifting, linking, selector logits and responses |
| New SAM raw detections | SAM feature identity plus normalized object name and retention thresholds | The current read's downstream geometry and selector work |

The processor/vision/SAM caches share a bounded host LRU, defaulting to 4 GiB only when a cache is enabled. Hits return independent storage. Oversized values are not retained. The cache lifetime ends with the generator/process; forked processes reset it. It never keys by a scene name alone and never caches a whole prompt, recurrent/KV state, own-depth scale, or a tool response. The new SAM cache refuses simultaneous use of the existing SAM memo policy so it cannot bypass that policy's verification.

'''
report+='Purity/source evidence: '+', '.join([
    link('G3T key and frozen execution',A/'b/e2e_reader/real.py',32),
    link('pixel/index identity',A/'b/e2e_reader/perception_memo.py',186),
    link('current-prefill scale',A/'b/e2e_reader/stage1.py',45),
    link('SAM name-dependent detection',A/'b/e2e_reader/stage1.py',83),
    link('SAM image encoding',A/'tree/student_pilot/sam3_tower.py',196),
    link('video processor boundary',P/'transformers/processing_utils.py',769),
    link('Qwen vision forward',P/'transformers/models/qwen3_5/modeling_qwen3_5.py',1078)])+'.\n\n'
report+='''**Batching is not an accepted byte-preserving optimization.** Sorting by prompt length can reduce KV padding, but does not establish bit equality. The deployed hook reader accepts one row, and consumes forced response tokens one at a time. The separate trainer batch decoder serializes video prefills, left-pads full-attention KV, and concatenates recurrent states; it is not wired to this reader's per-item hook/server lifecycle. Batched matrix operations and SDPA backend selection need not reproduce unbatched bits. Qwen's linear attention also dispatches differently for cached single-token and chunked input, with explicit padding-mask handling.

No nonzero answer or trace tolerance is accepted. Near-tied logits can turn a small floating-point difference into a different greedy token, then a different tool call and answer. A numerical logit tolerance alone cannot bound that change. A future batched implementation must pass the same exact trace gate; it is not included in these patches. Local torch/transformers file:line evidence and official documentation links are in `FRAMEWORK_EVIDENCE.md`.

The scorer extracts the text after `</think>`, normalizes its answer, and uses exact choice matching or numeric MRA. A changed number may remain in the same MRA bins, so equal scores cannot certify unchanged answers. The parity comparator therefore compares raw generated text and all token/call/response/head/scale/finish/score values, not only the aggregate score. See `tree/evalpath/run.py:70` and `tree/evalpath/official.py:269` in A4/src.

## Patches and CPU validation

Apply from a fresh copy of **A4/src**, with `patch --batch --fuzz=0 -p1`. `patches/MANIFEST.json` gives before/after hashes. Both diffs also applied without fuzz to the corresponding files extracted from B5's package. B5 has the same reader files but an extra launcher type-binding field; that field remains intact.

| Patch | Explicit opt-in | Default behavior |
|---|---|---|
| `patches/01_bounded_read_caches.diff` | Settings `read_processor_cache`, `read_vision_cache`, `read_sam_cache`: `on` | Each defaults to `off`; original component calls and serial decode remain |
| `patches/02_atomic_scene_shards.diff` | `--atomic-journal`, `--scene-shards`; array worker also requires `--enable-array` | Existing JSONL journal and modulo item sharding remain |

**24 CPU tests pass:** eleven cache tests, nine journal tests, and four comparator tests. The 50-read stub test compares the original reader, patched default-OFF reader, and cache-ON reader byte for byte after removing clock/cache telemetry; vision executions fall from 50 to five in that fixture. A tiny randomly initialized instance of the installed Qwen vision model also passes exact CPU caching comparison. These are correctness fixtures, not production speed measurements. The CPU environment lacks torchvision v2, so its native video-processor test covers packing/metadata with resize/RGB conversion/normalization disabled; the GPU kit must cover the unchanged production preprocessing.

All tests use the requested interpreter, isolated mode, CUDA hidden, nice 10, and eight threads. Reproduce the complete check with:

```bash
cd /scratch/jjyeung/orch_n30/so_read
bash work/cpu.sh work/run_checks.py
```

The individual commands below inherit those settings from `work/cpu.sh`. Their exact captured outputs follow.

'''
for result in checks['results']:
    path=result['command'][-1]
    command=(f"READ_INPUT_SRC={A} " if result['name']!='kit' else f"READ_TEST_TMP={L}/work/test-artifacts ")+f"bash {L}/work/cpu.sh {path}"
    report+='```bash\n'+command+'\n```\n\n```text\n'+(L/'out/checks'/result['output']).read_text()+'```\n\n'
report+=f'''The syntax/default-off checks and zero-fuzz patch application also pass. `checks/RESULTS.json` records torch **{checks['torch']}**, transformers **{checks['transformers']}**, an empty `CUDA_VISIBLE_DEVICES`, and eight torch threads. The measured maximum child RSS is **{checks['max_child_rss_bytes']:,} bytes**; the workspace occupies **{checks['workspace_bytes']:,} bytes** at validation, before these reports. No GPU job or model API ran.

## Requeue and return contract

The original reader skips completed `(id, arm, mode)` tuples but rejects an incomplete JSONL tail. The opt-in journal writes a checksummed item file, fsyncs it, atomically renames it, and fsyncs the directory **before** appending the ordinary JSONL projection. A requeued task acquires the same writer lock, validates the same export/source/settings/item/shard binding, reads the committed set, preserves divergent JSONL bytes, and rebuilds the projection. Interrupted temporary files never count as committed items. A kill before commit can repeat that item's computation; a kill after commit cannot duplicate its output. The CPU test interrupts between the durable commit and JSONL completion and confirms that all five items appear exactly once, with only the three uncommitted items generated on resume.

Whole-scene assignment sorts physical rooms by descending item count and assigns each to the least-loaded shard. Membership is disjoint and complete, and order within each shard follows the manifest. Keep the count fixed across requeues. Empty type shards are supported. Count balancing is not latency balancing; long traces can still produce stragglers.

`h1eval.h10.merge_read` checks the complete expected ID set, per-shard ownership, type/room, checksums, export/source/settings bindings and duplicates. It emits manifest-ordered canonical semantic records and a deterministic gzip/tar archive. CPU single-shard and three-shard archives match byte for byte. The optional `--shards 4` GPU kit checks the same property on real outputs without submitting jobs.

The equality contract excludes timing, runtime audit paths/counters, and cache telemetry; audit violations still fail. Those fields and environment bindings remain in the raw journals and `PROVENANCE.json`. **A raw Orchard transport archive or raw JSONL line containing timestamps and timings cannot be byte-identical across executions.** The deterministic answer/trace return is explicitly a new content artifact, not a claim that the original transport envelopes are identical.

`kit_parity50/array_preempt.template.sh` requests the user-specified preempt partition, REQUEUE, a two-day limit, one GPU per task and four tasks. It is an unsubmitted template. Persistent shared journals, stable staged input paths, real filesystem fsync/locking behavior, allocation policy, and final Orchard publishing need an orchestrator integration check. Status 75 denotes incomplete work; the template has no retry loop.

## Forecast and adoption checks

**Estimated, not measured for package D or step 600:** `580 × 23.599762 + 75.446133 + 49.761372 = 13813.070 s`, or **3 h 50 min 13 s**. This exceeds a 3 h 30 min request even before its stop/return margins. The user-provided 12-hour general limit is distinct from that shorter request, and general is reserved for the step-400 work.

With the same per-item cost and perfectly balanced, simultaneous starts, two scene shards estimate **6969.139 s (1 h 56 min 9 s)**; four estimate **3547.173 s (59 min 7 s)**. These estimates charge each task the observed load/startup allowance and exclude queue delay, staging variation, preemption/reloads, and imbalance. They are elapsed-read estimates, not per-GPU compute savings.

For processor/vision caching, **1.596 s/distance item is an optimistic exposed-window ceiling**, equal to all outer-minus-core time plus all prefill time. It is not a predicted saving: file reads, tokenization, language prefill, hashing and copies remain. Even eliminating that entire window would leave about **22.004 s/item** before any SAM gain. SAM's separate cost and reusable-name frequency across the full 580-item set are unmeasured. The scheduling budget therefore remains **23.60 s/item** until the parity kit demonstrates a net gain beyond OFF/OFF timing variation.

Adopt at **step 600 at the earliest**: first the atomic whole-scene preempt split after persistence/requeue/merge checks; then only caches that pass zero-byte-difference OFF/OFF, OFF/ON and single/sharded gates on the fixed 50-item sample and show useful hits, bounded memory, and lower item time. Keep greedy decoding, dtype, frame layout, sampling/stop rules, and response formatting unchanged. Do not alter step-400 deliveries.

## Failure detection and work not run

| Risk | Detection/action |
|---|---|
| Cache omits a dependency or GPU fresh calls are not deterministic | Exact text/token/call/head comparison; repeat OFF first; leave the affected switch OFF |
| Cache hashing/copying costs more than recomputation, or entries churn | Item time, hit/miss/eviction/oversize counters and host/GPU memory receipts; give no speed credit |
| Geometry injection or intermediate feature hooks would be skipped | Vision cache bypasses child/global hooks; the current read computes geometry/scale/selector work |
| Wrong checkpoint, settings, membership or shard count on requeue | Existing immutable binding comparison refuses resume |
| Partial item write or partial JSONL projection | Incomplete temporary file is ignored; committed checksum is verified; torn projection is preserved and rebuilt |
| Missing/duplicate shard output or corrupted committed record | Merger rejects the return |
| Shared filesystem lacks the assumed durability or journals live on a lost node | Run a real persistent-storage preemption test before array adoption; this was not simulated as a power-loss test |
| Source patch applied to a sealed package without rebuilding pins | Package dry checks reject hashes; rebuild payload/pins and rerun `dry2`/`dryres2` for the actual deployment |

GPU OFF/ON and multi-shard parity, H100/CUDA timings, production preprocessing, actual preemption, and production host-memory fit are **not run**, as required. There is no batch-generation patch, no numerical tolerance waiver, no modified checkpoint, no edited input tree, and no submitted or published Orchard job/return. The existing archive builders were reviewed but not executed: they depend on Orchard inputs and rebinding alone cannot install a source change. No skill requested an approval gate; no borderline revision-history sentence is retained.
'''
(L/'out/REPORT.md').write_text(report)

note='''At step 600, prioritize a preempt array with durable per-item journals. Enable component caches only after the unrun GPU parity kit passes. Keep step-400 deliveries unchanged.

**Measured step-200 baseline:** distance averages **23.60 s/item** (median **18.28**, p90 **29.18**). A4 loads one generator in **75.45 s**, already reuses it across all five types, and already caches G3T. G3T contributes **2.00 s/distance item**; SAM has no separate timer. One 2056-token item takes **648.40 s**. Its cause is unknown, so the forecast retains it.

| Scenario | Expected distance s/item for budgeting | Estimated 580-item elapsed read |
|---|---:|---:|
| One GPU, existing path | 23.60 | 3 h 50 min |
| Two concurrent, balanced scene shards | 23.60 per GPU | 1 h 56 min |
| Four concurrent, balanced scene shards | 23.60 per GPU | 59 min |
| Processor/vision/SAM caches | Keep 23.60 until measured | No saving credited yet |

The estimates use `580 × 23.599762 / shards + 75.446133 + 49.761372`. They exclude queue delay, staging changes, preemptions/reloads, and imbalance. A 3 h 30 min request is too short at this mean, even before stop margins. The partition limits and general-partition reservation are the dispatch's supplied constraints.

Two default-off patches are ready in `out/patches/`. The cache patch reuses video-processor outputs, frozen Qwen vision outputs, SAM image features and raw name-conditioned detections. It preserves serial decoding and recomputes each read's geometry, scale, selectors and tool responses. Its shared host cache defaults to a 4 GiB cap when enabled. The journal patch adds atomic item commits, disjoint whole-scene shards, and checked deterministic merging. Both patches apply without fuzz to A4 and B5; **24 CPU tests pass**.

The fixed `out/kit_parity50/` sample contains ten items per type and twelve native captures. On an assigned Orchard GPU, run OFF/OFF-repeat/ON and the optional four-shard check using its README. Require identical generated text, tokens, calls/responses, heads, scale, finish, scores and merged answer/trace archive bytes. Check useful cache hits, lower item time beyond baseline variation, and host/GPU memory. The sample stresses reuse; it does not establish representative 580-item throughput.

Before using preempt, prove that persistent journals survive a real requeue, then verify all expected IDs occur exactly once. An unfinished item may recompute; a committed item must not. Keep the shard count, checkpoint, source and settings fixed. The array template does not submit or publish anything; the orchestrator must integrate approved staging, resource policy and the return transport.

Runtime timings, audit paths and cache counters remain separate from the deterministic answer/trace return. Full raw transport archives cannot match across runs. Batched greedy decoding has no bit-equality guarantee and is not included. **GPU parity, GPU speedups, real requeue behavior and production memory fit remain unmeasured.** Rebuild package pins and run the supplied package dry checks before step-600 deployment.

Details and exact test outputs: `out/REPORT.md`; measured data: `out/profile.csv` and `out/profile.json`.
'''
(L/'out/NOTE_FOR_CONT_OPS.md').write_text(note)
print('Wrote REPORT.md and NOTE_FOR_CONT_OPS.md; note words:',len(note.split()))
