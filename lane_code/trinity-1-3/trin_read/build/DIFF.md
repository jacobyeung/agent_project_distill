# Trinity wrapper differences

No file under `kit_src/` is modified. The accepted bootstrap is decoded without execution and retains its exact CONFIG, payload, launcher, and review bytes. Existing stage files remain intact; `root/trinity_runner/` carries the wrapper modules and their manifest. The staged reader, worker, r3/r4/r5 adapters, and proof/pull scripts remain unchanged. All executable additions, tests, and operator documentation are listed line by line below; the ledger itself and generated evidence are excluded to avoid self-reference. An absent old line means a new file, not a replacement inside the kit.

PATH/ENV means relocation, local environment, or stdlib host compatibility. BEYOND means added behavior, including observers, guards, tests, and documentation. BEYOND changes are confined to the requested wrapper boundary; none changes decoding, prompts, frame selection rules, scoring, or model settings.

## Behavioral mapping

| Class | Kit source / old behavior | Trinity source / new behavior |
|---|---|---|
| PATH/ENV | `launcher/orchard_launcher.py:168`, `prepare()` constructs a bootstrap bundle. | `trinity_read.py`, `reference_bundle()` decodes and authenticates the accepted job 169991 bundle as data. It preserves all bootstrap bytes. |
| BEYOND | `launcher/orchard_stage.py:208`, `stage()` runs a monolithic fetch/extract sequence. | `trinity_read.py`, `stage()` consumes only complete local receipt-bearing pieces, records completion, locks staging, and refuses partial or unrecorded destinations. |
| PATH/ENV | `launcher/orchard_stage.py:19`, runtime absolute-link allowlist; `unpack(..., links=True)`. | The same imported extraction functions and absolute-link allowlist are used without changes. Python 3.6 gets a host-only `Path.is_relative_to` compatibility method. |
| BEYOND | `launcher/orchard_stage.py`, cloud export transport and `stage_videos()`. | `verify_export_local()` hashes the already-staged full-weight export. No export fetch, video stage, official row load, or cloud process exists in the runner. |
| BEYOND | `launcher/orchard_stage.py`, base manifest rows are checked against extracted inventory. | The same rows and hashes must match, and the entire inventory must match, so unlisted extra files also fail. |
| PATH/ENV | `launcher/orchard_job.py`, namespace maps Orchard logical paths and the external store. | `namespace()` maps root/sj, root/fsw, root/m/ap, the UV interpreter, root/bootstrap, private temp/cache/home, and the local store. |
| BEYOND | `proof/pull.py:20`, read an existing k6tk store. | `frames()` adds a verified append-only k6tk store builder. The existing puller is unchanged. CPU namespaces hide GPU devices; all namespaces disable networking. |
| BEYOND | `proof/phase_b.py:126`, phase B selects the first 20 main tasks. | `namespace_worker.bind_plan()` uses the same dry bind, select_tasks, sort, and payload functions for main/away/forward and named sets. |
| BEYOND | `reader/evaluator/worker.py:62`, sort tasks and apply smoke_items. | `namespace_worker.install_filter()` filters the loader and imported aliases in memory. Dataset bytes and pins remain unchanged. The request binding records selected IDs and wrapper SHA. |
| BEYOND | `launcher/orchard_job.py`, H100-specific card check and Slurm job identity. | `check_card()` requires one selected card, >=40 GiB, <100 MiB used, and no compute process. The operator token supplies the job-identity environment field. |
| BEYOND | `launcher/orchard_job.py`, trace `reader/chain.py` through the staged interpreter. | `launch()` traces unchanged `proof/phase_b.py` directly for proof, or the production wrapper for read, under vnice. No phase A or official item runs. |
| BEYOND | The kit checks free staging space; its reader copies both models into each packet. | `read_space()` preserves the 200 GiB floor with a reserve for both copied models, frames, and metadata/logs. |
| BEYOND | `proof/phase_b.py`, accepted per-arm equality comparison. | `compare_tokens.py` adds divergence indices, exact equality/means, explicit missing evidence, worker/meta latency, and a 1 s sampled card-memory peak. |
| BEYOND | The kit has no Trinity one-use command interface or receipt-based piece retries. | The CLI enforces path/family/ID/token boundaries, refuses existing packets, prints missing frame SHAs before GPU admission, and records execution evidence. It never retries jobs. |

## Unchanged reader settings

`max_model_len=49152`; greedy temperature 0; thinking cap 16384; GPU memory utilization 0.90; max sequences 32; inflight 16; max batched tokens 8192; tensor parallel size 1; seed 17; prefix caching disabled; budget answer cap 64. These values come from unchanged reader code and binds. The public direct wrapper hash is `d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a`. No worker or direct source patch exists.

Per-run CONFIG copies change the token, run/output paths, and plan hash. Production copies additionally bind the requested artifact path/hash/step. Proof retains the accepted step-544 artifact and all reader settings. Production request changes are build_only/export-verification, subset smoke_items, selection evidence, output paths inherited from bind, and the resulting binding hash.

## OPEN

- No real Ada proof ran. The unchanged 49,152-token context, 16,384-token thinking cap, 0.90 GPU memory setting, concurrency, and native BF16 weights may fail to fit or run on the 48 GB card. Report the failure; do not reduce settings.
- H100 token parity does not establish Ada token parity. Require the new PROOF.json before claiming equality.
- STAGING.json records incomplete runtime, base, and reader-payload pieces. Export/base compatibility, driver compatibility, and the complete namespace reader remain unvalidated. The host bwrap 0.4.0 probe reaches namespace setup, where this agent sandbox denies the NETLINK_ROUTE socket; full namespace execution remains unverified here.
- STAGING.json records bootstrap, camera (a0), bwrap, and export as complete. The camera receipt lacks extracted-file hashes; selfcheck reports it as unverifiable until an authorized stage reads the authenticated camera archive to add its inventory. No input tar was consumed in this follow-up.
- Runtime throughput and sampled card memory remain unknown. Budget reuse has no new generation latency; absent journals remain null. A 1 s sampler cannot establish a true instantaneous peak.
- Interrupted stages and store-index appends require manual inspection. Concurrent disk users can consume the reserved free-space margin. No automatic recovery or cleanup runs.

## Shared memory, yielding, and portability

| Class | Boundary | Behavior |
|---|---|---|
| PATH/ENV | `shm_directory`, `namespace`, `environment`, `cpu_need`, and proof/read options | Create the selected private shared-memory directory; bind it after the GPU `/dev` bind; keep temp/home and all seven requested cache/environment paths under root. CPU planning honors the same `--shm`. |
| BEYOND | `host_shm_ours`, launch evidence, and `compare_tokens.write_report` | Record shallow UID-owned host `/dev/shm` listings before and after execution in EXIT/PROOF evidence. Do not delete or attribute entries. |
| BEYOND | `yield_pattern`, `run_reader`, and `stop_group` | Poll a local nonrecursive glob immediately and every 30 seconds, create a dedicated reader process group, send TERM, wait 60 seconds without reaping its leader, then KILL only that group. A yield records return code 75 and makes the CLI fail. |
| BEYOND | `disk_listing` and `YIELD.json` | Record the matched file, time, process group, and run/model paths and byte sizes after termination. Do not follow symlinks, read model contents, remove leftovers, or retry. |
| PATH/ENV | `install_runner`, `package`, `namespace`, and `kit_stage` fallback | Carry three wrapper modules under root, bind those modules, use staged parity references, and load the staged bootstrap's stage helper when kit_src is absent. Runtime root copies need the three pinned build stub files when the llguidance overlay is enabled; source checkouts are unnecessary. |
| BEYOND | Stage member inventories and camera receipt enrichment | Retain runtime/camera/payload member size/hash inventories for cheap checks. An authorized stage can recover a legacy camera inventory from the authenticated archive without re-extraction. This build leaves the partial stage untouched. |
| BEYOND | `cheap_verify`, `config_audit`, and `selfcheck --root R` | Verify available piece sizes, SHA256 for files <=1 MiB, bootstrap/bwrap hashes, and wrapper pins; audit CONFIG values and symlink targets; execute a GPU-free bwrap `/bin/true` probe. Missing integrity evidence or active path escapes prevent acceptance; authenticated pinned CONFIG evidence is informational. |
| BEYOND | Portability evidence | SELF_CHECK_BWRAP.json reports 153 informational `pinned_evidence` values and eight root-backed namespace aliases. The CONFIG audit passes. Five missing pieces, the camera inventory gap, and sandbox namespace restrictions still prevent complete acceptance. |
| BEYOND | README model retention note | Neither `--keep-models` nor `--no-keep-models` is implemented. Reader model-copy behavior stays unchanged; each packet needs roughly 36 GiB for its two models, plus frames, caches, and logs, while preserving the 200 GiB floor. |
| BEYOND | Tests and documentation | The CPU tests cover live child-group TERM/KILL tests, mocked proof/read yields, cheap-integrity failures, private shm/cache bindings, portability findings, and root-only wrapper imports. README and REPORT_ADDENDUM.md state the limits. |

CONFIG auditing distinguishes pinned accepted evidence from active paths. The accepted bootstrap SHA256 authenticates the classification template; active paths receive normalized namespace mapping and symlink escape checks. No source, archive, or model-content scan is claimed. A successful cross-node reader run remains unproven.

## Host bwrap and CONFIG classification

| Class | Boundary | Behavior |
|---|---|---|
| PATH/ENV | `--bwrap PATH` on proof, read, need, selfcheck; namespace and preflight plumbing | Execute `/usr/bin/bwrap` by default or the selected host executable. Preserve the staged pinned Orchard binary as authenticated evidence and reject attempts to execute it, including links and byte-identical copies. Root carries the updated wrapper modules and manifest; STAGING pieces remain untouched. |
| BEYOND | COMMAND.json, EXIT.json, PROOF.json, CPU planning and selfcheck evidence | Record the resolved executable path, SHA256, exact `--version` stdout and stderr. COMMAND.json is an object with `argv` and `bwrap`. Each CPU family run records COMMAND/EXIT under root/needs; proof carries the same identity through reporting, including failed/yielded runs. |
| BEYOND | CONFIG findings | Report unchanged, authenticated accepted literals as `pinned_evidence` when unused as active paths. These findings do not fail. Active namespace aliases map into root; outside paths, traversal, and symlink escapes fail. |
| PATH/ENV | bubblewrap 0.4.0 flags | No unsupported flags or substitutions were found. CPU probes include every runner flag: `--unshare-net`, `--ro-bind`, `--symlink`, `--dev`, `--dev-bind`, `--bind`, `--proc`, `--dir`, `--die-with-parent`, `--chdir`; selfcheck additionally uses `--tmpfs`. Device binding uses only `/dev/null` in the probe. |
| BEYOND | Probe limits | BWRAP_FLAGS.json verifies coverage and the local 0.4.0 help lists every flag. The combined flag-set `/bin/true` probe passes option parsing but exits 1 on the sandbox's NETLINK_ROUTE denial. No namespace-isolation bypass or GPU probe runs; successful namespace execution is not claimed. |
| BEYOND | Tests and documentation | The CPU tests cover custom/default executable selection, staged-binary refusal, failure/yield evidence, accepted-evidence classification, and active path escapes. README states the evidence schema and remaining selfcheck limits. |

## llguidance load-time overlay and import probe

| Class | Boundary | Behavior |
|---|---|---|
| BEYOND | `llguidance_evidence`, `namespace`, and `--llguidance-stub` / `--no-llguidance-stub` | Default to the three pinned v2 stub files for proof/read/need/probe. Verify hashes and exact inventory before a read-only package overlay after the root binds. Require the destination directory to exist. Trinity glibc 2.28 cannot load the native llguidance GLIBC_2.30 dependency. This changes package loading; staged bytes remain unchanged. Guidance use raises explicitly. |
| BEYOND | COMMAND/EXIT/PROOF, CONFIG/SPEC, and CPU NEED evidence | Record overlay enablement, source path, destination, three SHA256 pins, satisfied names, version, and verification status. Generation logs count imports and calls; calls, malformed logs, or missing enabled-stub import evidence fail the audit. Write packet SPEC before execution; retain overlay identity on failed and yielded runs. CONFIG auditing authenticates the enabled overlay source. |
| BEYOND | `probe --root R` | Use the staged vLLM Python with the proof namespace, environment, overlay, and shm, with CPU-only devices. Import vLLM/torch/transformers, LLM, qwen3_5, engine core, and gpu_model_runner; report Python and package versions, glibc, and cryptography import presence. Invoke the installed GuidanceBackend.compile_grammar on CPU and require a stub RuntimeError plus its logged call. Report the exact blocker if the check cannot execute. Write PROBE.json under root/runs/probe_<utc>, including refusal/failure evidence. Require staged runtime_0; never consume or wait for arriving tars. |
| BEYOND | Tests and documentation | Cover overlay argv/order, each pin mismatch, missing targets, disable flags, run/packet/proof evidence, import reporting, missing runtime_0, namespace failure, and timeout. Real GPU execution and token parity remain untested. Root copies need the pinned build stub at the documented absolute path when enabled. |

## Stub audit, sandbox receipt, and repeat proof

| Class | Boundary | Behavior |
|---|---|---|
| BEYOND | `build/llg_stub/llguidance` | Log atomic JSONL import events with module/PID and call events with names. Every class construction, unknown module/class attribute, and hf/torch submodule import logs before raising. Keep `work/llg_stub` as the v1 record. |
| PATH/ENV | `LLG_STUB_LOG` | Give each generation run a shared root-bound log path inherited by engines. Keep the CPU probe's deliberate calls in its own log. |
| BEYOND | `SANDBOX.json` and packet evidence | Record bwrap identity, every bind and mode, special mounts, overlay hashes, host/namespace glibc, driver-query output, host driver library paths/sizes, namespace loader resolutions, and versions from the associated CPU probe. Retain explicit unknowns on preflight refusal. Copy SANDBOX and LLGUIDANCE evidence into phase-B packets. |
| BEYOND | `proof --repeat 2` | Run unchanged phase B twice in sequence on the same card with fresh `_r1`/`_r2` directories. Compare both against accepted results and each other, including item token IDs/divergence and arm answers/scores. Execution or audit failure stops the sequence without retry. |
| BEYOND | Validation scope | CPU fixtures cover logging, actual installed guidance-method source with dependency fixtures, receipts, failure gating, and repeated comparisons. The real probe refuses missing runtime_0/uv Python. A real namespace guidance test and GPU parity remain unverified. |

## Added-file ledger

Each row gives the current file:line, classification, old line, and exact new line encoded as a JSON string. Every line is an addition relative to the unchanged kit. The ledger and generated test/check evidence are excluded to avoid self-reference.

| File:line | Class | Old | New |
|---|---|---|---|
| trinity_read.py:1 | PATH/ENV | ∅ (added file) | <code>&quot;#!/usr/bin/env python3&quot;</code> |
| trinity_read.py:2 | PATH/ENV | ∅ (added file) | <code>&quot;\&quot;\&quot;\&quot;Local-only Trinity staging and launch boundary for the unchanged dev-S1 reader.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:3 | PATH/ENV | ∅ (added file) | <code>&quot;import argparse&quot;</code> |
| trinity_read.py:4 | PATH/ENV | ∅ (added file) | <code>&quot;import ast&quot;</code> |
| trinity_read.py:5 | PATH/ENV | ∅ (added file) | <code>&quot;import base64&quot;</code> |
| trinity_read.py:6 | PATH/ENV | ∅ (added file) | <code>&quot;import contextlib&quot;</code> |
| trinity_read.py:7 | PATH/ENV | ∅ (added file) | <code>&quot;import csv&quot;</code> |
| trinity_read.py:8 | BEYOND | ∅ (added file) | <code>&quot;import datetime&quot;</code> |
| trinity_read.py:9 | PATH/ENV | ∅ (added file) | <code>&quot;import fcntl&quot;</code> |
| trinity_read.py:10 | PATH/ENV | ∅ (added file) | <code>&quot;import glob&quot;</code> |
| trinity_read.py:11 | PATH/ENV | ∅ (added file) | <code>&quot;import gzip&quot;</code> |
| trinity_read.py:12 | PATH/ENV | ∅ (added file) | <code>&quot;import hashlib&quot;</code> |
| trinity_read.py:13 | PATH/ENV | ∅ (added file) | <code>&quot;import io&quot;</code> |
| trinity_read.py:14 | PATH/ENV | ∅ (added file) | <code>&quot;import json&quot;</code> |
| trinity_read.py:15 | PATH/ENV | ∅ (added file) | <code>&quot;import os&quot;</code> |
| trinity_read.py:16 | PATH/ENV | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| trinity_read.py:17 | PATH/ENV | ∅ (added file) | <code>&quot;import re&quot;</code> |
| trinity_read.py:18 | PATH/ENV | ∅ (added file) | <code>&quot;import shlex&quot;</code> |
| trinity_read.py:19 | PATH/ENV | ∅ (added file) | <code>&quot;import shutil&quot;</code> |
| trinity_read.py:20 | PATH/ENV | ∅ (added file) | <code>&quot;import signal&quot;</code> |
| trinity_read.py:21 | PATH/ENV | ∅ (added file) | <code>&quot;import stat&quot;</code> |
| trinity_read.py:22 | PATH/ENV | ∅ (added file) | <code>&quot;import subprocess&quot;</code> |
| trinity_read.py:23 | PATH/ENV | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| trinity_read.py:24 | PATH/ENV | ∅ (added file) | <code>&quot;import tarfile&quot;</code> |
| trinity_read.py:25 | PATH/ENV | ∅ (added file) | <code>&quot;import threading&quot;</code> |
| trinity_read.py:26 | PATH/ENV | ∅ (added file) | <code>&quot;import time&quot;</code> |
| trinity_read.py:27 | PATH/ENV | ∅ (added file) | <code>&quot;import uuid&quot;</code> |
| trinity_read.py:28 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:29 | PATH/ENV | ∅ (added file) | <code>&quot;sys.dont_write_bytecode = True&quot;</code> |
| trinity_read.py:30 | PATH/ENV | ∅ (added file) | <code>&quot;BUILD = Path(__file__).resolve().parent&quot;</code> |
| trinity_read.py:31 | PATH/ENV | ∅ (added file) | <code>&quot;AREA = Path(&#x27;/scratch/jjyeung/orch_n30/trin_read&#x27;)&quot;</code> |
| trinity_read.py:32 | PATH/ENV | ∅ (added file) | <code>&quot;DEFAULT_ROOT = AREA/&#x27;root&#x27;&quot;</code> |
| trinity_read.py:33 | PATH/ENV | ∅ (added file) | <code>&quot;KIT = Path(&#x27;/trinity-kit&#x27;) if Path(&#x27;/trinity-kit&#x27;).exists() else AREA/&#x27;kit_src&#x27;&quot;</code> |
| trinity_read.py:34 | PATH/ENV | ∅ (added file) | <code>&quot;REFERENCE = Path(&#x27;/scratch/jjyeung/orch_n30/evalx27/work/kit/build/pb59bef09f3&#x27;)&quot;</code> |
| trinity_read.py:35 | PATH/ENV | ∅ (added file) | <code>&quot;STORE = &#x27;/project/community/jjyeung/cp4tk_fr/k6tk&#x27;&quot;</code> |
| trinity_read.py:36 | PATH/ENV | ∅ (added file) | <code>&quot;VNICE = &#x27;/data3/shared/scripts/vnice/vnice.sh&#x27;&quot;</code> |
| trinity_read.py:37 | PATH/ENV | ∅ (added file) | <code>&quot;DEFAULT_BWRAP = &#x27;/usr/bin/bwrap&#x27;&quot;</code> |
| trinity_read.py:38 | BEYOND | ∅ (added file) | <code>&quot;PINNED_BWRAP_SHA256 = &#x27;e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71&#x27;&quot;</code> |
| trinity_read.py:39 | BEYOND | ∅ (added file) | <code>&quot;ACCEPTED_CONFIG_SHA256 = &#x27;a5d934125b00400916e2660c8721beb7d88dcf02f9e6cfeebbb97ae136920dfa&#x27;&quot;</code> |
| trinity_read.py:40 | PATH/ENV | ∅ (added file) | <code>&quot;FAMILIES = (&#x27;main&#x27;, &#x27;away&#x27;, &#x27;forward&#x27;)&quot;</code> |
| trinity_read.py:41 | PATH/ENV | ∅ (added file) | <code>&quot;REQUIRED_PIECES = {&#x27;bootstrap&#x27;, &#x27;runtime_0&#x27;, &#x27;runtime_1&#x27;, &#x27;runtime_2&#x27;, &#x27;a0&#x27;, &#x27;bwrap&#x27;, &#x27;reader_payload&#x27;, &#x27;base&#x27;, &#x27;export&#x27;}&quot;</code> |
| trinity_read.py:42 | PATH/ENV | ∅ (added file) | <code>&quot;SJ = Path(&#x27;/scratch/jjyeung&#x27;)&quot;</code> |
| trinity_read.py:43 | PATH/ENV | ∅ (added file) | <code>&quot;FSW = Path(&#x27;/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung&#x27;)&quot;</code> |
| trinity_read.py:44 | PATH/ENV | ∅ (added file) | <code>&quot;AP = Path(&#x27;/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap&#x27;)&quot;</code> |
| trinity_read.py:45 | BEYOND | ∅ (added file) | <code>&quot;VLLM_ENV = AP/&#x27;19252904/e&#x27;&quot;</code> |
| trinity_read.py:46 | BEYOND | ∅ (added file) | <code>&quot;LLG_STUB = AREA/&#x27;build/llg_stub/llguidance&#x27;&quot;</code> |
| trinity_read.py:47 | BEYOND | ∅ (added file) | <code>&quot;LLG_TARGET = VLLM_ENV/&#x27;lib/python3.12/site-packages/llguidance&#x27;&quot;</code> |
| trinity_read.py:48 | BEYOND | ∅ (added file) | <code>&quot;LLG_PINS = {&quot;</code> |
| trinity_read.py:49 | BEYOND | ∅ (added file) | <code>&quot;    &#x27;__init__.py&#x27;: &#x27;01fc27773baceee9eb87ff76cec70d8ce761a8ddef6c73055224e77a70023572&#x27;,&quot;</code> |
| trinity_read.py:50 | BEYOND | ∅ (added file) | <code>&quot;    &#x27;hf.py&#x27;: &#x27;72b199ae58e47693d9d9eecd1974ce4eba13ded40acab969ecdbdba00201b1f2&#x27;,&quot;</code> |
| trinity_read.py:51 | BEYOND | ∅ (added file) | <code>&quot;    &#x27;torch.py&#x27;: &#x27;72b199ae58e47693d9d9eecd1974ce4eba13ded40acab969ecdbdba00201b1f2&#x27;,&quot;</code> |
| trinity_read.py:52 | BEYOND | ∅ (added file) | <code>&quot;}&quot;</code> |
| trinity_read.py:53 | PATH/ENV | ∅ (added file) | <code>&quot;UV = &#x27;/home/jyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu&#x27;&quot;</code> |
| trinity_read.py:54 | PATH/ENV | ∅ (added file) | <code>&quot;LINEAGE = FSW/&#x27;ap/8865619b/runs/469ddece&#x27;&quot;</code> |
| trinity_read.py:55 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:56 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:57 | PATH/ENV | ∅ (added file) | <code>&quot;def inside(path, parent):&quot;</code> |
| trinity_read.py:58 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:59 | PATH/ENV | ∅ (added file) | <code>&quot;        Path(path).relative_to(parent)&quot;</code> |
| trinity_read.py:60 | PATH/ENV | ∅ (added file) | <code>&quot;        return True&quot;</code> |
| trinity_read.py:61 | PATH/ENV | ∅ (added file) | <code>&quot;    except ValueError:&quot;</code> |
| trinity_read.py:62 | BEYOND | ∅ (added file) | <code>&quot;        return False&quot;</code> |
| trinity_read.py:63 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:64 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:65 | PATH/ENV | ∅ (added file) | <code>&quot;def writable(path):&quot;</code> |
| trinity_read.py:66 | PATH/ENV | ∅ (added file) | <code>&quot;    path = Path(path).resolve()&quot;</code> |
| trinity_read.py:67 | PATH/ENV | ∅ (added file) | <code>&quot;    if not any(inside(path, p) for p in (AREA/&#x27;build&#x27;, DEFAULT_ROOT)):&quot;</code> |
| trinity_read.py:68 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Writes must remain under build/ or root/: &#x27;+str(path))&quot;</code> |
| trinity_read.py:69 | PATH/ENV | ∅ (added file) | <code>&quot;    return path&quot;</code> |
| trinity_read.py:70 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:71 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:72 | PATH/ENV | ∅ (added file) | <code>&quot;def load(path):&quot;</code> |
| trinity_read.py:73 | PATH/ENV | ∅ (added file) | <code>&quot;    return json.loads(Path(path).read_text())&quot;</code> |
| trinity_read.py:74 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:75 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:76 | PATH/ENV | ∅ (added file) | <code>&quot;def sha(path):&quot;</code> |
| trinity_read.py:77 | PATH/ENV | ∅ (added file) | <code>&quot;    h = hashlib.sha256()&quot;</code> |
| trinity_read.py:78 | PATH/ENV | ∅ (added file) | <code>&quot;    with Path(path).open(&#x27;rb&#x27;) as f:&quot;</code> |
| trinity_read.py:79 | PATH/ENV | ∅ (added file) | <code>&quot;        for chunk in iter(lambda: f.read(1024*1024), b&#x27;&#x27;):&quot;</code> |
| trinity_read.py:80 | PATH/ENV | ∅ (added file) | <code>&quot;            h.update(chunk)&quot;</code> |
| trinity_read.py:81 | PATH/ENV | ∅ (added file) | <code>&quot;    return h.hexdigest()&quot;</code> |
| trinity_read.py:82 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:83 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:84 | PATH/ENV | ∅ (added file) | <code>&quot;def install_runner(root):&quot;</code> |
| trinity_read.py:85 | PATH/ENV | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Carry the three wrapper modules with a root-only copy; never alter kit bytes.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:86 | PATH/ENV | ∅ (added file) | <code>&quot;    destination = root/&#x27;trinity_runner&#x27;&quot;</code> |
| trinity_read.py:87 | PATH/ENV | ∅ (added file) | <code>&quot;    rows = {}&quot;</code> |
| trinity_read.py:88 | PATH/ENV | ∅ (added file) | <code>&quot;    for name in (&#x27;trinity_read.py&#x27;, &#x27;namespace_worker.py&#x27;, &#x27;compare_tokens.py&#x27;):&quot;</code> |
| trinity_read.py:89 | PATH/ENV | ∅ (added file) | <code>&quot;        source = BUILD/name; target = destination/name&quot;</code> |
| trinity_read.py:90 | PATH/ENV | ∅ (added file) | <code>&quot;        rows[name] = dict(bytes=source.stat().st_size, sha256=sha(source))&quot;</code> |
| trinity_read.py:91 | PATH/ENV | ∅ (added file) | <code>&quot;        if target.exists():&quot;</code> |
| trinity_read.py:92 | PATH/ENV | ∅ (added file) | <code>&quot;            if sha(target) != rows[name][&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:93 | PATH/ENV | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Staged wrapper differs; preserve and review &#x27;+str(target))&quot;</code> |
| trinity_read.py:94 | BEYOND | ∅ (added file) | <code>&quot;        else:&quot;</code> |
| trinity_read.py:95 | PATH/ENV | ∅ (added file) | <code>&quot;            destination.mkdir(exist_ok=True)&quot;</code> |
| trinity_read.py:96 | PATH/ENV | ∅ (added file) | <code>&quot;            with target.open(&#x27;xb&#x27;) as f: f.write(source.read_bytes())&quot;</code> |
| trinity_read.py:97 | PATH/ENV | ∅ (added file) | <code>&quot;    if (destination/&#x27;MANIFEST.json&#x27;).exists():&quot;</code> |
| trinity_read.py:98 | PATH/ENV | ∅ (added file) | <code>&quot;        if load(destination/&#x27;MANIFEST.json&#x27;) != rows:&quot;</code> |
| trinity_read.py:99 | PATH/ENV | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Staged wrapper manifest differs&#x27;)&quot;</code> |
| trinity_read.py:100 | BEYOND | ∅ (added file) | <code>&quot;    else:&quot;</code> |
| trinity_read.py:101 | PATH/ENV | ∅ (added file) | <code>&quot;        dump(destination/&#x27;MANIFEST.json&#x27;, rows)&quot;</code> |
| trinity_read.py:102 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:103 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:104 | PATH/ENV | ∅ (added file) | <code>&quot;def package(root, config):&quot;</code> |
| trinity_read.py:105 | PATH/ENV | ∅ (added file) | <code>&quot;    return physical(root, config[&#x27;spec&#x27;][&#x27;package&#x27;])&quot;</code> |
| trinity_read.py:106 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:107 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:108 | PATH/ENV | ∅ (added file) | <code>&quot;def gz_bytes(raw):&quot;</code> |
| trinity_read.py:109 | PATH/ENV | ∅ (added file) | <code>&quot;    stream = io.BytesIO()&quot;</code> |
| trinity_read.py:110 | PATH/ENV | ∅ (added file) | <code>&quot;    with gzip.GzipFile(fileobj=stream, mode=&#x27;wb&#x27;, mtime=0) as f:&quot;</code> |
| trinity_read.py:111 | PATH/ENV | ∅ (added file) | <code>&quot;        f.write(raw)&quot;</code> |
| trinity_read.py:112 | PATH/ENV | ∅ (added file) | <code>&quot;    return stream.getvalue()&quot;</code> |
| trinity_read.py:113 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:114 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:115 | PATH/ENV | ∅ (added file) | <code>&quot;def dump(path, value):&quot;</code> |
| trinity_read.py:116 | PATH/ENV | ∅ (added file) | <code>&quot;    path = writable(path)&quot;</code> |
| trinity_read.py:117 | PATH/ENV | ∅ (added file) | <code>&quot;    path.parent.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:118 | PATH/ENV | ∅ (added file) | <code>&quot;    pending = path.with_name(path.name+&#x27;.new.&#x27;+uuid.uuid4().hex)&quot;</code> |
| trinity_read.py:119 | PATH/ENV | ∅ (added file) | <code>&quot;    with pending.open(&#x27;x&#x27;) as f:&quot;</code> |
| trinity_read.py:120 | PATH/ENV | ∅ (added file) | <code>&quot;        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)&quot;</code> |
| trinity_read.py:121 | PATH/ENV | ∅ (added file) | <code>&quot;        f.write(&#x27;\\n&#x27;); f.flush(); os.fsync(f.fileno())&quot;</code> |
| trinity_read.py:122 | PATH/ENV | ∅ (added file) | <code>&quot;    os.replace(str(pending), str(path))&quot;</code> |
| trinity_read.py:123 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:124 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:125 | PATH/ENV | ∅ (added file) | <code>&quot;@contextlib.contextmanager&quot;</code> |
| trinity_read.py:126 | PATH/ENV | ∅ (added file) | <code>&quot;def lock(path):&quot;</code> |
| trinity_read.py:127 | PATH/ENV | ∅ (added file) | <code>&quot;    path = writable(path); path.parent.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:128 | PATH/ENV | ∅ (added file) | <code>&quot;    with path.open(&#x27;a&#x27;) as f:&quot;</code> |
| trinity_read.py:129 | PATH/ENV | ∅ (added file) | <code>&quot;        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)&quot;</code> |
| trinity_read.py:130 | PATH/ENV | ∅ (added file) | <code>&quot;        yield&quot;</code> |
| trinity_read.py:131 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:132 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:133 | PATH/ENV | ∅ (added file) | <code>&quot;def kit_stage():&quot;</code> |
| trinity_read.py:134 | PATH/ENV | ∅ (added file) | <code>&quot;    # Trinity&#x27;s system Python is 3.6; this compatibility method changes no kit file.&quot;</code> |
| trinity_read.py:135 | PATH/ENV | ∅ (added file) | <code>&quot;    if not hasattr(Path, &#x27;is_relative_to&#x27;):&quot;</code> |
| trinity_read.py:136 | PATH/ENV | ∅ (added file) | <code>&quot;        Path.is_relative_to = lambda self, other: inside(self, other)&quot;</code> |
| trinity_read.py:137 | PATH/ENV | ∅ (added file) | <code>&quot;    source = KIT/&#x27;launcher&#x27; if (KIT/&#x27;launcher&#x27;).is_dir() else BUILD.parent/&#x27;bootstrap&#x27;&quot;</code> |
| trinity_read.py:138 | PATH/ENV | ∅ (added file) | <code>&quot;    sys.path.insert(0, str(source))&quot;</code> |
| trinity_read.py:139 | PATH/ENV | ∅ (added file) | <code>&quot;    import orchard_stage&quot;</code> |
| trinity_read.py:140 | PATH/ENV | ∅ (added file) | <code>&quot;    return orchard_stage&quot;</code> |
| trinity_read.py:141 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:142 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:143 | PATH/ENV | ∅ (added file) | <code>&quot;def physical(root, path):&quot;</code> |
| trinity_read.py:144 | PATH/ENV | ∅ (added file) | <code>&quot;    path = Path(path)&quot;</code> |
| trinity_read.py:145 | PATH/ENV | ∅ (added file) | <code>&quot;    if not path.is_absolute() or &#x27;..&#x27; in path.parts:&quot;</code> |
| trinity_read.py:146 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Require a canonical logical path&#x27;)&quot;</code> |
| trinity_read.py:147 | PATH/ENV | ∅ (added file) | <code>&quot;    for prefix, directory in ((SJ, &#x27;sj&#x27;), (FSW, &#x27;fsw&#x27;), (AP, &#x27;m/ap&#x27;)):&quot;</code> |
| trinity_read.py:148 | PATH/ENV | ∅ (added file) | <code>&quot;        if inside(path, prefix):&quot;</code> |
| trinity_read.py:149 | PATH/ENV | ∅ (added file) | <code>&quot;            return Path(root)/directory/path.relative_to(prefix)&quot;</code> |
| trinity_read.py:150 | PATH/ENV | ∅ (added file) | <code>&quot;    raise ValueError(&#x27;Unregistered logical path: &#x27;+str(path))&quot;</code> |
| trinity_read.py:151 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:152 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:153 | PATH/ENV | ∅ (added file) | <code>&quot;def reference_bundle(reference=REFERENCE):&quot;</code> |
| trinity_read.py:154 | PATH/ENV | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Decode data from the accepted BATCH.sh; never execute its shell/Python.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:155 | PATH/ENV | ∅ (added file) | <code>&quot;    config = load(reference/&#x27;CONFIG.json&#x27;)&quot;</code> |
| trinity_read.py:156 | PATH/ENV | ∅ (added file) | <code>&quot;    script = (reference/&#x27;BATCH.sh&#x27;).read_text()&quot;</code> |
| trinity_read.py:157 | PATH/ENV | ∅ (added file) | <code>&quot;    literal = re.search(r&#x27;^raw=base64.b64decode\\((.*),validate=True\\)$&#x27;, script, re.M)&quot;</code> |
| trinity_read.py:158 | PATH/ENV | ∅ (added file) | <code>&quot;    expected = re.search(r\&quot;^if hashlib.sha256\\(raw\\).hexdigest\\(\\)!=&#x27;([0-9a-f]{64})&#x27;\&quot;, script, re.M)&quot;</code> |
| trinity_read.py:159 | PATH/ENV | ∅ (added file) | <code>&quot;    if not literal or not expected:&quot;</code> |
| trinity_read.py:160 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Unrecognized accepted bootstrap&#x27;)&quot;</code> |
| trinity_read.py:161 | PATH/ENV | ∅ (added file) | <code>&quot;    raw = base64.b64decode(ast.literal_eval(literal.group(1)), validate=True)&quot;</code> |
| trinity_read.py:162 | PATH/ENV | ∅ (added file) | <code>&quot;    if hashlib.sha256(raw).hexdigest() != expected.group(1):&quot;</code> |
| trinity_read.py:163 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Bootstrap hash differs&#x27;)&quot;</code> |
| trinity_read.py:164 | PATH/ENV | ∅ (added file) | <code>&quot;    files = {}&quot;</code> |
| trinity_read.py:165 | PATH/ENV | ∅ (added file) | <code>&quot;    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:&quot;</code> |
| trinity_read.py:166 | BEYOND | ∅ (added file) | <code>&quot;        for m in tf:&quot;</code> |
| trinity_read.py:167 | PATH/ENV | ∅ (added file) | <code>&quot;            if not m.isfile() or m.name in files or not re.fullmatch(r&#x27;bootstrap/[A-Za-z0-9_.]+&#x27;, m.name):&quot;</code> |
| trinity_read.py:168 | PATH/ENV | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Unexpected bootstrap member&#x27;)&quot;</code> |
| trinity_read.py:169 | PATH/ENV | ∅ (added file) | <code>&quot;            files[m.name] = tf.extractfile(m).read()&quot;</code> |
| trinity_read.py:170 | PATH/ENV | ∅ (added file) | <code>&quot;    if json.loads(files[&#x27;bootstrap/CONFIG.json&#x27;]) != config:&quot;</code> |
| trinity_read.py:171 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Reference CONFIG differs from bundle&#x27;)&quot;</code> |
| trinity_read.py:172 | PATH/ENV | ∅ (added file) | <code>&quot;    for name, digest in config[&#x27;launcher_pins&#x27;].items():&quot;</code> |
| trinity_read.py:173 | PATH/ENV | ∅ (added file) | <code>&quot;        if hashlib.sha256(files[&#x27;bootstrap/&#x27;+Path(name).name]).hexdigest() != digest:&quot;</code> |
| trinity_read.py:174 | PATH/ENV | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Bootstrap launcher pin differs&#x27;)&quot;</code> |
| trinity_read.py:175 | PATH/ENV | ∅ (added file) | <code>&quot;    if hashlib.sha256(files[&#x27;bootstrap/REVIEW.json&#x27;]).hexdigest() != config[&#x27;launcher_review_pin&#x27;][&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:176 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Bootstrap review pin differs&#x27;)&quot;</code> |
| trinity_read.py:177 | PATH/ENV | ∅ (added file) | <code>&quot;    payload = files[&#x27;bootstrap/payload.tar.gz&#x27;]&quot;</code> |
| trinity_read.py:178 | PATH/ENV | ∅ (added file) | <code>&quot;    if hashlib.sha256(payload).hexdigest() != config[&#x27;payload_sha256&#x27;]:&quot;</code> |
| trinity_read.py:179 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Bootstrap payload pin differs&#x27;)&quot;</code> |
| trinity_read.py:180 | PATH/ENV | ∅ (added file) | <code>&quot;    pins = {}&quot;</code> |
| trinity_read.py:181 | PATH/ENV | ∅ (added file) | <code>&quot;    with tarfile.open(fileobj=io.BytesIO(payload)) as tf:&quot;</code> |
| trinity_read.py:182 | BEYOND | ∅ (added file) | <code>&quot;        for m in tf:&quot;</code> |
| trinity_read.py:183 | PATH/ENV | ∅ (added file) | <code>&quot;            kit_stage().relative(m.name)&quot;</code> |
| trinity_read.py:184 | PATH/ENV | ∅ (added file) | <code>&quot;            if not m.isfile() or m.name in pins:&quot;</code> |
| trinity_read.py:185 | PATH/ENV | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Unexpected payload member&#x27;)&quot;</code> |
| trinity_read.py:186 | PATH/ENV | ∅ (added file) | <code>&quot;            pins[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()&quot;</code> |
| trinity_read.py:187 | PATH/ENV | ∅ (added file) | <code>&quot;    if pins != config[&#x27;payload_pins&#x27;]:&quot;</code> |
| trinity_read.py:188 | PATH/ENV | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Payload member pins differ&#x27;)&quot;</code> |
| trinity_read.py:189 | PATH/ENV | ∅ (added file) | <code>&quot;    return config, files&quot;</code> |
| trinity_read.py:190 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:191 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:192 | BEYOND | ∅ (added file) | <code>&quot;def receipt_ready(path):&quot;</code> |
| trinity_read.py:193 | BEYOND | ∅ (added file) | <code>&quot;    receipt = Path(str(path)+&#x27;.RECEIPT.json&#x27;)&quot;</code> |
| trinity_read.py:194 | BEYOND | ∅ (added file) | <code>&quot;    if not path.is_file() or not receipt.is_file():&quot;</code> |
| trinity_read.py:195 | BEYOND | ∅ (added file) | <code>&quot;        return False&quot;</code> |
| trinity_read.py:196 | BEYOND | ∅ (added file) | <code>&quot;    value = load(receipt)&quot;</code> |
| trinity_read.py:197 | BEYOND | ∅ (added file) | <code>&quot;    if not isinstance(value, dict):&quot;</code> |
| trinity_read.py:198 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Invalid completion receipt: &#x27;+str(receipt))&quot;</code> |
| trinity_read.py:199 | BEYOND | ∅ (added file) | <code>&quot;    # Receipts admit a completed transfer; authoritative hashes come from the kit.&quot;</code> |
| trinity_read.py:200 | BEYOND | ∅ (added file) | <code>&quot;    for key in (&#x27;bytes&#x27;, &#x27;size&#x27;):&quot;</code> |
| trinity_read.py:201 | BEYOND | ∅ (added file) | <code>&quot;        if key in value and isinstance(value[key], int) and value[key] != path.stat().st_size:&quot;</code> |
| trinity_read.py:202 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Receipt size differs: &#x27;+str(path))&quot;</code> |
| trinity_read.py:203 | BEYOND | ∅ (added file) | <code>&quot;    if &#x27;sha256&#x27; in value and sha(path) != value[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:204 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Receipt SHA256 differs: &#x27;+str(path))&quot;</code> |
| trinity_read.py:205 | BEYOND | ∅ (added file) | <code>&quot;    return True&quot;</code> |
| trinity_read.py:206 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:207 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:208 | BEYOND | ∅ (added file) | <code>&quot;def authenticate_parts(path, group):&quot;</code> |
| trinity_read.py:209 | BEYOND | ∅ (added file) | <code>&quot;    if path.stat().st_size != sum(row[1] for row in group):&quot;</code> |
| trinity_read.py:210 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Runtime archive size differs&#x27;)&quot;</code> |
| trinity_read.py:211 | BEYOND | ∅ (added file) | <code>&quot;    whole = hashlib.sha256()&quot;</code> |
| trinity_read.py:212 | BEYOND | ∅ (added file) | <code>&quot;    with path.open(&#x27;rb&#x27;) as f:&quot;</code> |
| trinity_read.py:213 | BEYOND | ∅ (added file) | <code>&quot;        for _, size, expected in group:&quot;</code> |
| trinity_read.py:214 | BEYOND | ∅ (added file) | <code>&quot;            h = hashlib.sha256(); remaining = size&quot;</code> |
| trinity_read.py:215 | BEYOND | ∅ (added file) | <code>&quot;            while remaining:&quot;</code> |
| trinity_read.py:216 | BEYOND | ∅ (added file) | <code>&quot;                chunk = f.read(min(1024*1024, remaining))&quot;</code> |
| trinity_read.py:217 | BEYOND | ∅ (added file) | <code>&quot;                if not chunk:&quot;</code> |
| trinity_read.py:218 | BEYOND | ∅ (added file) | <code>&quot;                    raise ValueError(&#x27;Truncated runtime archive&#x27;)&quot;</code> |
| trinity_read.py:219 | BEYOND | ∅ (added file) | <code>&quot;                h.update(chunk); whole.update(chunk); remaining -= len(chunk)&quot;</code> |
| trinity_read.py:220 | BEYOND | ∅ (added file) | <code>&quot;            if h.hexdigest() != expected:&quot;</code> |
| trinity_read.py:221 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Runtime part SHA256 differs&#x27;)&quot;</code> |
| trinity_read.py:222 | BEYOND | ∅ (added file) | <code>&quot;    return whole.hexdigest()&quot;</code> |
| trinity_read.py:223 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:224 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:225 | BEYOND | ∅ (added file) | <code>&quot;def small_archive_inventory(source, pin):&quot;</code> |
| trinity_read.py:226 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Recover an old camera receipt&#x27;s member pins from its authenticated small tar.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:227 | BEYOND | ∅ (added file) | <code>&quot;    if source.stat().st_size != pin[&#x27;bytes&#x27;] or sha(source) != pin[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:228 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Camera archive pin differs&#x27;)&quot;</code> |
| trinity_read.py:229 | BEYOND | ∅ (added file) | <code>&quot;    inventory = {}&quot;</code> |
| trinity_read.py:230 | BEYOND | ∅ (added file) | <code>&quot;    with tarfile.open(str(source)) as archive:&quot;</code> |
| trinity_read.py:231 | BEYOND | ∅ (added file) | <code>&quot;        for member in archive:&quot;</code> |
| trinity_read.py:232 | BEYOND | ∅ (added file) | <code>&quot;            kit_stage().relative(member.name)&quot;</code> |
| trinity_read.py:233 | BEYOND | ∅ (added file) | <code>&quot;            if member.isdir(): continue&quot;</code> |
| trinity_read.py:234 | BEYOND | ∅ (added file) | <code>&quot;            if not member.isfile() or member.name in inventory:&quot;</code> |
| trinity_read.py:235 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Unexpected camera archive member&#x27;)&quot;</code> |
| trinity_read.py:236 | BEYOND | ∅ (added file) | <code>&quot;            digest = hashlib.sha256()&quot;</code> |
| trinity_read.py:237 | BEYOND | ∅ (added file) | <code>&quot;            with archive.extractfile(member) as stream:&quot;</code> |
| trinity_read.py:238 | BEYOND | ∅ (added file) | <code>&quot;                for chunk in iter(lambda: stream.read(1024*1024), b&#x27;&#x27;): digest.update(chunk)&quot;</code> |
| trinity_read.py:239 | BEYOND | ∅ (added file) | <code>&quot;            inventory[member.name] = dict(bytes=member.size, sha256=digest.hexdigest())&quot;</code> |
| trinity_read.py:240 | BEYOND | ∅ (added file) | <code>&quot;    return inventory&quot;</code> |
| trinity_read.py:241 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:242 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:243 | BEYOND | ∅ (added file) | <code>&quot;def piece(root, state, name, action):&quot;</code> |
| trinity_read.py:244 | BEYOND | ∅ (added file) | <code>&quot;    previous = state[&#x27;pieces&#x27;].get(name)&quot;</code> |
| trinity_read.py:245 | BEYOND | ∅ (added file) | <code>&quot;    if previous:&quot;</code> |
| trinity_read.py:246 | BEYOND | ∅ (added file) | <code>&quot;        if previous[&#x27;status&#x27;] != &#x27;complete&#x27;:&quot;</code> |
| trinity_read.py:247 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Partial stage refused: &#x27;+name+&#x27;; preserve it for operator review&#x27;)&quot;</code> |
| trinity_read.py:248 | BEYOND | ∅ (added file) | <code>&quot;        return&quot;</code> |
| trinity_read.py:249 | BEYOND | ∅ (added file) | <code>&quot;    state[&#x27;pieces&#x27;][name] = dict(status=&#x27;partial&#x27;, started=time.time())&quot;</code> |
| trinity_read.py:250 | BEYOND | ∅ (added file) | <code>&quot;    dump(root/&#x27;STAGING.json&#x27;, state)&quot;</code> |
| trinity_read.py:251 | BEYOND | ∅ (added file) | <code>&quot;    result = action()&quot;</code> |
| trinity_read.py:252 | BEYOND | ∅ (added file) | <code>&quot;    state[&#x27;pieces&#x27;][name] = dict(status=&#x27;complete&#x27;, completed=time.time(), evidence=result)&quot;</code> |
| trinity_read.py:253 | BEYOND | ∅ (added file) | <code>&quot;    dump(root/&#x27;STAGING.json&#x27;, state)&quot;</code> |
| trinity_read.py:254 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:255 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:256 | BEYOND | ∅ (added file) | <code>&quot;def verify_export_local(root, config):&quot;</code> |
| trinity_read.py:257 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Hash the existing export without moving it or resolving its logical links on host.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:258 | BEYOND | ∅ (added file) | <code>&quot;    spec = config[&#x27;spec&#x27;]; pin = spec[&#x27;artifact&#x27;]; artifact = physical(root, pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:259 | BEYOND | ∅ (added file) | <code>&quot;    if sha(artifact) != pin[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:260 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Existing export artifact SHA256 differs&#x27;)&quot;</code> |
| trinity_read.py:261 | BEYOND | ∅ (added file) | <code>&quot;    a = load(artifact)&quot;</code> |
| trinity_read.py:262 | BEYOND | ∅ (added file) | <code>&quot;    if a[&#x27;step&#x27;] != spec[&#x27;step&#x27;] or a[&#x27;schema&#x27;] != &#x27;carrier-c1-artifact-v1&#x27;:&quot;</code> |
| trinity_read.py:263 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Existing export identity differs&#x27;)&quot;</code> |
| trinity_read.py:264 | BEYOND | ∅ (added file) | <code>&quot;    manifest = physical(root, a[&#x27;full_weights&#x27;][&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:265 | BEYOND | ∅ (added file) | <code>&quot;    if manifest != artifact.parent/&#x27;full_weights/full_weights.json&#x27; or sha(manifest) != a[&#x27;full_weights&#x27;][&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:266 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Existing full-weights manifest differs&#x27;)&quot;</code> |
| trinity_read.py:267 | BEYOND | ∅ (added file) | <code>&quot;    m = load(manifest)&quot;</code> |
| trinity_read.py:268 | BEYOND | ∅ (added file) | <code>&quot;    for row in [m[&#x27;index&#x27;]]+m[&#x27;files&#x27;]:&quot;</code> |
| trinity_read.py:269 | BEYOND | ∅ (added file) | <code>&quot;        if Path(row[&#x27;name&#x27;]).name != row[&#x27;name&#x27;]:&quot;</code> |
| trinity_read.py:270 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Unsafe export member&#x27;)&quot;</code> |
| trinity_read.py:271 | BEYOND | ∅ (added file) | <code>&quot;        p = manifest.parent/row[&#x27;name&#x27;]&quot;</code> |
| trinity_read.py:272 | BEYOND | ∅ (added file) | <code>&quot;        if &#x27;bytes&#x27; in row and p.stat().st_size != row[&#x27;bytes&#x27;]:&quot;</code> |
| trinity_read.py:273 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Existing export shard size differs&#x27;)&quot;</code> |
| trinity_read.py:274 | BEYOND | ∅ (added file) | <code>&quot;        if sha(p) != row[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:275 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Existing export member SHA256 differs: &#x27;+row[&#x27;name&#x27;])&quot;</code> |
| trinity_read.py:276 | BEYOND | ∅ (added file) | <code>&quot;    return dict(artifact_sha256=pin[&#x27;sha256&#x27;], full_weights_sha256=a[&#x27;full_weights&#x27;][&#x27;sha256&#x27;],&quot;</code> |
| trinity_read.py:277 | BEYOND | ∅ (added file) | <code>&quot;                files=len(m[&#x27;files&#x27;]), moved=False)&quot;</code> |
| trinity_read.py:278 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:279 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:280 | BEYOND | ∅ (added file) | <code>&quot;def stage(root, dl):&quot;</code> |
| trinity_read.py:281 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(root); dl = Path(dl).resolve(); root.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:282 | BEYOND | ∅ (added file) | <code>&quot;    config, bootstrap = reference_bundle(); S = kit_stage()&quot;</code> |
| trinity_read.py:283 | BEYOND | ∅ (added file) | <code>&quot;    with lock(root/&#x27;.stage.lock&#x27;):&quot;</code> |
| trinity_read.py:284 | BEYOND | ∅ (added file) | <code>&quot;        state = load(root/&#x27;STAGING.json&#x27;) if (root/&#x27;STAGING.json&#x27;).exists() else dict(schema=1, pieces={})&quot;</code> |
| trinity_read.py:285 | BEYOND | ∅ (added file) | <code>&quot;        for name, item in state[&#x27;pieces&#x27;].items():&quot;</code> |
| trinity_read.py:286 | BEYOND | ∅ (added file) | <code>&quot;            if item[&#x27;status&#x27;] != &#x27;complete&#x27;:&quot;</code> |
| trinity_read.py:287 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Partial stage refused: &#x27;+name)&quot;</code> |
| trinity_read.py:288 | BEYOND | ∅ (added file) | <code>&quot;        S.room(root)&quot;</code> |
| trinity_read.py:289 | BEYOND | ∅ (added file) | <code>&quot;        def boot():&quot;</code> |
| trinity_read.py:290 | BEYOND | ∅ (added file) | <code>&quot;            if (root/&#x27;bootstrap&#x27;).exists():&quot;</code> |
| trinity_read.py:291 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Unrecorded bootstrap destination exists&#x27;)&quot;</code> |
| trinity_read.py:292 | BEYOND | ∅ (added file) | <code>&quot;            for name, raw in bootstrap.items():&quot;</code> |
| trinity_read.py:293 | BEYOND | ∅ (added file) | <code>&quot;                p = root/name; p.parent.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:294 | BEYOND | ∅ (added file) | <code>&quot;                with p.open(&#x27;xb&#x27;) as f: f.write(raw)&quot;</code> |
| trinity_read.py:295 | BEYOND | ∅ (added file) | <code>&quot;            return dict(payload_sha256=config[&#x27;payload_sha256&#x27;])&quot;</code> |
| trinity_read.py:296 | BEYOND | ∅ (added file) | <code>&quot;        piece(root, state, &#x27;bootstrap&#x27;, boot)&quot;</code> |
| trinity_read.py:297 | BEYOND | ∅ (added file) | <code>&quot;        missing = []&quot;</code> |
| trinity_read.py:298 | BEYOND | ∅ (added file) | <code>&quot;        for index, group in enumerate(config[&#x27;assets&#x27;][&#x27;groups&#x27;]):&quot;</code> |
| trinity_read.py:299 | BEYOND | ∅ (added file) | <code>&quot;            name = &#x27;runtime_&#x27;+str(index); source = dl/(name+&#x27;.tar&#x27;)&quot;</code> |
| trinity_read.py:300 | BEYOND | ∅ (added file) | <code>&quot;            if name in state[&#x27;pieces&#x27;]:&quot;</code> |
| trinity_read.py:301 | BEYOND | ∅ (added file) | <code>&quot;                continue&quot;</code> |
| trinity_read.py:302 | BEYOND | ∅ (added file) | <code>&quot;            if not receipt_ready(source):&quot;</code> |
| trinity_read.py:303 | BEYOND | ∅ (added file) | <code>&quot;                missing.append(source.name+&#x27; + receipt&#x27;); continue&quot;</code> |
| trinity_read.py:304 | BEYOND | ∅ (added file) | <code>&quot;            def runtime(source=source, group=group):&quot;</code> |
| trinity_read.py:305 | BEYOND | ∅ (added file) | <code>&quot;                digest = authenticate_parts(source, group); S.room(root, source.stat().st_size)&quot;</code> |
| trinity_read.py:306 | BEYOND | ∅ (added file) | <code>&quot;                inventory = S.unpack(source, root, links=True)&quot;</code> |
| trinity_read.py:307 | BEYOND | ∅ (added file) | <code>&quot;                return dict(sha256=digest, files=len(inventory), inventory=inventory)&quot;</code> |
| trinity_read.py:308 | BEYOND | ∅ (added file) | <code>&quot;            piece(root, state, name, runtime)&quot;</code> |
| trinity_read.py:309 | BEYOND | ∅ (added file) | <code>&quot;        for name, filename, pin in [(&#x27;a0&#x27;, &#x27;camera.tar&#x27;, config[&#x27;assets&#x27;][&#x27;camera_archive&#x27;]),&quot;</code> |
| trinity_read.py:310 | BEYOND | ∅ (added file) | <code>&quot;                                     (&#x27;bwrap&#x27;, &#x27;bwrap&#x27;, config[&#x27;assets&#x27;][&#x27;bwrap_pin&#x27;])]:&quot;</code> |
| trinity_read.py:311 | BEYOND | ∅ (added file) | <code>&quot;            source = dl/filename&quot;</code> |
| trinity_read.py:312 | BEYOND | ∅ (added file) | <code>&quot;            if name in state[&#x27;pieces&#x27;]:&quot;</code> |
| trinity_read.py:313 | BEYOND | ∅ (added file) | <code>&quot;                if name == &#x27;a0&#x27; and &#x27;inventory&#x27; not in state[&#x27;pieces&#x27;][name][&#x27;evidence&#x27;] and receipt_ready(source):&quot;</code> |
| trinity_read.py:314 | BEYOND | ∅ (added file) | <code>&quot;                    state[&#x27;pieces&#x27;][name][&#x27;evidence&#x27;][&#x27;inventory&#x27;] = small_archive_inventory(source, pin)&quot;</code> |
| trinity_read.py:315 | BEYOND | ∅ (added file) | <code>&quot;                continue&quot;</code> |
| trinity_read.py:316 | BEYOND | ∅ (added file) | <code>&quot;            if not receipt_ready(source):&quot;</code> |
| trinity_read.py:317 | BEYOND | ∅ (added file) | <code>&quot;                missing.append(filename+&#x27; + receipt&#x27;); continue&quot;</code> |
| trinity_read.py:318 | BEYOND | ∅ (added file) | <code>&quot;            def small(source=source, pin=pin, name=name):&quot;</code> |
| trinity_read.py:319 | BEYOND | ∅ (added file) | <code>&quot;                if source.stat().st_size != pin[&#x27;bytes&#x27;] or sha(source) != pin[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:320 | BEYOND | ∅ (added file) | <code>&quot;                    raise ValueError(&#x27;Local &#x27;+name+&#x27; pin differs&#x27;)&quot;</code> |
| trinity_read.py:321 | BEYOND | ∅ (added file) | <code>&quot;                if name == &#x27;bwrap&#x27;:&quot;</code> |
| trinity_read.py:322 | BEYOND | ∅ (added file) | <code>&quot;                    with (root/&#x27;bwrap&#x27;).open(&#x27;xb&#x27;) as out, source.open(&#x27;rb&#x27;) as inp:&quot;</code> |
| trinity_read.py:323 | BEYOND | ∅ (added file) | <code>&quot;                        shutil.copyfileobj(inp, out)&quot;</code> |
| trinity_read.py:324 | BEYOND | ∅ (added file) | <code>&quot;                    (root/&#x27;bwrap&#x27;).chmod(0o700)&quot;</code> |
| trinity_read.py:325 | BEYOND | ∅ (added file) | <code>&quot;                else:&quot;</code> |
| trinity_read.py:326 | BEYOND | ∅ (added file) | <code>&quot;                    inventory = S.unpack(source, root)&quot;</code> |
| trinity_read.py:327 | BEYOND | ∅ (added file) | <code>&quot;                    return dict(sha256=pin[&#x27;sha256&#x27;], inventory=inventory)&quot;</code> |
| trinity_read.py:328 | BEYOND | ∅ (added file) | <code>&quot;                return dict(sha256=pin[&#x27;sha256&#x27;])&quot;</code> |
| trinity_read.py:329 | BEYOND | ∅ (added file) | <code>&quot;            piece(root, state, name, small)&quot;</code> |
| trinity_read.py:330 | BEYOND | ∅ (added file) | <code>&quot;        runtime_done = all(&#x27;runtime_&#x27;+str(i) in state[&#x27;pieces&#x27;] for i in range(3))&quot;</code> |
| trinity_read.py:331 | BEYOND | ∅ (added file) | <code>&quot;        if runtime_done and &#x27;a0&#x27; in state[&#x27;pieces&#x27;]:&quot;</code> |
| trinity_read.py:332 | BEYOND | ∅ (added file) | <code>&quot;            def payload():&quot;</code> |
| trinity_read.py:333 | BEYOND | ∅ (added file) | <code>&quot;                with (root/&#x27;bootstrap/payload.tar.gz&#x27;).open(&#x27;rb&#x27;) as f:&quot;</code> |
| trinity_read.py:334 | BEYOND | ∅ (added file) | <code>&quot;                    inventory = S.extract_stream(f, root, None, 32*1024**2, overlay=True)&quot;</code> |
| trinity_read.py:335 | BEYOND | ∅ (added file) | <code>&quot;                return dict(files=len(inventory), sha256=config[&#x27;payload_sha256&#x27;], inventory=inventory)&quot;</code> |
| trinity_read.py:336 | BEYOND | ∅ (added file) | <code>&quot;            piece(root, state, &#x27;reader_payload&#x27;, payload)&quot;</code> |
| trinity_read.py:337 | BEYOND | ∅ (added file) | <code>&quot;        source = dl/&#x27;base.tar&#x27;&quot;</code> |
| trinity_read.py:338 | BEYOND | ∅ (added file) | <code>&quot;        if &#x27;base&#x27; not in state[&#x27;pieces&#x27;]:&quot;</code> |
| trinity_read.py:339 | BEYOND | ∅ (added file) | <code>&quot;            if &#x27;runtime_2&#x27; not in state[&#x27;pieces&#x27;] or not receipt_ready(source):&quot;</code> |
| trinity_read.py:340 | BEYOND | ∅ (added file) | <code>&quot;                missing.append(&#x27;base.tar + receipt + runtime_2&#x27;)&quot;</code> |
| trinity_read.py:341 | BEYOND | ∅ (added file) | <code>&quot;            else:&quot;</code> |
| trinity_read.py:342 | BEYOND | ∅ (added file) | <code>&quot;                def base():&quot;</code> |
| trinity_read.py:343 | BEYOND | ∅ (added file) | <code>&quot;                    if source.stat().st_size != config[&#x27;assets&#x27;][&#x27;base_archive_bytes&#x27;]:&quot;</code> |
| trinity_read.py:344 | BEYOND | ∅ (added file) | <code>&quot;                        raise ValueError(&#x27;Base archive size differs&#x27;)&quot;</code> |
| trinity_read.py:345 | BEYOND | ∅ (added file) | <code>&quot;                    pin = config[&#x27;assets&#x27;][&#x27;base_manifest&#x27;]; manifest = physical(root, pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:346 | BEYOND | ∅ (added file) | <code>&quot;                    if sha(manifest) != pin[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:347 | BEYOND | ∅ (added file) | <code>&quot;                        raise ValueError(&#x27;Base manifest hash differs&#x27;)&quot;</code> |
| trinity_read.py:348 | BEYOND | ∅ (added file) | <code>&quot;                    dest = root/&#x27;m/ap/85fc3486&#x27;&quot;</code> |
| trinity_read.py:349 | BEYOND | ∅ (added file) | <code>&quot;                    if dest.exists(): raise ValueError(&#x27;Unrecorded base destination exists&#x27;)&quot;</code> |
| trinity_read.py:350 | BEYOND | ∅ (added file) | <code>&quot;                    S.room(root, source.stat().st_size); dest.mkdir(parents=True)&quot;</code> |
| trinity_read.py:351 | BEYOND | ∅ (added file) | <code>&quot;                    inventory = S.unpack(source, dest, strip=3)&quot;</code> |
| trinity_read.py:352 | BEYOND | ∅ (added file) | <code>&quot;                    expected = {r[&#x27;path&#x27;]: {k:r[k] for k in (&#x27;bytes&#x27;, &#x27;sha256&#x27;)} for r in load(manifest)[&#x27;files&#x27;]}&quot;</code> |
| trinity_read.py:353 | BEYOND | ∅ (added file) | <code>&quot;                    if inventory != expected:&quot;</code> |
| trinity_read.py:354 | BEYOND | ∅ (added file) | <code>&quot;                        raise ValueError(&#x27;Base file inventory differs from frozen manifest&#x27;)&quot;</code> |
| trinity_read.py:355 | BEYOND | ∅ (added file) | <code>&quot;                    return dict(files=len(inventory), manifest_sha256=pin[&#x27;sha256&#x27;])&quot;</code> |
| trinity_read.py:356 | BEYOND | ∅ (added file) | <code>&quot;                piece(root, state, &#x27;base&#x27;, base)&quot;</code> |
| trinity_read.py:357 | BEYOND | ∅ (added file) | <code>&quot;        # Verification is independent of pending runtime pieces; no export fetch exists.&quot;</code> |
| trinity_read.py:358 | BEYOND | ∅ (added file) | <code>&quot;        piece(root, state, &#x27;export&#x27;, lambda: verify_export_local(root, config))&quot;</code> |
| trinity_read.py:359 | BEYOND | ∅ (added file) | <code>&quot;        state[&#x27;complete&#x27;] = REQUIRED_PIECES &lt;= set(state[&#x27;pieces&#x27;]); state[&#x27;missing&#x27;] = missing&quot;</code> |
| trinity_read.py:360 | BEYOND | ∅ (added file) | <code>&quot;        dump(root/&#x27;STAGING.json&#x27;, state)&quot;</code> |
| trinity_read.py:361 | BEYOND | ∅ (added file) | <code>&quot;        install_runner(root)&quot;</code> |
| trinity_read.py:362 | BEYOND | ∅ (added file) | <code>&quot;        return state&quot;</code> |
| trinity_read.py:363 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:364 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:365 | BEYOND | ∅ (added file) | <code>&quot;def store_index(root):&quot;</code> |
| trinity_read.py:366 | BEYOND | ∅ (added file) | <code>&quot;    path = Path(root)/&#x27;k6tk/MEMBERS.tsv.gz&#x27;; result = {}&quot;</code> |
| trinity_read.py:367 | BEYOND | ∅ (added file) | <code>&quot;    if path.exists():&quot;</code> |
| trinity_read.py:368 | BEYOND | ∅ (added file) | <code>&quot;        with gzip.open(str(path), &#x27;rt&#x27;) as f:&quot;</code> |
| trinity_read.py:369 | BEYOND | ∅ (added file) | <code>&quot;            for line in f:&quot;</code> |
| trinity_read.py:370 | BEYOND | ∅ (added file) | <code>&quot;                digest, shard = line.rstrip(&#x27;\\n&#x27;).split(&#x27;\\t&#x27;)&quot;</code> |
| trinity_read.py:371 | BEYOND | ∅ (added file) | <code>&quot;                if not re.fullmatch(&#x27;[0-9a-f]{64}&#x27;, digest) or not re.fullmatch(&#x27;[a-z0-9]+_[0-9]+[.]tar&#x27;, shard):&quot;</code> |
| trinity_read.py:372 | BEYOND | ∅ (added file) | <code>&quot;                    raise ValueError(&#x27;Malformed frame store index&#x27;)&quot;</code> |
| trinity_read.py:373 | BEYOND | ∅ (added file) | <code>&quot;                if digest in result: raise ValueError(&#x27;Duplicate store SHA&#x27;)&quot;</code> |
| trinity_read.py:374 | BEYOND | ∅ (added file) | <code>&quot;                part = path.parent/&#x27;parts&#x27;/shard.split(&#x27;_&#x27;)[0]/shard&quot;</code> |
| trinity_read.py:375 | BEYOND | ∅ (added file) | <code>&quot;                if not part.is_file(): raise ValueError(&#x27;Indexed frame shard is absent&#x27;)&quot;</code> |
| trinity_read.py:376 | BEYOND | ∅ (added file) | <code>&quot;                result[digest] = shard&quot;</code> |
| trinity_read.py:377 | BEYOND | ∅ (added file) | <code>&quot;    return result&quot;</code> |
| trinity_read.py:378 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:379 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:380 | BEYOND | ∅ (added file) | <code>&quot;def frame_members(path):&quot;</code> |
| trinity_read.py:381 | BEYOND | ∅ (added file) | <code>&quot;    with tarfile.open(str(path), &#x27;r:*&#x27;) as tf:&quot;</code> |
| trinity_read.py:382 | BEYOND | ∅ (added file) | <code>&quot;        seen = set()&quot;</code> |
| trinity_read.py:383 | BEYOND | ∅ (added file) | <code>&quot;        for m in tf:&quot;</code> |
| trinity_read.py:384 | BEYOND | ∅ (added file) | <code>&quot;            digest = Path(m.name).stem&quot;</code> |
| trinity_read.py:385 | BEYOND | ∅ (added file) | <code>&quot;            if (not m.isfile() or not re.fullmatch(&#x27;[0-9a-f]{64}&#x27;, digest)&quot;</code> |
| trinity_read.py:386 | BEYOND | ∅ (added file) | <code>&quot;                    or m.name != digest[:2]+&#x27;/&#x27;+digest+&#x27;.png&#x27; or digest in seen or m.size &gt; 64*1024**2):&quot;</code> |
| trinity_read.py:387 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Unexpected PNG archive member: &#x27;+m.name)&quot;</code> |
| trinity_read.py:388 | BEYOND | ∅ (added file) | <code>&quot;            raw = tf.extractfile(m).read()&quot;</code> |
| trinity_read.py:389 | BEYOND | ∅ (added file) | <code>&quot;            if not raw.startswith(b&#x27;\\x89PNG\\r\\n\\x1a\\n&#x27;) or hashlib.sha256(raw).hexdigest() != digest:&quot;</code> |
| trinity_read.py:390 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;PNG SHA256 or signature differs: &#x27;+m.name)&quot;</code> |
| trinity_read.py:391 | BEYOND | ∅ (added file) | <code>&quot;            seen.add(digest)&quot;</code> |
| trinity_read.py:392 | BEYOND | ∅ (added file) | <code>&quot;            yield digest, raw&quot;</code> |
| trinity_read.py:393 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:394 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:395 | BEYOND | ∅ (added file) | <code>&quot;def frames(root, archives):&quot;</code> |
| trinity_read.py:396 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(root); store = root/&#x27;k6tk&#x27;; store.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:397 | BEYOND | ∅ (added file) | <code>&quot;    with lock(store/&#x27;.lock&#x27;):&quot;</code> |
| trinity_read.py:398 | BEYOND | ∅ (added file) | <code>&quot;        index = store_index(root); added = 0; total_bytes = 0&quot;</code> |
| trinity_read.py:399 | BEYOND | ∅ (added file) | <code>&quot;        for path in archives:&quot;</code> |
| trinity_read.py:400 | BEYOND | ∅ (added file) | <code>&quot;            path = Path(path).resolve()&quot;</code> |
| trinity_read.py:401 | BEYOND | ∅ (added file) | <code>&quot;            # Validate the entire input before publishing anything from this input.&quot;</code> |
| trinity_read.py:402 | BEYOND | ∅ (added file) | <code>&quot;            fresh = {h:len(raw) for h, raw in frame_members(path) if h not in index}&quot;</code> |
| trinity_read.py:403 | BEYOND | ∅ (added file) | <code>&quot;            if not fresh: continue&quot;</code> |
| trinity_read.py:404 | BEYOND | ∅ (added file) | <code>&quot;            kit_stage().room(store, sum(fresh.values())+1024*len(fresh)+10240)&quot;</code> |
| trinity_read.py:405 | BEYOND | ∅ (added file) | <code>&quot;            tag = &#x27;t&#x27;+uuid.uuid4().hex; partdir = store/&#x27;parts&#x27;/tag; partdir.mkdir(parents=True)&quot;</code> |
| trinity_read.py:406 | BEYOND | ∅ (added file) | <code>&quot;            shard = tag+&#x27;_000.tar&#x27;; partial = partdir/(shard+&#x27;.partial&#x27;)&quot;</code> |
| trinity_read.py:407 | BEYOND | ∅ (added file) | <code>&quot;            with tarfile.open(str(partial), &#x27;w&#x27;, format=tarfile.USTAR_FORMAT) as tf:&quot;</code> |
| trinity_read.py:408 | BEYOND | ∅ (added file) | <code>&quot;                written = set()&quot;</code> |
| trinity_read.py:409 | BEYOND | ∅ (added file) | <code>&quot;                for digest, raw in frame_members(path):&quot;</code> |
| trinity_read.py:410 | BEYOND | ∅ (added file) | <code>&quot;                    if digest not in fresh: continue&quot;</code> |
| trinity_read.py:411 | BEYOND | ∅ (added file) | <code>&quot;                    info = tarfile.TarInfo(digest[:2]+&#x27;/&#x27;+digest+&#x27;.png&#x27;); info.size = len(raw); info.mode = 0o444&quot;</code> |
| trinity_read.py:412 | BEYOND | ∅ (added file) | <code>&quot;                    tf.addfile(info, io.BytesIO(raw)); written.add(digest)&quot;</code> |
| trinity_read.py:413 | BEYOND | ∅ (added file) | <code>&quot;                if written != set(fresh): raise ValueError(&#x27;Frame input changed during build&#x27;)&quot;</code> |
| trinity_read.py:414 | BEYOND | ∅ (added file) | <code>&quot;            os.replace(str(partial), str(partdir/shard))&quot;</code> |
| trinity_read.py:415 | BEYOND | ∅ (added file) | <code>&quot;            # Append a gzip member: existing index bytes and shards never change.&quot;</code> |
| trinity_read.py:416 | BEYOND | ∅ (added file) | <code>&quot;            rows = &#x27;&#x27;.join(h+&#x27;\\t&#x27;+shard+&#x27;\\n&#x27; for h in sorted(fresh)).encode()&quot;</code> |
| trinity_read.py:417 | BEYOND | ∅ (added file) | <code>&quot;            with (store/&#x27;MEMBERS.tsv.gz&#x27;).open(&#x27;ab&#x27;) as f:&quot;</code> |
| trinity_read.py:418 | BEYOND | ∅ (added file) | <code>&quot;                f.write(gz_bytes(rows)); f.flush(); os.fsync(f.fileno())&quot;</code> |
| trinity_read.py:419 | BEYOND | ∅ (added file) | <code>&quot;            index.update({h:shard for h in fresh}); added += len(fresh); total_bytes += sum(fresh.values())&quot;</code> |
| trinity_read.py:420 | BEYOND | ∅ (added file) | <code>&quot;        if not (store/&#x27;MEMBERS.tsv.gz&#x27;).exists():&quot;</code> |
| trinity_read.py:421 | BEYOND | ∅ (added file) | <code>&quot;            (store/&#x27;MEMBERS.tsv.gz&#x27;).write_bytes(gz_bytes(b&#x27;&#x27;))&quot;</code> |
| trinity_read.py:422 | BEYOND | ∅ (added file) | <code>&quot;        return dict(added=added, added_png_bytes=total_bytes, frames=len(index))&quot;</code> |
| trinity_read.py:423 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:424 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:425 | PATH/ENV | ∅ (added file) | <code>&quot;def shm_directory(root, shm=None):&quot;</code> |
| trinity_read.py:426 | PATH/ENV | ∅ (added file) | <code>&quot;    path = writable(shm or root/&#x27;shm&#x27;)&quot;</code> |
| trinity_read.py:427 | PATH/ENV | ∅ (added file) | <code>&quot;    path.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:428 | PATH/ENV | ∅ (added file) | <code>&quot;    return path&quot;</code> |
| trinity_read.py:429 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:430 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:431 | PATH/ENV | ∅ (added file) | <code>&quot;def bwrap_path(root, path=DEFAULT_BWRAP):&quot;</code> |
| trinity_read.py:432 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Reject the staged evidence binary, including links and byte-identical copies.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:433 | PATH/ENV | ∅ (added file) | <code>&quot;    path = Path(path).resolve()&quot;</code> |
| trinity_read.py:434 | BEYOND | ∅ (added file) | <code>&quot;    staged = root/&#x27;bwrap&#x27;&quot;</code> |
| trinity_read.py:435 | BEYOND | ∅ (added file) | <code>&quot;    if path == staged.resolve() or (staged.exists() and os.path.samefile(str(path), str(staged))):&quot;</code> |
| trinity_read.py:436 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Staged bwrap is authenticated evidence only; choose a host bwrap&#x27;)&quot;</code> |
| trinity_read.py:437 | BEYOND | ∅ (added file) | <code>&quot;    if sha(path) == PINNED_BWRAP_SHA256:&quot;</code> |
| trinity_read.py:438 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Pinned Orchard bwrap must never execute&#x27;)&quot;</code> |
| trinity_read.py:439 | BEYOND | ∅ (added file) | <code>&quot;    if not path.is_file() or not os.access(str(path), os.X_OK):&quot;</code> |
| trinity_read.py:440 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;bwrap must be an executable file: &#x27;+str(path))&quot;</code> |
| trinity_read.py:441 | BEYOND | ∅ (added file) | <code>&quot;    return str(path)&quot;</code> |
| trinity_read.py:442 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:443 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:444 | PATH/ENV | ∅ (added file) | <code>&quot;def bwrap_evidence(root, path=DEFAULT_BWRAP):&quot;</code> |
| trinity_read.py:445 | BEYOND | ∅ (added file) | <code>&quot;    path = bwrap_path(root, path)&quot;</code> |
| trinity_read.py:446 | BEYOND | ∅ (added file) | <code>&quot;    digest = sha(path)&quot;</code> |
| trinity_read.py:447 | BEYOND | ∅ (added file) | <code>&quot;    version = subprocess.run([path, &#x27;--version&#x27;], stdout=subprocess.PIPE, stderr=subprocess.PIPE,&quot;</code> |
| trinity_read.py:448 | BEYOND | ∅ (added file) | <code>&quot;                             universal_newlines=True, timeout=30, check=True)&quot;</code> |
| trinity_read.py:449 | BEYOND | ∅ (added file) | <code>&quot;    if sha(path) != digest: raise ValueError(&#x27;bwrap changed during version check&#x27;)&quot;</code> |
| trinity_read.py:450 | BEYOND | ∅ (added file) | <code>&quot;    return dict(path=path, sha256=digest, version=version.stdout, version_stderr=version.stderr)&quot;</code> |
| trinity_read.py:451 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:452 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:453 | BEYOND | ∅ (added file) | <code>&quot;def llguidance_evidence(enabled=True):&quot;</code> |
| trinity_read.py:454 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Authenticate the entire import-only overlay before exposing it to Python.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:455 | BEYOND | ∅ (added file) | <code>&quot;    evidence = dict(enabled=bool(enabled), path=str(LLG_STUB), target=str(LLG_TARGET),&quot;</code> |
| trinity_read.py:456 | BEYOND | ∅ (added file) | <code>&quot;                    sha256=dict(LLG_PINS), verified=False, version=2,&quot;</code> |
| trinity_read.py:457 | BEYOND | ∅ (added file) | <code>&quot;                    satisfies=[&#x27;llguidance&#x27;, &#x27;LLMatcher&#x27;, &#x27;LLTokenizer&#x27;, &#x27;LLInterpreter&#x27;,&quot;</code> |
| trinity_read.py:458 | BEYOND | ∅ (added file) | <code>&quot;                               &#x27;llguidance.hf (raises)&#x27;, &#x27;llguidance.torch (raises)&#x27;])&quot;</code> |
| trinity_read.py:459 | BEYOND | ∅ (added file) | <code>&quot;    if not enabled:&quot;</code> |
| trinity_read.py:460 | BEYOND | ∅ (added file) | <code>&quot;        return evidence&quot;</code> |
| trinity_read.py:461 | BEYOND | ∅ (added file) | <code>&quot;    if not LLG_STUB.is_dir() or LLG_STUB.is_symlink():&quot;</code> |
| trinity_read.py:462 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;llguidance stub directory missing or linked: &#x27;+str(LLG_STUB))&quot;</code> |
| trinity_read.py:463 | BEYOND | ∅ (added file) | <code>&quot;    if set(p.name for p in LLG_STUB.iterdir()) != set(LLG_PINS):&quot;</code> |
| trinity_read.py:464 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;llguidance stub inventory differs: &#x27;+str(LLG_STUB))&quot;</code> |
| trinity_read.py:465 | BEYOND | ∅ (added file) | <code>&quot;    for name, digest in LLG_PINS.items():&quot;</code> |
| trinity_read.py:466 | BEYOND | ∅ (added file) | <code>&quot;        path = LLG_STUB/name&quot;</code> |
| trinity_read.py:467 | BEYOND | ∅ (added file) | <code>&quot;        if path.is_symlink() or not path.is_file() or sha(path) != digest:&quot;</code> |
| trinity_read.py:468 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;llguidance stub pin mismatch: &#x27;+str(path))&quot;</code> |
| trinity_read.py:469 | BEYOND | ∅ (added file) | <code>&quot;    evidence[&#x27;verified&#x27;] = True&quot;</code> |
| trinity_read.py:470 | BEYOND | ∅ (added file) | <code>&quot;    return evidence&quot;</code> |
| trinity_read.py:471 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:472 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:473 | BEYOND | ∅ (added file) | <code>&quot;def namespace(root, gpu=False, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):&quot;</code> |
| trinity_read.py:474 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(root)&quot;</code> |
| trinity_read.py:475 | BEYOND | ∅ (added file) | <code>&quot;    overlay = llguidance_evidence(llguidance_stub)&quot;</code> |
| trinity_read.py:476 | BEYOND | ∅ (added file) | <code>&quot;    if overlay[&#x27;enabled&#x27;]:&quot;</code> |
| trinity_read.py:477 | BEYOND | ∅ (added file) | <code>&quot;        target = physical(root, LLG_TARGET)&quot;</code> |
| trinity_read.py:478 | BEYOND | ∅ (added file) | <code>&quot;        if not target.is_dir() or target.is_symlink() or target.resolve() != target:&quot;</code> |
| trinity_read.py:479 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;llguidance overlay requires an existing staged directory: &#x27;+str(target))&quot;</code> |
| trinity_read.py:480 | BEYOND | ∅ (added file) | <code>&quot;    argv = [bwrap_path(root, bwrap), &#x27;--unshare-net&#x27;]&quot;</code> |
| trinity_read.py:481 | BEYOND | ∅ (added file) | <code>&quot;    for name in (&#x27;usr&#x27;, &#x27;bin&#x27;, &#x27;sbin&#x27;, &#x27;lib&#x27;, &#x27;lib64&#x27;, &#x27;etc&#x27;, &#x27;opt&#x27;, &#x27;run&#x27;, &#x27;sys&#x27;):&quot;</code> |
| trinity_read.py:482 | BEYOND | ∅ (added file) | <code>&quot;        path = Path(&#x27;/&#x27;)/name&quot;</code> |
| trinity_read.py:483 | BEYOND | ∅ (added file) | <code>&quot;        if path.is_symlink(): argv += [&#x27;--symlink&#x27;, os.readlink(str(path)), str(path)]&quot;</code> |
| trinity_read.py:484 | BEYOND | ∅ (added file) | <code>&quot;        elif path.exists(): argv += [&#x27;--ro-bind&#x27;, str(path), str(path)]&quot;</code> |
| trinity_read.py:485 | BEYOND | ∅ (added file) | <code>&quot;    argv += ([&#x27;--dev-bind&#x27;, &#x27;/dev&#x27;, &#x27;/dev&#x27;] if gpu else [&#x27;--dev&#x27;, &#x27;/dev&#x27;])&quot;</code> |
| trinity_read.py:486 | PATH/ENV | ∅ (added file) | <code>&quot;    argv += [&#x27;--bind&#x27;, str(shm_directory(root, shm)), &#x27;/dev/shm&#x27;,&quot;</code> |
| trinity_read.py:487 | PATH/ENV | ∅ (added file) | <code>&quot;             &#x27;--proc&#x27;, &#x27;/proc&#x27;, &#x27;--bind&#x27;, str(root/&#x27;temp&#x27;), &#x27;/tmp&#x27;,&quot;</code> |
| trinity_read.py:488 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;--dir&#x27;, &#x27;/scratch&#x27;, &#x27;--bind&#x27;, str(root/&#x27;sj&#x27;), str(SJ),&quot;</code> |
| trinity_read.py:489 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;--bind&#x27;, str(root/&#x27;fsw&#x27;), str(FSW), &#x27;--dir&#x27;, &#x27;/lustre&#x27;,&quot;</code> |
| trinity_read.py:490 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;--bind&#x27;, str(root/&#x27;m/ap&#x27;), str(AP),&quot;</code> |
| trinity_read.py:491 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;--ro-bind&#x27;, str(root/&#x27;sj/uv-python/cpython-3.12.13-linux-x86_64-gnu&#x27;), UV,&quot;</code> |
| trinity_read.py:492 | PATH/ENV | ∅ (added file) | <code>&quot;             &#x27;--bind&#x27;, str(root), str(root), &#x27;--ro-bind&#x27;, str(root/&#x27;trinity_runner&#x27;), &#x27;/trinity-build&#x27;,&quot;</code> |
| trinity_read.py:493 | PATH/ENV | ∅ (added file) | <code>&quot;             &#x27;--ro-bind&#x27;, str(root/&#x27;k6tk&#x27;), STORE,&quot;</code> |
| trinity_read.py:494 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;--dir&#x27;, &#x27;/home/jjyeung&#x27;, &#x27;--die-with-parent&#x27;, &#x27;--chdir&#x27;, str(root)]&quot;</code> |
| trinity_read.py:495 | BEYOND | ∅ (added file) | <code>&quot;    if overlay[&#x27;enabled&#x27;]:&quot;</code> |
| trinity_read.py:496 | BEYOND | ∅ (added file) | <code>&quot;        argv += [&#x27;--ro-bind&#x27;, overlay[&#x27;path&#x27;], overlay[&#x27;target&#x27;]]&quot;</code> |
| trinity_read.py:497 | BEYOND | ∅ (added file) | <code>&quot;    return argv&quot;</code> |
| trinity_read.py:498 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:499 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:500 | PATH/ENV | ∅ (added file) | <code>&quot;def environment(root, gpu=&#x27;&#x27;, token=&#x27;cpu&#x27;, shm=None):&quot;</code> |
| trinity_read.py:501 | PATH/ENV | ∅ (added file) | <code>&quot;    shm_directory(root, shm)&quot;</code> |
| trinity_read.py:502 | PATH/ENV | ∅ (added file) | <code>&quot;    for name in (&#x27;cache&#x27;, &#x27;temp&#x27;, &#x27;home&#x27;, &#x27;k6tk&#x27;, &#x27;cache/hf&#x27;, &#x27;cache/triton&#x27;, &#x27;cache/torchinductor&#x27;, &#x27;cache/vllm&#x27;):&quot;</code> |
| trinity_read.py:503 | PATH/ENV | ∅ (added file) | <code>&quot;        (root/name).mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:504 | PATH/ENV | ∅ (added file) | <code>&quot;    return dict(PATH=&#x27;/usr/local/bin:/usr/bin:/bin&#x27;, USER=os.environ.get(&#x27;USER&#x27;, &#x27;jjyeung&#x27;),&quot;</code> |
| trinity_read.py:505 | BEYOND | ∅ (added file) | <code>&quot;                SLURM_JOB_ID=token, CUDA_VISIBLE_DEVICES=gpu, HOME=str(root/&#x27;home&#x27;), TMPDIR=str(root/&#x27;temp&#x27;),&quot;</code> |
| trinity_read.py:506 | PATH/ENV | ∅ (added file) | <code>&quot;                XDG_CACHE_HOME=str(root/&#x27;cache&#x27;), HF_HOME=str(root/&#x27;cache/hf&#x27;),&quot;</code> |
| trinity_read.py:507 | PATH/ENV | ∅ (added file) | <code>&quot;                TRITON_CACHE_DIR=str(root/&#x27;cache/triton&#x27;), TORCHINDUCTOR_CACHE_DIR=str(root/&#x27;cache/torchinductor&#x27;),&quot;</code> |
| trinity_read.py:508 | PATH/ENV | ∅ (added file) | <code>&quot;                VLLM_CACHE_ROOT=str(root/&#x27;cache/vllm&#x27;),&quot;</code> |
| trinity_read.py:509 | PATH/ENV | ∅ (added file) | <code>&quot;                HF_HUB_OFFLINE=&#x27;1&#x27;, TRANSFORMERS_OFFLINE=&#x27;1&#x27;, HF_HUB_DISABLE_TELEMETRY=&#x27;1&#x27;,&quot;</code> |
| trinity_read.py:510 | PATH/ENV | ∅ (added file) | <code>&quot;                TOKENIZERS_PARALLELISM=&#x27;false&#x27;, VLLM_NO_USAGE_STATS=&#x27;1&#x27;, DO_NOT_TRACK=&#x27;1&#x27;,&quot;</code> |
| trinity_read.py:511 | PATH/ENV | ∅ (added file) | <code>&quot;                VLLM_USE_FLASHINFER_SAMPLER=&#x27;0&#x27;, PYTHONDONTWRITEBYTECODE=&#x27;1&#x27;,&quot;</code> |
| trinity_read.py:512 | PATH/ENV | ∅ (added file) | <code>&quot;                OMP_NUM_THREADS=&#x27;8&#x27;, OPENBLAS_NUM_THREADS=&#x27;1&#x27;)&quot;</code> |
| trinity_read.py:513 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:514 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:515 | BEYOND | ∅ (added file) | <code>&quot;def require_stage(root):&quot;</code> |
| trinity_read.py:516 | BEYOND | ∅ (added file) | <code>&quot;    state = load(root/&#x27;STAGING.json&#x27;)&quot;</code> |
| trinity_read.py:517 | BEYOND | ∅ (added file) | <code>&quot;    if not state.get(&#x27;complete&#x27;): raise ValueError(&#x27;Stage incomplete: &#x27;+str(state.get(&#x27;missing&#x27;)))&quot;</code> |
| trinity_read.py:518 | BEYOND | ∅ (added file) | <code>&quot;    config = load(root/&#x27;bootstrap/CONFIG.json&#x27;)&quot;</code> |
| trinity_read.py:519 | BEYOND | ∅ (added file) | <code>&quot;    if sha(root/&#x27;bootstrap/payload.tar.gz&#x27;) != config[&#x27;payload_sha256&#x27;]:&quot;</code> |
| trinity_read.py:520 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Staged payload changed&#x27;)&quot;</code> |
| trinity_read.py:521 | BEYOND | ∅ (added file) | <code>&quot;    return config&quot;</code> |
| trinity_read.py:522 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:523 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:524 | BEYOND | ∅ (added file) | <code>&quot;def ns_command(root, config_path, script, args=(), gpu=False, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):&quot;</code> |
| trinity_read.py:525 | PATH/ENV | ∅ (added file) | <code>&quot;    config = load(config_path)&quot;</code> |
| trinity_read.py:526 | BEYOND | ∅ (added file) | <code>&quot;    return namespace(root, gpu, shm, bwrap, llguidance_stub)+[config[&#x27;spec&#x27;][&#x27;interpreters&#x27;][&#x27;vllm&#x27;] if gpu else config[&#x27;spec&#x27;][&#x27;interpreters&#x27;][&#x27;p1cpu&#x27;],&quot;</code> |
| trinity_read.py:527 | PATH/ENV | ∅ (added file) | <code>&quot;        &#x27;-s&#x27;, &#x27;-B&#x27;, str(root/&#x27;bootstrap/trace_runtime.py&#x27;), &#x27;--root&#x27;, str(root), &#x27;--config&#x27;, str(config_path),&quot;</code> |
| trinity_read.py:528 | PATH/ENV | ∅ (added file) | <code>&quot;        &#x27;--script&#x27;, str(script)]+list(args)&quot;</code> |
| trinity_read.py:529 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:530 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:531 | BEYOND | ∅ (added file) | <code>&quot;def selected_tasks(tasks, ids=None, first=None):&quot;</code> |
| trinity_read.py:532 | BEYOND | ∅ (added file) | <code>&quot;    if any(t[&#x27;benchmark&#x27;] != &#x27;devrows&#x27; for t in tasks):&quot;</code> |
| trinity_read.py:533 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Only dev-S1 direct items are admitted&#x27;)&quot;</code> |
| trinity_read.py:534 | BEYOND | ∅ (added file) | <code>&quot;    ordered = sorted(tasks, key=lambda t:(t[&#x27;benchmark&#x27;], t[&#x27;example_id&#x27;]))&quot;</code> |
| trinity_read.py:535 | BEYOND | ∅ (added file) | <code>&quot;    if len({t[&#x27;example_id&#x27;] for t in ordered}) != len(ordered):&quot;</code> |
| trinity_read.py:536 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Duplicate dev-S1 task IDs&#x27;)&quot;</code> |
| trinity_read.py:537 | BEYOND | ∅ (added file) | <code>&quot;    if ids is not None:&quot;</code> |
| trinity_read.py:538 | BEYOND | ∅ (added file) | <code>&quot;        if not ids or len(ids) != len(set(ids)):&quot;</code> |
| trinity_read.py:539 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Require a nonempty unique ID list&#x27;)&quot;</code> |
| trinity_read.py:540 | BEYOND | ∅ (added file) | <code>&quot;        unknown = set(ids)-{t[&#x27;example_id&#x27;] for t in ordered}&quot;</code> |
| trinity_read.py:541 | BEYOND | ∅ (added file) | <code>&quot;        if unknown: raise ValueError(&#x27;IDs outside the family dev-S1 direct set: &#x27;+&#x27;, &#x27;.join(sorted(unknown)))&quot;</code> |
| trinity_read.py:542 | BEYOND | ∅ (added file) | <code>&quot;        ordered = [t for t in ordered if t[&#x27;example_id&#x27;] in set(ids)]&quot;</code> |
| trinity_read.py:543 | BEYOND | ∅ (added file) | <code>&quot;    elif first is not None:&quot;</code> |
| trinity_read.py:544 | BEYOND | ∅ (added file) | <code>&quot;        if first &lt;= 0 or first &gt; len(ordered): raise ValueError(&#x27;--first exceeds the nonempty family set&#x27;)&quot;</code> |
| trinity_read.py:545 | BEYOND | ∅ (added file) | <code>&quot;        ordered = ordered[:first]&quot;</code> |
| trinity_read.py:546 | BEYOND | ∅ (added file) | <code>&quot;    return ordered&quot;</code> |
| trinity_read.py:547 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:548 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:549 | BEYOND | ∅ (added file) | <code>&quot;def needed(captures, tasks):&quot;</code> |
| trinity_read.py:550 | BEYOND | ∅ (added file) | <code>&quot;    return sorted({f[&#x27;sha256&#x27;] for t in tasks for f in captures[t[&#x27;native&#x27;]][&#x27;frames&#x27;]})&quot;</code> |
| trinity_read.py:551 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:552 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:553 | PATH/ENV | ∅ (added file) | <code>&quot;def read_ids(path):&quot;</code> |
| trinity_read.py:554 | PATH/ENV | ∅ (added file) | <code>&quot;    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]&quot;</code> |
| trinity_read.py:555 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:556 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:557 | BEYOND | ∅ (added file) | <code>&quot;def cpu_need(root, family, ids=None, first=None, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):&quot;</code> |
| trinity_read.py:558 | BEYOND | ∅ (added file) | <code>&quot;    config = require_stage(root)&quot;</code> |
| trinity_read.py:559 | BEYOND | ∅ (added file) | <code>&quot;    overlay = llguidance_evidence(llguidance_stub)&quot;</code> |
| trinity_read.py:560 | BEYOND | ∅ (added file) | <code>&quot;    install_runner(root)&quot;</code> |
| trinity_read.py:561 | BEYOND | ∅ (added file) | <code>&quot;    executed = bwrap_evidence(root, bwrap)&quot;</code> |
| trinity_read.py:562 | BEYOND | ∅ (added file) | <code>&quot;    work = root/&#x27;needs&#x27;/uuid.uuid4().hex; work.mkdir(parents=True)&quot;</code> |
| trinity_read.py:563 | BEYOND | ∅ (added file) | <code>&quot;    request = dict(action=&#x27;need&#x27;, family=family, ids=ids, first=first, work=str(work))&quot;</code> |
| trinity_read.py:564 | BEYOND | ∅ (added file) | <code>&quot;    dump(work/&#x27;INPUT.json&#x27;, request)&quot;</code> |
| trinity_read.py:565 | PATH/ENV | ∅ (added file) | <code>&quot;    env = environment(root, shm=shm)&quot;</code> |
| trinity_read.py:566 | BEYOND | ∅ (added file) | <code>&quot;    cmd = ns_command(root, root/&#x27;bootstrap/CONFIG.json&#x27;, &#x27;/trinity-build/namespace_worker.py&#x27;,&quot;</code> |
| trinity_read.py:567 | BEYOND | ∅ (added file) | <code>&quot;                     [&#x27;--input&#x27;, str(work/&#x27;INPUT.json&#x27;)], shm=shm, bwrap=executed[&#x27;path&#x27;], llguidance_stub=llguidance_stub)&quot;</code> |
| trinity_read.py:568 | BEYOND | ∅ (added file) | <code>&quot;    dump(work/&#x27;COMMAND.json&#x27;, dict(argv=cmd, bwrap=executed, llguidance_stub=overlay))&quot;</code> |
| trinity_read.py:569 | BEYOND | ∅ (added file) | <code>&quot;    started = time.monotonic(); code = None&quot;</code> |
| trinity_read.py:570 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:571 | BEYOND | ∅ (added file) | <code>&quot;        process = subprocess.run(cmd, env=env)&quot;</code> |
| trinity_read.py:572 | BEYOND | ∅ (added file) | <code>&quot;        code = process.returncode&quot;</code> |
| trinity_read.py:573 | BEYOND | ∅ (added file) | <code>&quot;        process.check_returncode()&quot;</code> |
| trinity_read.py:574 | BEYOND | ∅ (added file) | <code>&quot;    finally:&quot;</code> |
| trinity_read.py:575 | BEYOND | ∅ (added file) | <code>&quot;        dump(work/&#x27;EXIT.json&#x27;, dict(returncode=code, wall_seconds=time.monotonic()-started, bwrap=executed, llguidance_stub=overlay))&quot;</code> |
| trinity_read.py:576 | BEYOND | ∅ (added file) | <code>&quot;    result = load(work/&#x27;NEED.json&#x27;)&quot;</code> |
| trinity_read.py:577 | BEYOND | ∅ (added file) | <code>&quot;    result.update(bwrap=executed, llguidance_stub=overlay, evidence_directory=str(work))&quot;</code> |
| trinity_read.py:578 | BEYOND | ∅ (added file) | <code>&quot;    dump(work/&#x27;NEED.json&#x27;, result)&quot;</code> |
| trinity_read.py:579 | BEYOND | ∅ (added file) | <code>&quot;    return result&quot;</code> |
| trinity_read.py:580 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:581 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:582 | BEYOND | ∅ (added file) | <code>&quot;def need_command(args):&quot;</code> |
| trinity_read.py:583 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(args.root); results = {}&quot;</code> |
| trinity_read.py:584 | BEYOND | ∅ (added file) | <code>&quot;    for family in FAMILIES if args.all else (args.family,):&quot;</code> |
| trinity_read.py:585 | BEYOND | ∅ (added file) | <code>&quot;        results[family] = cpu_need(root, family, read_ids(args.ids) if args.ids else None,&quot;</code> |
| trinity_read.py:586 | BEYOND | ∅ (added file) | <code>&quot;                                   args.first if not args.all else None, None, args.bwrap, getattr(args, &#x27;llguidance_stub&#x27;, True))&quot;</code> |
| trinity_read.py:587 | BEYOND | ∅ (added file) | <code>&quot;    hashes = sorted({h for result in results.values() for h in result[&#x27;need&#x27;]})&quot;</code> |
| trinity_read.py:588 | BEYOND | ∅ (added file) | <code>&quot;    index = store_index(root); missing = sorted(set(hashes)-set(index))&quot;</code> |
| trinity_read.py:589 | BEYOND | ∅ (added file) | <code>&quot;    out = writable(args.out); out.parent.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:590 | BEYOND | ∅ (added file) | <code>&quot;    out.write_text(&#x27;&#x27;.join(h+&#x27;\\n&#x27; for h in hashes))&quot;</code> |
| trinity_read.py:591 | BEYOND | ∅ (added file) | <code>&quot;    Path(str(out)+&#x27;.missing&#x27;).write_text(&#x27;&#x27;.join(h+&#x27;\\n&#x27; for h in missing))&quot;</code> |
| trinity_read.py:592 | BEYOND | ∅ (added file) | <code>&quot;    report = dict(families=results, frames=len(hashes), missing=missing,&quot;</code> |
| trinity_read.py:593 | BEYOND | ∅ (added file) | <code>&quot;                  estimated_png_bytes=sum(max(r[&#x27;estimated_frame_bytes&#x27;].get(h, 0) for r in results.values()) for h in hashes),&quot;</code> |
| trinity_read.py:594 | BEYOND | ∅ (added file) | <code>&quot;                  estimate_basis=&#x27;Conservative uncompressed RGB bytes (height * width * 3); PNG and tar sizes vary.&#x27;)&quot;</code> |
| trinity_read.py:595 | BEYOND | ∅ (added file) | <code>&quot;    dump(str(out)+&#x27;.json&#x27;, report)&quot;</code> |
| trinity_read.py:596 | BEYOND | ∅ (added file) | <code>&quot;    print(json.dumps(dict(out=str(out), frames=len(hashes), absent=len(missing),&quot;</code> |
| trinity_read.py:597 | BEYOND | ∅ (added file) | <code>&quot;                         items={f:r[&#x27;items&#x27;] for f,r in results.items()}, estimated_bytes=report[&#x27;estimated_png_bytes&#x27;])))&quot;</code> |
| trinity_read.py:598 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:599 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:600 | PATH/ENV | ∅ (added file) | <code>&quot;def smi(arguments):&quot;</code> |
| trinity_read.py:601 | PATH/ENV | ∅ (added file) | <code>&quot;    return subprocess.check_output([&#x27;nvidia-smi&#x27;]+arguments, universal_newlines=True, timeout=30)&quot;</code> |
| trinity_read.py:602 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:603 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:604 | BEYOND | ∅ (added file) | <code>&quot;def check_card(index):&quot;</code> |
| trinity_read.py:605 | BEYOND | ∅ (added file) | <code>&quot;    if not re.fullmatch(&#x27;[0-9]+&#x27;, str(index)): raise ValueError(&#x27;--gpu requires one physical card index&#x27;)&quot;</code> |
| trinity_read.py:606 | BEYOND | ∅ (added file) | <code>&quot;    raw = smi([&#x27;-i&#x27;, str(index), &#x27;--query-gpu=index,uuid,name,memory.total,memory.used&#x27;, &#x27;--format=csv,noheader,nounits&#x27;])&quot;</code> |
| trinity_read.py:607 | BEYOND | ∅ (added file) | <code>&quot;    rows = list(csv.reader(raw.strip().splitlines()))&quot;</code> |
| trinity_read.py:608 | BEYOND | ∅ (added file) | <code>&quot;    if len(rows) != 1: raise ValueError(&#x27;Require exactly one selected visible GPU&#x27;)&quot;</code> |
| trinity_read.py:609 | BEYOND | ∅ (added file) | <code>&quot;    card_index, card_uuid, name, total, used = [x.strip() for x in rows[0]]&quot;</code> |
| trinity_read.py:610 | BEYOND | ∅ (added file) | <code>&quot;    processes = smi([&#x27;-i&#x27;, str(index), &#x27;--query-compute-apps=gpu_uuid,pid&#x27;, &#x27;--format=csv,noheader,nounits&#x27;])&quot;</code> |
| trinity_read.py:611 | BEYOND | ∅ (added file) | <code>&quot;    if card_index != str(index) or float(total) &lt; 40*1024 or float(used) &gt;= 100 or card_uuid in processes:&quot;</code> |
| trinity_read.py:612 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Card must have &gt;=40 GiB, &lt;100 MiB used, and no compute process&#x27;)&quot;</code> |
| trinity_read.py:613 | BEYOND | ∅ (added file) | <code>&quot;    return dict(index=card_index, uuid=card_uuid, name=name, total_mib=float(total), initial_used_mib=float(used))&quot;</code> |
| trinity_read.py:614 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:615 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:616 | BEYOND | ∅ (added file) | <code>&quot;class Sampler:&quot;</code> |
| trinity_read.py:617 | BEYOND | ∅ (added file) | <code>&quot;    def __init__(self, index, path):&quot;</code> |
| trinity_read.py:618 | BEYOND | ∅ (added file) | <code>&quot;        self.index, self.path = index, path&quot;</code> |
| trinity_read.py:619 | BEYOND | ∅ (added file) | <code>&quot;        self.stop = threading.Event(); self.errors = []&quot;</code> |
| trinity_read.py:620 | BEYOND | ∅ (added file) | <code>&quot;        self.thread = threading.Thread(target=self.run, daemon=True)&quot;</code> |
| trinity_read.py:621 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:622 | BEYOND | ∅ (added file) | <code>&quot;    def run(self):&quot;</code> |
| trinity_read.py:623 | BEYOND | ∅ (added file) | <code>&quot;        with self.path.open(&#x27;x&#x27;) as f:&quot;</code> |
| trinity_read.py:624 | BEYOND | ∅ (added file) | <code>&quot;            while not self.stop.is_set():&quot;</code> |
| trinity_read.py:625 | BEYOND | ∅ (added file) | <code>&quot;                start = time.monotonic()&quot;</code> |
| trinity_read.py:626 | BEYOND | ∅ (added file) | <code>&quot;                try:&quot;</code> |
| trinity_read.py:627 | BEYOND | ∅ (added file) | <code>&quot;                    value = float(smi([&#x27;-i&#x27;, self.index, &#x27;--query-gpu=memory.used&#x27;, &#x27;--format=csv,noheader,nounits&#x27;]).strip())&quot;</code> |
| trinity_read.py:628 | BEYOND | ∅ (added file) | <code>&quot;                    f.write(json.dumps(dict(time=time.time(), memory_used_mib=value))+&#x27;\\n&#x27;); f.flush()&quot;</code> |
| trinity_read.py:629 | BEYOND | ∅ (added file) | <code>&quot;                except Exception as error:&quot;</code> |
| trinity_read.py:630 | BEYOND | ∅ (added file) | <code>&quot;                    self.errors.append(str(error)); return&quot;</code> |
| trinity_read.py:631 | BEYOND | ∅ (added file) | <code>&quot;                self.stop.wait(max(0, 1-(time.monotonic()-start)))&quot;</code> |
| trinity_read.py:632 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:633 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:634 | BEYOND | ∅ (added file) | <code>&quot;def logical_artifact(root, value, step):&quot;</code> |
| trinity_read.py:635 | BEYOND | ∅ (added file) | <code>&quot;    path = Path(value)&quot;</code> |
| trinity_read.py:636 | BEYOND | ∅ (added file) | <code>&quot;    expected = LINEAGE/(&#x27;m&#x27;+str(step))/&#x27;artifact.json&#x27;&quot;</code> |
| trinity_read.py:637 | BEYOND | ∅ (added file) | <code>&quot;    if path == physical(root, expected): path = expected&quot;</code> |
| trinity_read.py:638 | BEYOND | ∅ (added file) | <code>&quot;    if step &lt;= 0 or path != expected:&quot;</code> |
| trinity_read.py:639 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Export must be the staged artifact.json of this lineage and step&#x27;)&quot;</code> |
| trinity_read.py:640 | BEYOND | ∅ (added file) | <code>&quot;    return str(path)&quot;</code> |
| trinity_read.py:641 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:642 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:643 | BEYOND | ∅ (added file) | <code>&quot;def read_space(root, config, plan):&quot;</code> |
| trinity_read.py:644 | BEYOND | ∅ (added file) | <code>&quot;    base_pin = config[&#x27;spec&#x27;][&#x27;models&#x27;][&#x27;base&#x27;][&#x27;manifest&#x27;]&quot;</code> |
| trinity_read.py:645 | BEYOND | ∅ (added file) | <code>&quot;    base_path = physical(root, base_pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:646 | BEYOND | ∅ (added file) | <code>&quot;    artifact_pin = config[&#x27;spec&#x27;][&#x27;artifact&#x27;]; artifact_path = physical(root, artifact_pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:647 | BEYOND | ∅ (added file) | <code>&quot;    if sha(base_path) != base_pin[&#x27;sha256&#x27;] or sha(artifact_path) != artifact_pin[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:648 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Model metadata pin differs before launch&#x27;)&quot;</code> |
| trinity_read.py:649 | BEYOND | ∅ (added file) | <code>&quot;    weight_pin = load(artifact_path)[&#x27;full_weights&#x27;]; weight_path = physical(root, weight_pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:650 | BEYOND | ∅ (added file) | <code>&quot;    if sha(weight_path) != weight_pin[&#x27;sha256&#x27;]:&quot;</code> |
| trinity_read.py:651 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Full-weights manifest differs before launch&#x27;)&quot;</code> |
| trinity_read.py:652 | BEYOND | ∅ (added file) | <code>&quot;    model_bytes = sum(row[&#x27;bytes&#x27;] for row in load(base_path)[&#x27;files&#x27;])+sum(row[&#x27;bytes&#x27;] for row in load(weight_path)[&#x27;files&#x27;])&quot;</code> |
| trinity_read.py:653 | BEYOND | ∅ (added file) | <code>&quot;    # The unchanged reader copies both models. Pulled PNGs also occupy a tar and an extracted tree.&quot;</code> |
| trinity_read.py:654 | BEYOND | ∅ (added file) | <code>&quot;    reserve = model_bytes+2*sum(plan[&#x27;estimated_frame_bytes&#x27;].values())+2*1024**3&quot;</code> |
| trinity_read.py:655 | BEYOND | ∅ (added file) | <code>&quot;    kit_stage().room(root, reserve)&quot;</code> |
| trinity_read.py:656 | BEYOND | ∅ (added file) | <code>&quot;    return reserve&quot;</code> |
| trinity_read.py:657 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:658 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:659 | BEYOND | ∅ (added file) | <code>&quot;def host_shm_ours(directory=Path(&#x27;/dev/shm&#x27;)):&quot;</code> |
| trinity_read.py:660 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Stat immediate children only, including symlinks without following them.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:661 | BEYOND | ∅ (added file) | <code>&quot;    rows = []&quot;</code> |
| trinity_read.py:662 | BEYOND | ∅ (added file) | <code>&quot;    for path in directory.iterdir():&quot;</code> |
| trinity_read.py:663 | BEYOND | ∅ (added file) | <code>&quot;        try: info = path.lstat()&quot;</code> |
| trinity_read.py:664 | BEYOND | ∅ (added file) | <code>&quot;        except FileNotFoundError: continue&quot;</code> |
| trinity_read.py:665 | BEYOND | ∅ (added file) | <code>&quot;        if info.st_uid == os.getuid():&quot;</code> |
| trinity_read.py:666 | BEYOND | ∅ (added file) | <code>&quot;            rows.append(dict(path=str(path), bytes=info.st_size))&quot;</code> |
| trinity_read.py:667 | BEYOND | ∅ (added file) | <code>&quot;    return sorted(rows, key=lambda row: row[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:668 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:669 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:670 | BEYOND | ∅ (added file) | <code>&quot;def yield_pattern(value):&quot;</code> |
| trinity_read.py:671 | BEYOND | ∅ (added file) | <code>&quot;    if value is None: return None&quot;</code> |
| trinity_read.py:672 | BEYOND | ∅ (added file) | <code>&quot;    # A single local directory avoids recursive or shared-filesystem polling.&quot;</code> |
| trinity_read.py:673 | BEYOND | ∅ (added file) | <code>&quot;    path = Path(value)&quot;</code> |
| trinity_read.py:674 | BEYOND | ∅ (added file) | <code>&quot;    if &#x27;**&#x27; in value or glob.has_magic(str(path.parent)):&quot;</code> |
| trinity_read.py:675 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;--yield-glob requires a fixed local parent and a nonrecursive filename glob&#x27;)&quot;</code> |
| trinity_read.py:676 | BEYOND | ∅ (added file) | <code>&quot;    return str(writable(path.parent)/path.name)&quot;</code> |
| trinity_read.py:677 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:678 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:679 | BEYOND | ∅ (added file) | <code>&quot;def disk_listing(directory):&quot;</code> |
| trinity_read.py:680 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Record metadata only; never follow a directory or file symlink.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:681 | BEYOND | ∅ (added file) | <code>&quot;    rows = []&quot;</code> |
| trinity_read.py:682 | BEYOND | ∅ (added file) | <code>&quot;    if not directory.exists(): return rows&quot;</code> |
| trinity_read.py:683 | BEYOND | ∅ (added file) | <code>&quot;    for parent, directories, files in os.walk(str(directory), followlinks=False):&quot;</code> |
| trinity_read.py:684 | BEYOND | ∅ (added file) | <code>&quot;        for name in sorted(directories+files):&quot;</code> |
| trinity_read.py:685 | BEYOND | ∅ (added file) | <code>&quot;            path = Path(parent)/name&quot;</code> |
| trinity_read.py:686 | BEYOND | ∅ (added file) | <code>&quot;            try:&quot;</code> |
| trinity_read.py:687 | BEYOND | ∅ (added file) | <code>&quot;                info = path.lstat()&quot;</code> |
| trinity_read.py:688 | BEYOND | ∅ (added file) | <code>&quot;                row = dict(path=str(path), bytes=info.st_size,&quot;</code> |
| trinity_read.py:689 | BEYOND | ∅ (added file) | <code>&quot;                           kind=&#x27;symlink&#x27; if stat.S_ISLNK(info.st_mode) else &#x27;directory&#x27; if stat.S_ISDIR(info.st_mode) else &#x27;file&#x27;)&quot;</code> |
| trinity_read.py:690 | BEYOND | ∅ (added file) | <code>&quot;                if stat.S_ISLNK(info.st_mode): row[&#x27;target&#x27;] = os.readlink(str(path))&quot;</code> |
| trinity_read.py:691 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(row)&quot;</code> |
| trinity_read.py:692 | BEYOND | ∅ (added file) | <code>&quot;            except FileNotFoundError:&quot;</code> |
| trinity_read.py:693 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(path=str(path), bytes=None, kind=&#x27;vanished&#x27;))&quot;</code> |
| trinity_read.py:694 | BEYOND | ∅ (added file) | <code>&quot;    return sorted(rows, key=lambda row: row[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:695 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:696 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:697 | BEYOND | ∅ (added file) | <code>&quot;def stop_group(process, grace=60):&quot;</code> |
| trinity_read.py:698 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Only signal the session/process group created by run_reader.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:699 | BEYOND | ∅ (added file) | <code>&quot;    group = process.pid&quot;</code> |
| trinity_read.py:700 | BEYOND | ∅ (added file) | <code>&quot;    if group &lt;= 1 or group == os.getpgrp():&quot;</code> |
| trinity_read.py:701 | BEYOND | ∅ (added file) | <code>&quot;        raise RuntimeError(&#x27;Refuse to signal the wrapper process group&#x27;)&quot;</code> |
| trinity_read.py:702 | BEYOND | ∅ (added file) | <code>&quot;    try: os.killpg(group, signal.SIGTERM)&quot;</code> |
| trinity_read.py:703 | BEYOND | ∅ (added file) | <code>&quot;    except ProcessLookupError: return process.wait()&quot;</code> |
| trinity_read.py:704 | BEYOND | ∅ (added file) | <code>&quot;    # Do not reap the leader until escalation ends: its PID cannot be recycled.&quot;</code> |
| trinity_read.py:705 | BEYOND | ∅ (added file) | <code>&quot;    time.sleep(grace)&quot;</code> |
| trinity_read.py:706 | BEYOND | ∅ (added file) | <code>&quot;    try: os.killpg(group, signal.SIGKILL)&quot;</code> |
| trinity_read.py:707 | BEYOND | ∅ (added file) | <code>&quot;    except ProcessLookupError: pass&quot;</code> |
| trinity_read.py:708 | BEYOND | ∅ (added file) | <code>&quot;    return process.wait()&quot;</code> |
| trinity_read.py:709 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:710 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:711 | BEYOND | ∅ (added file) | <code>&quot;def run_reader(command, env, root, log, pattern=None):&quot;</code> |
| trinity_read.py:712 | BEYOND | ∅ (added file) | <code>&quot;    process = subprocess.Popen(command, env=env, cwd=str(root), stdout=log,&quot;</code> |
| trinity_read.py:713 | BEYOND | ∅ (added file) | <code>&quot;                               stderr=subprocess.STDOUT, start_new_session=True)&quot;</code> |
| trinity_read.py:714 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:715 | BEYOND | ∅ (added file) | <code>&quot;        while True:&quot;</code> |
| trinity_read.py:716 | BEYOND | ∅ (added file) | <code>&quot;            if pattern:&quot;</code> |
| trinity_read.py:717 | BEYOND | ∅ (added file) | <code>&quot;                matches = []&quot;</code> |
| trinity_read.py:718 | BEYOND | ∅ (added file) | <code>&quot;                for name in glob.glob(pattern):&quot;</code> |
| trinity_read.py:719 | BEYOND | ∅ (added file) | <code>&quot;                    try:&quot;</code> |
| trinity_read.py:720 | BEYOND | ∅ (added file) | <code>&quot;                        if stat.S_ISREG(Path(name).lstat().st_mode): matches.append(name)&quot;</code> |
| trinity_read.py:721 | BEYOND | ∅ (added file) | <code>&quot;                    except FileNotFoundError: pass&quot;</code> |
| trinity_read.py:722 | BEYOND | ∅ (added file) | <code>&quot;                if matches:&quot;</code> |
| trinity_read.py:723 | BEYOND | ∅ (added file) | <code>&quot;                    event = dict(matched_file=sorted(matches)[0], time=time.time(),&quot;</code> |
| trinity_read.py:724 | BEYOND | ∅ (added file) | <code>&quot;                                 utc=time.strftime(&#x27;%Y-%m-%dT%H:%M:%SZ&#x27;, time.gmtime()), process_group=process.pid)&quot;</code> |
| trinity_read.py:725 | BEYOND | ∅ (added file) | <code>&quot;                    stop_group(process)&quot;</code> |
| trinity_read.py:726 | BEYOND | ∅ (added file) | <code>&quot;                    return 75, event&quot;</code> |
| trinity_read.py:727 | BEYOND | ∅ (added file) | <code>&quot;            try: return process.wait(timeout=30 if pattern else None), None&quot;</code> |
| trinity_read.py:728 | BEYOND | ∅ (added file) | <code>&quot;            except subprocess.TimeoutExpired: pass&quot;</code> |
| trinity_read.py:729 | BEYOND | ∅ (added file) | <code>&quot;    except BaseException:&quot;</code> |
| trinity_read.py:730 | BEYOND | ∅ (added file) | <code>&quot;        stop_group(process)&quot;</code> |
| trinity_read.py:731 | BEYOND | ∅ (added file) | <code>&quot;        raise&quot;</code> |
| trinity_read.py:732 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:733 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:734 | BEYOND | ∅ (added file) | <code>&quot;SMALL_FILE_BYTES = 1024*1024&quot;</code> |
| trinity_read.py:735 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:736 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:737 | BEYOND | ∅ (added file) | <code>&quot;def cheap_verify(root, rows):&quot;</code> |
| trinity_read.py:738 | BEYOND | ∅ (added file) | <code>&quot;    result = dict(files=0, hashed=0, size_only=0, errors=[])&quot;</code> |
| trinity_read.py:739 | BEYOND | ∅ (added file) | <code>&quot;    for relative, pin in sorted(rows.items()):&quot;</code> |
| trinity_read.py:740 | BEYOND | ∅ (added file) | <code>&quot;        path = root/relative&quot;</code> |
| trinity_read.py:741 | BEYOND | ∅ (added file) | <code>&quot;        try:&quot;</code> |
| trinity_read.py:742 | BEYOND | ∅ (added file) | <code>&quot;            if Path(relative).is_absolute() or &#x27;..&#x27; in Path(relative).parts or not inside(path.resolve(), root):&quot;</code> |
| trinity_read.py:743 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Inventory path escapes root&#x27;)&quot;</code> |
| trinity_read.py:744 | BEYOND | ∅ (added file) | <code>&quot;            info = path.stat()&quot;</code> |
| trinity_read.py:745 | BEYOND | ∅ (added file) | <code>&quot;            if not stat.S_ISREG(info.st_mode): raise ValueError(&#x27;Not a regular file&#x27;)&quot;</code> |
| trinity_read.py:746 | BEYOND | ∅ (added file) | <code>&quot;            if &#x27;bytes&#x27; in pin and info.st_size != pin[&#x27;bytes&#x27;]: raise ValueError(&#x27;Size differs&#x27;)&quot;</code> |
| trinity_read.py:747 | BEYOND | ∅ (added file) | <code>&quot;            if info.st_size &lt;= SMALL_FILE_BYTES:&quot;</code> |
| trinity_read.py:748 | BEYOND | ∅ (added file) | <code>&quot;                if sha(path) != pin[&#x27;sha256&#x27;]: raise ValueError(&#x27;SHA256 differs&#x27;)&quot;</code> |
| trinity_read.py:749 | BEYOND | ∅ (added file) | <code>&quot;                result[&#x27;hashed&#x27;] += 1&quot;</code> |
| trinity_read.py:750 | BEYOND | ∅ (added file) | <code>&quot;            elif &#x27;bytes&#x27; not in pin:&quot;</code> |
| trinity_read.py:751 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;No recorded size for large file&#x27;)&quot;</code> |
| trinity_read.py:752 | BEYOND | ∅ (added file) | <code>&quot;            else: result[&#x27;size_only&#x27;] += 1&quot;</code> |
| trinity_read.py:753 | BEYOND | ∅ (added file) | <code>&quot;            result[&#x27;files&#x27;] += 1&quot;</code> |
| trinity_read.py:754 | BEYOND | ∅ (added file) | <code>&quot;        except (OSError, ValueError) as error:&quot;</code> |
| trinity_read.py:755 | BEYOND | ∅ (added file) | <code>&quot;            result[&#x27;errors&#x27;].append(dict(path=str(path), error=str(error)))&quot;</code> |
| trinity_read.py:756 | BEYOND | ∅ (added file) | <code>&quot;    return result&quot;</code> |
| trinity_read.py:757 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:758 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:759 | BEYOND | ∅ (added file) | <code>&quot;def config_audit(root):&quot;</code> |
| trinity_read.py:760 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Separate authenticated, unused evidence from paths consumed by the runner.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:761 | BEYOND | ∅ (added file) | <code>&quot;    rows = []; links = []; accepted = {}&quot;</code> |
| trinity_read.py:762 | BEYOND | ∅ (added file) | <code>&quot;    systems = (&#x27;/usr&#x27;, &#x27;/bin&#x27;, &#x27;/sbin&#x27;, &#x27;/lib&#x27;, &#x27;/lib64&#x27;, &#x27;/etc&#x27;, &#x27;/opt&#x27;, &#x27;/run&#x27;, &#x27;/sys&#x27;, &#x27;/dev&#x27;, &#x27;/proc&#x27;)&quot;</code> |
| trinity_read.py:763 | BEYOND | ∅ (added file) | <code>&quot;    bootstrap = root/&#x27;bootstrap/CONFIG.json&#x27;&quot;</code> |
| trinity_read.py:764 | BEYOND | ∅ (added file) | <code>&quot;    authenticated = bootstrap.is_file() and sha(bootstrap) == ACCEPTED_CONFIG_SHA256&quot;</code> |
| trinity_read.py:765 | BEYOND | ∅ (added file) | <code>&quot;    def flatten(value, location=&#x27;$&#x27;):&quot;</code> |
| trinity_read.py:766 | BEYOND | ∅ (added file) | <code>&quot;        if isinstance(value, dict):&quot;</code> |
| trinity_read.py:767 | BEYOND | ∅ (added file) | <code>&quot;            for key, item in value.items():&quot;</code> |
| trinity_read.py:768 | BEYOND | ∅ (added file) | <code>&quot;                for entry in flatten(item, location+&#x27;.&#x27;+str(key)): yield entry&quot;</code> |
| trinity_read.py:769 | BEYOND | ∅ (added file) | <code>&quot;        elif isinstance(value, list):&quot;</code> |
| trinity_read.py:770 | BEYOND | ∅ (added file) | <code>&quot;            for index, item in enumerate(value):&quot;</code> |
| trinity_read.py:771 | BEYOND | ∅ (added file) | <code>&quot;                for entry in flatten(item, location+&#x27;[&#x27;+str(index)+&#x27;]&#x27;): yield entry&quot;</code> |
| trinity_read.py:772 | BEYOND | ∅ (added file) | <code>&quot;        elif isinstance(value, str): yield location, value&quot;</code> |
| trinity_read.py:773 | BEYOND | ∅ (added file) | <code>&quot;    if authenticated: accepted = dict(flatten(load(bootstrap)))&quot;</code> |
| trinity_read.py:774 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:775 | BEYOND | ∅ (added file) | <code>&quot;    def mapped_path(value):&quot;</code> |
| trinity_read.py:776 | BEYOND | ∅ (added file) | <code>&quot;        path = Path(os.path.normpath(value))&quot;</code> |
| trinity_read.py:777 | BEYOND | ∅ (added file) | <code>&quot;        if inside(path, root): return path&quot;</code> |
| trinity_read.py:778 | BEYOND | ∅ (added file) | <code>&quot;        for prefix, target in ((Path(UV), root/&#x27;sj/uv-python/cpython-3.12.13-linux-x86_64-gnu&#x27;),&quot;</code> |
| trinity_read.py:779 | BEYOND | ∅ (added file) | <code>&quot;                               (SJ, root/&#x27;sj&#x27;), (FSW, root/&#x27;fsw&#x27;), (AP, root/&#x27;m/ap&#x27;),&quot;</code> |
| trinity_read.py:780 | BEYOND | ∅ (added file) | <code>&quot;                               (Path(STORE), root/&#x27;k6tk&#x27;), (Path(&#x27;/tmp&#x27;), root/&#x27;temp&#x27;),&quot;</code> |
| trinity_read.py:781 | BEYOND | ∅ (added file) | <code>&quot;                               (Path(&#x27;/dev/shm&#x27;), root/&#x27;shm&#x27;)):&quot;</code> |
| trinity_read.py:782 | BEYOND | ∅ (added file) | <code>&quot;            if inside(path, prefix): return target/path.relative_to(prefix)&quot;</code> |
| trinity_read.py:783 | BEYOND | ∅ (added file) | <code>&quot;        return path&quot;</code> |
| trinity_read.py:784 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:785 | BEYOND | ∅ (added file) | <code>&quot;    def path_check(value):&quot;</code> |
| trinity_read.py:786 | BEYOND | ∅ (added file) | <code>&quot;        mapped = mapped_path(value)&quot;</code> |
| trinity_read.py:787 | BEYOND | ∅ (added file) | <code>&quot;        resolved = mapped.resolve()&quot;</code> |
| trinity_read.py:788 | BEYOND | ∅ (added file) | <code>&quot;        allowed = any(inside(resolved, Path(p).resolve()) for p in (str(root), &#x27;/data3/shared/scripts/vnice&#x27;)+systems)&quot;</code> |
| trinity_read.py:789 | BEYOND | ∅ (added file) | <code>&quot;        return str(mapped), allowed&quot;</code> |
| trinity_read.py:790 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:791 | BEYOND | ∅ (added file) | <code>&quot;    def active(location, filename):&quot;</code> |
| trinity_read.py:792 | BEYOND | ∅ (added file) | <code>&quot;        # Assets/archive transport, phase-A inputs, release records and launcher&quot;</code> |
| trinity_read.py:793 | BEYOND | ∅ (added file) | <code>&quot;        # receipts remain data. These fields alone reach the direct runner.&quot;</code> |
| trinity_read.py:794 | BEYOND | ∅ (added file) | <code>&quot;        return (location == &#x27;$.spec.package&#x27; or location == &#x27;$.assets.base_manifest.path&#x27;&quot;</code> |
| trinity_read.py:795 | BEYOND | ∅ (added file) | <code>&quot;                or location.startswith((&#x27;$.spec.artifact.&#x27;, &#x27;$.spec.models.&#x27;, &#x27;$.spec.interpreters.&#x27;))&quot;</code> |
| trinity_read.py:796 | BEYOND | ∅ (added file) | <code>&quot;                or (location in (&#x27;$.output&#x27;, &#x27;$.spec.run&#x27;) and filename != str(bootstrap)))&quot;</code> |
| trinity_read.py:797 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:798 | BEYOND | ∅ (added file) | <code>&quot;    def visit(value, filename):&quot;</code> |
| trinity_read.py:799 | BEYOND | ∅ (added file) | <code>&quot;        for location, item in flatten(value):&quot;</code> |
| trinity_read.py:800 | BEYOND | ∅ (added file) | <code>&quot;            path = item.startswith(&#x27;/&#x27;)&quot;</code> |
| trinity_read.py:801 | BEYOND | ∅ (added file) | <code>&quot;            host = bool(re.search(r&#x27;\\b(?:trinity(?:-\\d+-\\d+)?|orchard-login-\\d+)\\b&#x27;, item))&quot;</code> |
| trinity_read.py:802 | BEYOND | ∅ (added file) | <code>&quot;            pinned = accepted.get(location) == item&quot;</code> |
| trinity_read.py:803 | BEYOND | ∅ (added file) | <code>&quot;            if location == &#x27;$.spec.llguidance_stub.path&#x27; and item == str(LLG_STUB):&quot;</code> |
| trinity_read.py:804 | BEYOND | ∅ (added file) | <code>&quot;                try:&quot;</code> |
| trinity_read.py:805 | BEYOND | ∅ (added file) | <code>&quot;                    llguidance_evidence(value.get(&#x27;spec&#x27;, {}).get(&#x27;llguidance_stub&#x27;, {}).get(&#x27;enabled&#x27;, False))&quot;</code> |
| trinity_read.py:806 | BEYOND | ∅ (added file) | <code>&quot;                    valid = True&quot;</code> |
| trinity_read.py:807 | BEYOND | ∅ (added file) | <code>&quot;                except (ValueError, OSError):&quot;</code> |
| trinity_read.py:808 | BEYOND | ∅ (added file) | <code>&quot;                    valid = False&quot;</code> |
| trinity_read.py:809 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(file=filename, field=location, value=item, kind=&#x27;pinned_overlay&#x27;, fails=not valid))&quot;</code> |
| trinity_read.py:810 | BEYOND | ∅ (added file) | <code>&quot;            elif pinned and (not path or not active(location, filename)):&quot;</code> |
| trinity_read.py:811 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(file=filename, field=location, value=item, kind=&#x27;pinned_evidence&#x27;, fails=False))&quot;</code> |
| trinity_read.py:812 | BEYOND | ∅ (added file) | <code>&quot;            elif path:&quot;</code> |
| trinity_read.py:813 | BEYOND | ∅ (added file) | <code>&quot;                mapped, allowed = path_check(item)&quot;</code> |
| trinity_read.py:814 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(file=filename, field=location, value=item, mapped_path=mapped,&quot;</code> |
| trinity_read.py:815 | BEYOND | ∅ (added file) | <code>&quot;                                 kind=(&#x27;namespace_alias&#x27; if mapped != item else &#x27;allowed_path&#x27;) if allowed else &#x27;external_path&#x27;,&quot;</code> |
| trinity_read.py:816 | BEYOND | ∅ (added file) | <code>&quot;                                 fails=not allowed))&quot;</code> |
| trinity_read.py:817 | BEYOND | ∅ (added file) | <code>&quot;            elif host:&quot;</code> |
| trinity_read.py:818 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(file=filename, field=location, value=item, kind=&#x27;metadata&#x27;, fails=False))&quot;</code> |
| trinity_read.py:819 | BEYOND | ∅ (added file) | <code>&quot;    for parent, directories, files in os.walk(str(root), followlinks=False):&quot;</code> |
| trinity_read.py:820 | BEYOND | ∅ (added file) | <code>&quot;        for name in directories+files:&quot;</code> |
| trinity_read.py:821 | BEYOND | ∅ (added file) | <code>&quot;            if name.startswith(&#x27;.&#x27;): continue&quot;</code> |
| trinity_read.py:822 | BEYOND | ∅ (added file) | <code>&quot;            path = Path(parent)/name&quot;</code> |
| trinity_read.py:823 | BEYOND | ∅ (added file) | <code>&quot;            if path.is_symlink():&quot;</code> |
| trinity_read.py:824 | BEYOND | ∅ (added file) | <code>&quot;                target = os.readlink(str(path))&quot;</code> |
| trinity_read.py:825 | BEYOND | ∅ (added file) | <code>&quot;                logical = target if target.startswith(&#x27;/&#x27;) else os.path.normpath(str(path.parent/target))&quot;</code> |
| trinity_read.py:826 | BEYOND | ∅ (added file) | <code>&quot;                mapped, allowed = path_check(logical)&quot;</code> |
| trinity_read.py:827 | BEYOND | ∅ (added file) | <code>&quot;                links.append(dict(path=str(path), target=target, mapped_path=mapped, allowed=allowed))&quot;</code> |
| trinity_read.py:828 | BEYOND | ∅ (added file) | <code>&quot;        directories[:] = [d for d in directories if not d.startswith(&#x27;.&#x27;) and not (Path(parent)/d).is_symlink()]&quot;</code> |
| trinity_read.py:829 | BEYOND | ∅ (added file) | <code>&quot;        if &#x27;CONFIG.json&#x27; in files:&quot;</code> |
| trinity_read.py:830 | BEYOND | ∅ (added file) | <code>&quot;            path = Path(parent)/&#x27;CONFIG.json&#x27;&quot;</code> |
| trinity_read.py:831 | BEYOND | ∅ (added file) | <code>&quot;            if path.is_symlink():&quot;</code> |
| trinity_read.py:832 | BEYOND | ∅ (added file) | <code>&quot;                mapped, allowed = path_check(str(path))&quot;</code> |
| trinity_read.py:833 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(file=str(path), kind=&#x27;config_symlink&#x27;, value=os.readlink(str(path)), fails=not allowed))&quot;</code> |
| trinity_read.py:834 | BEYOND | ∅ (added file) | <code>&quot;                if allowed and path.is_file() and path.stat().st_size &lt;= 4*1024**2: visit(load(path), str(path))&quot;</code> |
| trinity_read.py:835 | BEYOND | ∅ (added file) | <code>&quot;            elif path.stat().st_size &gt; 4*1024**2:&quot;</code> |
| trinity_read.py:836 | BEYOND | ∅ (added file) | <code>&quot;                rows.append(dict(file=str(path), kind=&#x27;config_too_large_to_audit&#x27;, fails=True))&quot;</code> |
| trinity_read.py:837 | BEYOND | ∅ (added file) | <code>&quot;            else: visit(load(path), str(path))&quot;</code> |
| trinity_read.py:838 | BEYOND | ∅ (added file) | <code>&quot;    passed = not any(r[&#x27;fails&#x27;] for r in rows) and not any(not r[&#x27;allowed&#x27;] for r in links)&quot;</code> |
| trinity_read.py:839 | BEYOND | ∅ (added file) | <code>&quot;    return dict(passed=passed, findings=rows, symlinks=links, pinned_template_authenticated=authenticated,&quot;</code> |
| trinity_read.py:840 | BEYOND | ∅ (added file) | <code>&quot;                scope=&#x27;CONFIG string values and symlink targets; pinned evidence is informational. Active aliases resolve into root; large files receive no content scan.&#x27;)&quot;</code> |
| trinity_read.py:841 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:842 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:843 | PATH/ENV | ∅ (added file) | <code>&quot;def selfcheck(root, bwrap=DEFAULT_BWRAP):&quot;</code> |
| trinity_read.py:844 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(root); state = load(root/&#x27;STAGING.json&#x27;); config = load(root/&#x27;bootstrap/CONFIG.json&#x27;)&quot;</code> |
| trinity_read.py:845 | BEYOND | ∅ (added file) | <code>&quot;    checks = {}; rows = {}; unverifiable = []&quot;</code> |
| trinity_read.py:846 | BEYOND | ∅ (added file) | <code>&quot;    missing = sorted(REQUIRED_PIECES-set(state[&#x27;pieces&#x27;]))&quot;</code> |
| trinity_read.py:847 | BEYOND | ∅ (added file) | <code>&quot;    overlays = state[&#x27;pieces&#x27;].get(&#x27;reader_payload&#x27;, {}).get(&#x27;evidence&#x27;, {}).get(&#x27;inventory&#x27;, {})&quot;</code> |
| trinity_read.py:848 | BEYOND | ∅ (added file) | <code>&quot;    for name, item in sorted(state[&#x27;pieces&#x27;].items()):&quot;</code> |
| trinity_read.py:849 | BEYOND | ∅ (added file) | <code>&quot;        if item[&#x27;status&#x27;] != &#x27;complete&#x27;:&quot;</code> |
| trinity_read.py:850 | BEYOND | ∅ (added file) | <code>&quot;            unverifiable.append(name+&#x27;: partial&#x27;); continue&quot;</code> |
| trinity_read.py:851 | BEYOND | ∅ (added file) | <code>&quot;        evidence = item[&#x27;evidence&#x27;]; current = {}&quot;</code> |
| trinity_read.py:852 | BEYOND | ∅ (added file) | <code>&quot;        if name == &#x27;bootstrap&#x27;:&quot;</code> |
| trinity_read.py:853 | BEYOND | ∅ (added file) | <code>&quot;            if evidence[&#x27;payload_sha256&#x27;] != config[&#x27;payload_sha256&#x27;]:&quot;</code> |
| trinity_read.py:854 | BEYOND | ∅ (added file) | <code>&quot;                unverifiable.append(&#x27;bootstrap: payload pin differs from STAGING.json&#x27;)&quot;</code> |
| trinity_read.py:855 | BEYOND | ∅ (added file) | <code>&quot;            # Small bootstrap archive and launcher files have authoritative hashes.&quot;</code> |
| trinity_read.py:856 | BEYOND | ∅ (added file) | <code>&quot;            for filename, digest in config[&#x27;launcher_pins&#x27;].items():&quot;</code> |
| trinity_read.py:857 | BEYOND | ∅ (added file) | <code>&quot;                current[&#x27;bootstrap/&#x27;+Path(filename).name] = dict(sha256=digest)&quot;</code> |
| trinity_read.py:858 | BEYOND | ∅ (added file) | <code>&quot;            current[&#x27;bootstrap/REVIEW.json&#x27;] = dict(sha256=config[&#x27;launcher_review_pin&#x27;][&#x27;sha256&#x27;])&quot;</code> |
| trinity_read.py:859 | BEYOND | ∅ (added file) | <code>&quot;            payload = root/&#x27;bootstrap/payload.tar.gz&#x27;&quot;</code> |
| trinity_read.py:860 | BEYOND | ∅ (added file) | <code>&quot;            checks[&#x27;bootstrap_payload&#x27;] = dict(passed=sha(payload) == evidence[&#x27;payload_sha256&#x27;])&quot;</code> |
| trinity_read.py:861 | BEYOND | ∅ (added file) | <code>&quot;        elif name == &#x27;bwrap&#x27;:&quot;</code> |
| trinity_read.py:862 | BEYOND | ∅ (added file) | <code>&quot;            current[&#x27;bwrap&#x27;] = dict(config[&#x27;assets&#x27;][&#x27;bwrap_pin&#x27;])&quot;</code> |
| trinity_read.py:863 | BEYOND | ∅ (added file) | <code>&quot;            # bwrap is small enough to authenticate explicitly despite the metadata threshold.&quot;</code> |
| trinity_read.py:864 | BEYOND | ∅ (added file) | <code>&quot;            checks[&#x27;bwrap_hash&#x27;] = dict(passed=sha(root/&#x27;bwrap&#x27;) == evidence[&#x27;sha256&#x27;])&quot;</code> |
| trinity_read.py:865 | BEYOND | ∅ (added file) | <code>&quot;        elif name == &#x27;export&#x27;:&quot;</code> |
| trinity_read.py:866 | BEYOND | ∅ (added file) | <code>&quot;            pin = config[&#x27;spec&#x27;][&#x27;artifact&#x27;]; artifact = physical(root, pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:867 | BEYOND | ∅ (added file) | <code>&quot;            current[str(artifact.relative_to(root))] = dict(sha256=evidence[&#x27;artifact_sha256&#x27;])&quot;</code> |
| trinity_read.py:868 | BEYOND | ∅ (added file) | <code>&quot;            weight = load(artifact)[&#x27;full_weights&#x27;]; manifest = physical(root, weight[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:869 | BEYOND | ∅ (added file) | <code>&quot;            current[str(manifest.relative_to(root))] = dict(sha256=evidence[&#x27;full_weights_sha256&#x27;])&quot;</code> |
| trinity_read.py:870 | BEYOND | ∅ (added file) | <code>&quot;            for row in [load(manifest)[&#x27;index&#x27;]]+load(manifest)[&#x27;files&#x27;]:&quot;</code> |
| trinity_read.py:871 | BEYOND | ∅ (added file) | <code>&quot;                current[str((manifest.parent/row[&#x27;name&#x27;]).relative_to(root))] = row&quot;</code> |
| trinity_read.py:872 | BEYOND | ∅ (added file) | <code>&quot;        elif name == &#x27;base&#x27;:&quot;</code> |
| trinity_read.py:873 | BEYOND | ∅ (added file) | <code>&quot;            pin = config[&#x27;assets&#x27;][&#x27;base_manifest&#x27;]; manifest = physical(root, pin[&#x27;path&#x27;])&quot;</code> |
| trinity_read.py:874 | BEYOND | ∅ (added file) | <code>&quot;            current[str(manifest.relative_to(root))] = dict(sha256=evidence[&#x27;manifest_sha256&#x27;])&quot;</code> |
| trinity_read.py:875 | BEYOND | ∅ (added file) | <code>&quot;            for row in load(manifest)[&#x27;files&#x27;]:&quot;</code> |
| trinity_read.py:876 | BEYOND | ∅ (added file) | <code>&quot;                current[&#x27;m/ap/85fc3486/&#x27;+row[&#x27;path&#x27;]] = row&quot;</code> |
| trinity_read.py:877 | BEYOND | ∅ (added file) | <code>&quot;        elif &#x27;inventory&#x27; in evidence:&quot;</code> |
| trinity_read.py:878 | BEYOND | ∅ (added file) | <code>&quot;            current = {p:pin for p,pin in evidence[&#x27;inventory&#x27;].items() if name == &#x27;reader_payload&#x27; or p not in overlays}&quot;</code> |
| trinity_read.py:879 | BEYOND | ∅ (added file) | <code>&quot;        else:&quot;</code> |
| trinity_read.py:880 | BEYOND | ∅ (added file) | <code>&quot;            unverifiable.append(name+&#x27;: STAGING.json has no extracted-file inventory&#x27;)&quot;</code> |
| trinity_read.py:881 | BEYOND | ∅ (added file) | <code>&quot;        rows.update(current)&quot;</code> |
| trinity_read.py:882 | BEYOND | ∅ (added file) | <code>&quot;    checks[&#x27;pieces&#x27;] = cheap_verify(root, rows)&quot;</code> |
| trinity_read.py:883 | BEYOND | ∅ (added file) | <code>&quot;    manifest = root/&#x27;trinity_runner/MANIFEST.json&#x27;&quot;</code> |
| trinity_read.py:884 | BEYOND | ∅ (added file) | <code>&quot;    if manifest.exists():&quot;</code> |
| trinity_read.py:885 | BEYOND | ∅ (added file) | <code>&quot;        checks[&#x27;runner&#x27;] = cheap_verify(root, {&#x27;trinity_runner/&#x27;+p:pin for p,pin in load(manifest).items()})&quot;</code> |
| trinity_read.py:886 | BEYOND | ∅ (added file) | <code>&quot;    else: unverifiable.append(&#x27;trinity_runner: not installed; run stage from build before copying&#x27;)&quot;</code> |
| trinity_read.py:887 | BEYOND | ∅ (added file) | <code>&quot;    # This probe needs no staged interpreter, model, frame, cache, or GPU device.&quot;</code> |
| trinity_read.py:888 | BEYOND | ∅ (added file) | <code>&quot;    executed = bwrap_evidence(root, bwrap)&quot;</code> |
| trinity_read.py:889 | BEYOND | ∅ (added file) | <code>&quot;    command = [executed[&#x27;path&#x27;], &#x27;--unshare-net&#x27;, &#x27;--dev&#x27;, &#x27;/dev&#x27;, &#x27;--dev-bind&#x27;, &#x27;/dev/null&#x27;, &#x27;/dev/null&#x27;,&quot;</code> |
| trinity_read.py:890 | BEYOND | ∅ (added file) | <code>&quot;               &#x27;--tmpfs&#x27;, &#x27;/dev/shm&#x27;, &#x27;--proc&#x27;, &#x27;/proc&#x27;, &#x27;--dir&#x27;, &#x27;/trinity-probe&#x27;]&quot;</code> |
| trinity_read.py:891 | BEYOND | ∅ (added file) | <code>&quot;    for name in (&#x27;usr&#x27;, &#x27;bin&#x27;, &#x27;sbin&#x27;, &#x27;lib&#x27;, &#x27;lib64&#x27;, &#x27;etc&#x27;):&quot;</code> |
| trinity_read.py:892 | BEYOND | ∅ (added file) | <code>&quot;        path = Path(&#x27;/&#x27;)/name&quot;</code> |
| trinity_read.py:893 | BEYOND | ∅ (added file) | <code>&quot;        if path.is_symlink(): command += [&#x27;--symlink&#x27;, os.readlink(str(path)), str(path)]&quot;</code> |
| trinity_read.py:894 | BEYOND | ∅ (added file) | <code>&quot;        elif path.exists(): command += [&#x27;--ro-bind&#x27;, str(path), str(path)]&quot;</code> |
| trinity_read.py:895 | BEYOND | ∅ (added file) | <code>&quot;    command += [&#x27;--bind&#x27;, str(root), str(root), &#x27;--chdir&#x27;, str(root), &#x27;--die-with-parent&#x27;, &#x27;/bin/true&#x27;]&quot;</code> |
| trinity_read.py:896 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:897 | BEYOND | ∅ (added file) | <code>&quot;        probe = subprocess.run(command, env=dict(PATH=&#x27;/usr/bin:/bin&#x27;), stdout=subprocess.PIPE,&quot;</code> |
| trinity_read.py:898 | BEYOND | ∅ (added file) | <code>&quot;                               stderr=subprocess.PIPE, universal_newlines=True, timeout=30)&quot;</code> |
| trinity_read.py:899 | PATH/ENV | ∅ (added file) | <code>&quot;        checks[&#x27;cpu_namespace&#x27;] = dict(returncode=probe.returncode, stderr=probe.stderr, command=command, bwrap=executed)&quot;</code> |
| trinity_read.py:900 | BEYOND | ∅ (added file) | <code>&quot;    except (OSError, subprocess.SubprocessError) as error:&quot;</code> |
| trinity_read.py:901 | PATH/ENV | ∅ (added file) | <code>&quot;        checks[&#x27;cpu_namespace&#x27;] = dict(returncode=None, error=str(error), command=command, bwrap=executed)&quot;</code> |
| trinity_read.py:902 | BEYOND | ∅ (added file) | <code>&quot;    audit = config_audit(root)&quot;</code> |
| trinity_read.py:903 | BEYOND | ∅ (added file) | <code>&quot;    passed = (state.get(&#x27;complete&#x27;, False) and not missing and not unverifiable and not checks[&#x27;pieces&#x27;][&#x27;errors&#x27;]&quot;</code> |
| trinity_read.py:904 | BEYOND | ∅ (added file) | <code>&quot;              and not checks.get(&#x27;runner&#x27;, {}).get(&#x27;errors&#x27;) and checks[&#x27;cpu_namespace&#x27;][&#x27;returncode&#x27;] == 0&quot;</code> |
| trinity_read.py:905 | BEYOND | ∅ (added file) | <code>&quot;              and all(c.get(&#x27;passed&#x27;, True) for c in checks.values()) and audit[&#x27;passed&#x27;])&quot;</code> |
| trinity_read.py:906 | BEYOND | ∅ (added file) | <code>&quot;    return dict(passed=bool(passed), stage_complete=state.get(&#x27;complete&#x27;, False), checks=checks,&quot;</code> |
| trinity_read.py:907 | BEYOND | ∅ (added file) | <code>&quot;                unverifiable=unverifiable, missing_pieces=missing, portability=audit, small_file_bytes=SMALL_FILE_BYTES,&quot;</code> |
| trinity_read.py:908 | PATH/ENV | ∅ (added file) | <code>&quot;                bwrap=executed, note=&#x27;Large file sizes are checked, not large-file content hashes. Pinned evidence does not fail the path audit.&#x27;)&quot;</code> |
| trinity_read.py:909 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:910 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:911 | BEYOND | ∅ (added file) | <code>&quot;def stub_usage(path, enabled=True):&quot;</code> |
| trinity_read.py:912 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Count all engine events; unreadable or malformed evidence cannot pass.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:913 | BEYOND | ∅ (added file) | <code>&quot;    result = dict(path=str(path), enabled=enabled, import_events_count=0, call_events_count=0,&quot;</code> |
| trinity_read.py:914 | BEYOND | ∅ (added file) | <code>&quot;                  errors=[], calls=[])&quot;</code> |
| trinity_read.py:915 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:916 | BEYOND | ∅ (added file) | <code>&quot;        for line in Path(path).read_text().splitlines():&quot;</code> |
| trinity_read.py:917 | BEYOND | ∅ (added file) | <code>&quot;            row = json.loads(line)&quot;</code> |
| trinity_read.py:918 | BEYOND | ∅ (added file) | <code>&quot;            if row.get(&#x27;event&#x27;) == &#x27;import&#x27; and isinstance(row.get(&#x27;pid&#x27;), int) and row.get(&#x27;module&#x27;):&quot;</code> |
| trinity_read.py:919 | BEYOND | ∅ (added file) | <code>&quot;                result[&#x27;import_events_count&#x27;] += 1&quot;</code> |
| trinity_read.py:920 | BEYOND | ∅ (added file) | <code>&quot;            elif row.get(&#x27;event&#x27;) == &#x27;call&#x27; and isinstance(row.get(&#x27;name&#x27;), str):&quot;</code> |
| trinity_read.py:921 | BEYOND | ∅ (added file) | <code>&quot;                result[&#x27;call_events_count&#x27;] += 1&quot;</code> |
| trinity_read.py:922 | BEYOND | ∅ (added file) | <code>&quot;                result[&#x27;calls&#x27;].append(row[&#x27;name&#x27;])&quot;</code> |
| trinity_read.py:923 | BEYOND | ∅ (added file) | <code>&quot;            else:&quot;</code> |
| trinity_read.py:924 | BEYOND | ∅ (added file) | <code>&quot;                result[&#x27;errors&#x27;].append(&#x27;Invalid stub event: &#x27;+repr(row))&quot;</code> |
| trinity_read.py:925 | BEYOND | ∅ (added file) | <code>&quot;    except (OSError, ValueError) as error:&quot;</code> |
| trinity_read.py:926 | BEYOND | ∅ (added file) | <code>&quot;        result[&#x27;errors&#x27;].append(str(error))&quot;</code> |
| trinity_read.py:927 | BEYOND | ∅ (added file) | <code>&quot;    if result[&#x27;call_events_count&#x27;]:&quot;</code> |
| trinity_read.py:928 | BEYOND | ∅ (added file) | <code>&quot;        result[&#x27;errors&#x27;].append(&#x27;llguidance stub called {} time(s): {}&#x27;.format(result[&#x27;call_events_count&#x27;], &#x27;, &#x27;.join(result[&#x27;calls&#x27;])))&quot;</code> |
| trinity_read.py:929 | BEYOND | ∅ (added file) | <code>&quot;    if enabled and not result[&#x27;import_events_count&#x27;]:&quot;</code> |
| trinity_read.py:930 | BEYOND | ∅ (added file) | <code>&quot;        result[&#x27;errors&#x27;].append(&#x27;Enabled llguidance stub has no import evidence&#x27;)&quot;</code> |
| trinity_read.py:931 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;passed&#x27;] = not result[&#x27;errors&#x27;]&quot;</code> |
| trinity_read.py:932 | BEYOND | ∅ (added file) | <code>&quot;    return result&quot;</code> |
| trinity_read.py:933 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:934 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:935 | BEYOND | ∅ (added file) | <code>&quot;def capture_command(argv):&quot;</code> |
| trinity_read.py:936 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:937 | BEYOND | ∅ (added file) | <code>&quot;        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,&quot;</code> |
| trinity_read.py:938 | BEYOND | ∅ (added file) | <code>&quot;                           universal_newlines=True, timeout=30)&quot;</code> |
| trinity_read.py:939 | BEYOND | ∅ (added file) | <code>&quot;        return dict(argv=argv, returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)&quot;</code> |
| trinity_read.py:940 | BEYOND | ∅ (added file) | <code>&quot;    except (OSError, subprocess.SubprocessError) as error:&quot;</code> |
| trinity_read.py:941 | BEYOND | ∅ (added file) | <code>&quot;        return dict(argv=argv, returncode=None, error=str(error))&quot;</code> |
| trinity_read.py:942 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:943 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:944 | BEYOND | ∅ (added file) | <code>&quot;def sandbox_receipt(command=None, executed=None, overlay=None, probe_report=None):&quot;</code> |
| trinity_read.py:945 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Record actual namespace argv, with explicit unknowns before execution.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:946 | BEYOND | ∅ (added file) | <code>&quot;    binds = []; special = []&quot;</code> |
| trinity_read.py:947 | BEYOND | ∅ (added file) | <code>&quot;    argv = command or []&quot;</code> |
| trinity_read.py:948 | BEYOND | ∅ (added file) | <code>&quot;    for i, arg in enumerate(argv):&quot;</code> |
| trinity_read.py:949 | BEYOND | ∅ (added file) | <code>&quot;        if arg in (&#x27;--bind&#x27;, &#x27;--ro-bind&#x27;, &#x27;--dev-bind&#x27;):&quot;</code> |
| trinity_read.py:950 | BEYOND | ∅ (added file) | <code>&quot;            binds.append(dict(source=argv[i+1], target=argv[i+2], mode=&#x27;ro&#x27; if arg == &#x27;--ro-bind&#x27; else &#x27;rw&#x27;, option=arg))&quot;</code> |
| trinity_read.py:951 | BEYOND | ∅ (added file) | <code>&quot;        elif arg in (&#x27;--symlink&#x27;,):&quot;</code> |
| trinity_read.py:952 | BEYOND | ∅ (added file) | <code>&quot;            special.append(dict(option=arg, source=argv[i+1], target=argv[i+2]))&quot;</code> |
| trinity_read.py:953 | BEYOND | ∅ (added file) | <code>&quot;        elif arg in (&#x27;--dev&#x27;, &#x27;--proc&#x27;, &#x27;--tmpfs&#x27;):&quot;</code> |
| trinity_read.py:954 | BEYOND | ∅ (added file) | <code>&quot;            special.append(dict(option=arg, target=argv[i+1]))&quot;</code> |
| trinity_read.py:955 | BEYOND | ∅ (added file) | <code>&quot;    glibc = capture_command([&#x27;ldd&#x27;, &#x27;--version&#x27;])&quot;</code> |
| trinity_read.py:956 | BEYOND | ∅ (added file) | <code>&quot;    driver = capture_command([&#x27;nvidia-smi&#x27;, &#x27;--query-gpu=driver_version&#x27;, &#x27;--format=csv,noheader&#x27;])&quot;</code> |
| trinity_read.py:957 | BEYOND | ∅ (added file) | <code>&quot;    libraries = []&quot;</code> |
| trinity_read.py:958 | BEYOND | ∅ (added file) | <code>&quot;    for name in (&#x27;libcuda.so.1&#x27;, &#x27;libnvidia-ml.so.1&#x27;):&quot;</code> |
| trinity_read.py:959 | BEYOND | ∅ (added file) | <code>&quot;        path = Path(&#x27;/usr/lib64&#x27;)/name&quot;</code> |
| trinity_read.py:960 | BEYOND | ∅ (added file) | <code>&quot;        row = dict(name=name, path=str(path), resolved_path=str(path.resolve()), bytes=None)&quot;</code> |
| trinity_read.py:961 | BEYOND | ∅ (added file) | <code>&quot;        try: row[&#x27;bytes&#x27;] = path.stat().st_size&quot;</code> |
| trinity_read.py:962 | BEYOND | ∅ (added file) | <code>&quot;        except OSError as error: row[&#x27;error&#x27;] = str(error)&quot;</code> |
| trinity_read.py:963 | BEYOND | ∅ (added file) | <code>&quot;        libraries.append(row)&quot;</code> |
| trinity_read.py:964 | BEYOND | ∅ (added file) | <code>&quot;    p = probe_report or {}&quot;</code> |
| trinity_read.py:965 | BEYOND | ∅ (added file) | <code>&quot;    return dict(bwrap=executed, namespace_executed=False, namespace_argv=command, binds=binds, special_mounts=special,&quot;</code> |
| trinity_read.py:966 | BEYOND | ∅ (added file) | <code>&quot;                llguidance_stub=overlay, host_glibc=next(iter(glibc.get(&#x27;stdout&#x27;, &#x27;&#x27;).splitlines()), None),&quot;</code> |
| trinity_read.py:967 | BEYOND | ∅ (added file) | <code>&quot;                host_glibc_command=glibc, namespace_glibc=p.get(&#x27;glibc&#x27;),&quot;</code> |
| trinity_read.py:968 | BEYOND | ∅ (added file) | <code>&quot;                host_nvidia_driver=driver, host_driver_libraries=libraries,&quot;</code> |
| trinity_read.py:969 | BEYOND | ∅ (added file) | <code>&quot;                namespace_driver_resolution=p.get(&#x27;imports&#x27;, {}).get(&#x27;driver_resolution&#x27;),&quot;</code> |
| trinity_read.py:970 | BEYOND | ∅ (added file) | <code>&quot;                versions=p.get(&#x27;versions&#x27;, {}), probe_path=p.get(&#x27;evidence_directory&#x27;),&quot;</code> |
| trinity_read.py:971 | BEYOND | ∅ (added file) | <code>&quot;                probe_passed=p.get(&#x27;passed&#x27;), unavailable_reason=p.get(&#x27;error&#x27;))&quot;</code> |
| trinity_read.py:972 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:973 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:974 | BEYOND | ∅ (added file) | <code>&quot;PROBE_MARKER = &#x27;TRINITY_PROBE_JSON=&#x27;&quot;</code> |
| trinity_read.py:975 | BEYOND | ∅ (added file) | <code>&quot;PROBE_CODE = r&#x27;&#x27;&#x27;&quot;</code> |
| trinity_read.py:976 | BEYOND | ∅ (added file) | <code>&quot;import ctypes, json, os, sys, traceback&quot;</code> |
| trinity_read.py:977 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace&quot;</code> |
| trinity_read.py:978 | BEYOND | ∅ (added file) | <code>&quot;result = dict(versions={&#x27;python&#x27;: sys.version}, glibc=os.confstr(&#x27;CS_GNU_LIBC_VERSION&#x27;), imports_passed=False,&quot;</code> |
| trinity_read.py:979 | BEYOND | ∅ (added file) | <code>&quot;              structured_output=dict(passed=False, status=&#x27;not_reached&#x27;))&quot;</code> |
| trinity_read.py:980 | BEYOND | ∅ (added file) | <code>&quot;try:&quot;</code> |
| trinity_read.py:981 | BEYOND | ∅ (added file) | <code>&quot;    import vllm, torch, transformers&quot;</code> |
| trinity_read.py:982 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;versions&#x27;].update(vllm=vllm.__version__, torch=torch.__version__, transformers=transformers.__version__)&quot;</code> |
| trinity_read.py:983 | BEYOND | ∅ (added file) | <code>&quot;    from vllm import LLM&quot;</code> |
| trinity_read.py:984 | BEYOND | ∅ (added file) | <code>&quot;    from vllm.model_executor.models import qwen3_5&quot;</code> |
| trinity_read.py:985 | BEYOND | ∅ (added file) | <code>&quot;    import vllm.v1.engine.core, vllm.v1.worker.gpu_model_runner&quot;</code> |
| trinity_read.py:986 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;imports_passed&#x27;] = True&quot;</code> |
| trinity_read.py:987 | BEYOND | ∅ (added file) | <code>&quot;except Exception as error:&quot;</code> |
| trinity_read.py:988 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;error&#x27;] = type(error).__name__ + &#x27;: &#x27; + str(error)&quot;</code> |
| trinity_read.py:989 | BEYOND | ∅ (added file) | <code>&quot;    traceback.print_exc()&quot;</code> |
| trinity_read.py:990 | BEYOND | ∅ (added file) | <code>&quot;try:&quot;</code> |
| trinity_read.py:991 | BEYOND | ∅ (added file) | <code>&quot;    from vllm.v1.structured_output.backend_guidance import GuidanceBackend, StructuredOutputOptions&quot;</code> |
| trinity_read.py:992 | BEYOND | ∅ (added file) | <code>&quot;    backend = SimpleNamespace(disable_any_whitespace=False, disable_additional_properties=False,&quot;</code> |
| trinity_read.py:993 | BEYOND | ∅ (added file) | <code>&quot;                              ll_tokenizer=None, vocab_size=1)&quot;</code> |
| trinity_read.py:994 | BEYOND | ∅ (added file) | <code>&quot;    # Execute the installed method; no model, tokenizer download, or GPU allocation.&quot;</code> |
| trinity_read.py:995 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;structured_output&#x27;][&#x27;stage&#x27;] = &#x27;GuidanceBackend.compile_grammar(REGEX, \&quot;a\&quot;)&#x27;&quot;</code> |
| trinity_read.py:996 | BEYOND | ∅ (added file) | <code>&quot;    GuidanceBackend.compile_grammar(backend, StructuredOutputOptions.REGEX, &#x27;a&#x27;)&quot;</code> |
| trinity_read.py:997 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;structured_output&#x27;].update(status=&#x27;unexpected_success&#x27;, reason=&#x27;Guidance compilation did not raise&#x27;)&quot;</code> |
| trinity_read.py:998 | BEYOND | ∅ (added file) | <code>&quot;except Exception as error:&quot;</code> |
| trinity_read.py:999 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;structured_output&#x27;].update(status=&#x27;raised&#x27;, exception=type(error).__name__, reason=str(error))&quot;</code> |
| trinity_read.py:1000 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;structured_output&#x27;][&#x27;stub_runtime_error&#x27;] = isinstance(error, RuntimeError) and str(error).startswith(&#x27;llguidance stub:&#x27;)&quot;</code> |
| trinity_read.py:1001 | BEYOND | ∅ (added file) | <code>&quot;result[&#x27;driver_resolution&#x27;] = []&quot;</code> |
| trinity_read.py:1002 | BEYOND | ∅ (added file) | <code>&quot;for name in (&#x27;libcuda.so.1&#x27;, &#x27;libnvidia-ml.so.1&#x27;):&quot;</code> |
| trinity_read.py:1003 | BEYOND | ∅ (added file) | <code>&quot;    row = dict(name=name, paths=[])&quot;</code> |
| trinity_read.py:1004 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:1005 | BEYOND | ∅ (added file) | <code>&quot;        lib = ctypes.CDLL(name)&quot;</code> |
| trinity_read.py:1006 | BEYOND | ∅ (added file) | <code>&quot;        with open(&#x27;/proc/self/maps&#x27;) as f:&quot;</code> |
| trinity_read.py:1007 | BEYOND | ∅ (added file) | <code>&quot;            paths = sorted({line.split()[-1] for line in f if &#x27;/libcuda.so&#x27; in line or &#x27;/libnvidia-ml.so&#x27; in line})&quot;</code> |
| trinity_read.py:1008 | BEYOND | ∅ (added file) | <code>&quot;        row[&#x27;paths&#x27;] = [dict(path=p, bytes=os.stat(p).st_size) for p in paths if os.path.basename(p).startswith(name.split(&#x27;.so&#x27;)[0]+&#x27;.so&#x27;)]&quot;</code> |
| trinity_read.py:1009 | BEYOND | ∅ (added file) | <code>&quot;    except Exception as error:&quot;</code> |
| trinity_read.py:1010 | BEYOND | ∅ (added file) | <code>&quot;        row[&#x27;error&#x27;] = type(error).__name__ + &#x27;: &#x27; + str(error)&quot;</code> |
| trinity_read.py:1011 | BEYOND | ∅ (added file) | <code>&quot;    result[&#x27;driver_resolution&#x27;].append(row)&quot;</code> |
| trinity_read.py:1012 | BEYOND | ∅ (added file) | <code>&quot;result[&#x27;cryptography_imported&#x27;] = any(n == &#x27;cryptography&#x27; or n.startswith(&#x27;cryptography.&#x27;) for n in sys.modules)&quot;</code> |
| trinity_read.py:1013 | BEYOND | ∅ (added file) | <code>&quot;print(&#x27;TRINITY_PROBE_JSON=&#x27; + json.dumps(result, sort_keys=True), flush=True)&quot;</code> |
| trinity_read.py:1014 | BEYOND | ∅ (added file) | <code>&quot;sys.exit(0 if result[&#x27;imports_passed&#x27;] else 1)&quot;</code> |
| trinity_read.py:1015 | BEYOND | ∅ (added file) | <code>&quot;&#x27;&#x27;&#x27;&quot;</code> |
| trinity_read.py:1016 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1017 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1018 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1019 | BEYOND | ∅ (added file) | <code>&quot;def probe(root, shm=None, bwrap=DEFAULT_BWRAP, llguidance_stub=True):&quot;</code> |
| trinity_read.py:1020 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Check vLLM imports with host libraries and an isolated CPU-only /dev.\&quot;\&quot;\&quot;&quot;</code> |
| trinity_read.py:1021 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(root)&quot;</code> |
| trinity_read.py:1022 | BEYOND | ∅ (added file) | <code>&quot;    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(&#x27;%Y%m%dT%H%M%S.%fZ&#x27;)&quot;</code> |
| trinity_read.py:1023 | BEYOND | ∅ (added file) | <code>&quot;    out = root/&#x27;runs&#x27;/(&#x27;probe_&#x27;+stamp); out.mkdir(parents=True)&quot;</code> |
| trinity_read.py:1024 | BEYOND | ∅ (added file) | <code>&quot;    report = dict(passed=False, cpu_only=True, evidence_directory=str(out), returncode=None,&quot;</code> |
| trinity_read.py:1025 | BEYOND | ∅ (added file) | <code>&quot;                  versions={}, glibc=None, cryptography_imported=None)&quot;</code> |
| trinity_read.py:1026 | BEYOND | ∅ (added file) | <code>&quot;    started = time.monotonic()&quot;</code> |
| trinity_read.py:1027 | BEYOND | ∅ (added file) | <code>&quot;    command = None; executed = None; namespace_executed = False&quot;</code> |
| trinity_read.py:1028 | BEYOND | ∅ (added file) | <code>&quot;    log = out/&#x27;llg_stub_calls.jsonl&#x27;; log.touch(exist_ok=False)&quot;</code> |
| trinity_read.py:1029 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:1030 | BEYOND | ∅ (added file) | <code>&quot;        report[&#x27;llguidance_stub&#x27;] = llguidance_evidence(llguidance_stub)&quot;</code> |
| trinity_read.py:1031 | BEYOND | ∅ (added file) | <code>&quot;        state = load(root/&#x27;STAGING.json&#x27;) if (root/&#x27;STAGING.json&#x27;).exists() else {}&quot;</code> |
| trinity_read.py:1032 | BEYOND | ∅ (added file) | <code>&quot;        runtime = state.get(&#x27;pieces&#x27;, {}).get(&#x27;runtime_0&#x27;, {})&quot;</code> |
| trinity_read.py:1033 | BEYOND | ∅ (added file) | <code>&quot;        uv_python = root/&#x27;sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12&#x27;&quot;</code> |
| trinity_read.py:1034 | BEYOND | ∅ (added file) | <code>&quot;        if runtime.get(&#x27;status&#x27;) != &#x27;complete&#x27; or not uv_python.is_file():&quot;</code> |
| trinity_read.py:1035 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;probe requires runtime_0 staged (uv Python); input archives are not consumed or awaited&#x27;)&quot;</code> |
| trinity_read.py:1036 | BEYOND | ∅ (added file) | <code>&quot;        # The venv&#x27;s absolute interpreter link resolves only inside the namespace.&quot;</code> |
| trinity_read.py:1037 | BEYOND | ∅ (added file) | <code>&quot;        python = physical(root, VLLM_ENV/&#x27;bin/python&#x27;)&quot;</code> |
| trinity_read.py:1038 | BEYOND | ∅ (added file) | <code>&quot;        if not os.path.lexists(str(python)):&quot;</code> |
| trinity_read.py:1039 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;probe requires the staged vLLM interpreter: &#x27;+str(python))&quot;</code> |
| trinity_read.py:1040 | BEYOND | ∅ (added file) | <code>&quot;        env = environment(root, shm=shm)&quot;</code> |
| trinity_read.py:1041 | BEYOND | ∅ (added file) | <code>&quot;        env[&#x27;LLG_STUB_LOG&#x27;] = str(log)&quot;</code> |
| trinity_read.py:1042 | BEYOND | ∅ (added file) | <code>&quot;        executed = bwrap_evidence(root, bwrap)&quot;</code> |
| trinity_read.py:1043 | BEYOND | ∅ (added file) | <code>&quot;        report.update(bwrap=executed, env=env, shm=str(shm_directory(root, shm)))&quot;</code> |
| trinity_read.py:1044 | BEYOND | ∅ (added file) | <code>&quot;        # Match vllm_isolated.sh&#x27;s -I without requiring the reader payload to be staged.&quot;</code> |
| trinity_read.py:1045 | BEYOND | ∅ (added file) | <code>&quot;        command = namespace(root, gpu=False, shm=shm, bwrap=executed[&#x27;path&#x27;], llguidance_stub=llguidance_stub)&quot;</code> |
| trinity_read.py:1046 | BEYOND | ∅ (added file) | <code>&quot;        command += [str(VLLM_ENV/&#x27;bin/python&#x27;), &#x27;-I&#x27;, &#x27;-B&#x27;, &#x27;-c&#x27;, PROBE_CODE]&quot;</code> |
| trinity_read.py:1047 | BEYOND | ∅ (added file) | <code>&quot;        report[&#x27;argv&#x27;] = command&quot;</code> |
| trinity_read.py:1048 | BEYOND | ∅ (added file) | <code>&quot;        namespace_executed = True&quot;</code> |
| trinity_read.py:1049 | BEYOND | ∅ (added file) | <code>&quot;        process = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,&quot;</code> |
| trinity_read.py:1050 | BEYOND | ∅ (added file) | <code>&quot;                                 universal_newlines=True, timeout=120)&quot;</code> |
| trinity_read.py:1051 | BEYOND | ∅ (added file) | <code>&quot;        report.update(returncode=process.returncode, stdout=process.stdout, stderr=process.stderr)&quot;</code> |
| trinity_read.py:1052 | BEYOND | ∅ (added file) | <code>&quot;        records = [line[len(PROBE_MARKER):] for line in process.stdout.splitlines() if line.startswith(PROBE_MARKER)]&quot;</code> |
| trinity_read.py:1053 | BEYOND | ∅ (added file) | <code>&quot;        if len(records) == 1:&quot;</code> |
| trinity_read.py:1054 | BEYOND | ∅ (added file) | <code>&quot;            imports = json.loads(records[0])&quot;</code> |
| trinity_read.py:1055 | BEYOND | ∅ (added file) | <code>&quot;            report.update({k:imports[k] for k in (&#x27;versions&#x27;, &#x27;glibc&#x27;, &#x27;cryptography_imported&#x27;)})&quot;</code> |
| trinity_read.py:1056 | BEYOND | ∅ (added file) | <code>&quot;            report[&#x27;imports&#x27;] = imports&quot;</code> |
| trinity_read.py:1057 | BEYOND | ∅ (added file) | <code>&quot;            usage = stub_usage(log, llguidance_stub)&quot;</code> |
| trinity_read.py:1058 | BEYOND | ∅ (added file) | <code>&quot;            structured = imports.get(&#x27;structured_output&#x27;, dict(status=&#x27;not_reported&#x27;))&quot;</code> |
| trinity_read.py:1059 | BEYOND | ∅ (added file) | <code>&quot;            structured[&#x27;call_events_count&#x27;] = usage[&#x27;call_events_count&#x27;]&quot;</code> |
| trinity_read.py:1060 | BEYOND | ∅ (added file) | <code>&quot;            structured[&#x27;calls&#x27;] = usage[&#x27;calls&#x27;]&quot;</code> |
| trinity_read.py:1061 | BEYOND | ∅ (added file) | <code>&quot;            structured[&#x27;passed&#x27;] = bool(structured.get(&#x27;stub_runtime_error&#x27;) and usage[&#x27;call_events_count&#x27;] &gt; 0)&quot;</code> |
| trinity_read.py:1062 | BEYOND | ∅ (added file) | <code>&quot;            report[&#x27;structured_output&#x27;] = structured&quot;</code> |
| trinity_read.py:1063 | BEYOND | ∅ (added file) | <code>&quot;            report[&#x27;stub_usage&#x27;] = usage&quot;</code> |
| trinity_read.py:1064 | BEYOND | ∅ (added file) | <code>&quot;            report[&#x27;passed&#x27;] = (process.returncode == 0 and imports[&#x27;imports_passed&#x27;]&quot;</code> |
| trinity_read.py:1065 | BEYOND | ∅ (added file) | <code>&quot;                                and (not llguidance_stub or structured[&#x27;passed&#x27;]))&quot;</code> |
| trinity_read.py:1066 | BEYOND | ∅ (added file) | <code>&quot;        if not report[&#x27;passed&#x27;]:&quot;</code> |
| trinity_read.py:1067 | BEYOND | ∅ (added file) | <code>&quot;            raise RuntimeError(&#x27;CPU import probe failed; inspect &#x27;+str(out/&#x27;PROBE.json&#x27;))&quot;</code> |
| trinity_read.py:1068 | BEYOND | ∅ (added file) | <code>&quot;    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:&quot;</code> |
| trinity_read.py:1069 | BEYOND | ∅ (added file) | <code>&quot;        report[&#x27;error&#x27;] = str(error)&quot;</code> |
| trinity_read.py:1070 | BEYOND | ∅ (added file) | <code>&quot;        error.probe_report = report&quot;</code> |
| trinity_read.py:1071 | BEYOND | ∅ (added file) | <code>&quot;        raise&quot;</code> |
| trinity_read.py:1072 | BEYOND | ∅ (added file) | <code>&quot;    finally:&quot;</code> |
| trinity_read.py:1073 | BEYOND | ∅ (added file) | <code>&quot;        report[&#x27;wall_seconds&#x27;] = time.monotonic()-started&quot;</code> |
| trinity_read.py:1074 | BEYOND | ∅ (added file) | <code>&quot;        report.setdefault(&#x27;structured_output&#x27;, dict(passed=False, status=&#x27;not_executed&#x27;, reason=report.get(&#x27;error&#x27;)))&quot;</code> |
| trinity_read.py:1075 | BEYOND | ∅ (added file) | <code>&quot;        report.setdefault(&#x27;stub_usage&#x27;, stub_usage(log, llguidance_stub))&quot;</code> |
| trinity_read.py:1076 | BEYOND | ∅ (added file) | <code>&quot;        receipt = sandbox_receipt(command, executed, report.get(&#x27;llguidance_stub&#x27;), report)&quot;</code> |
| trinity_read.py:1077 | BEYOND | ∅ (added file) | <code>&quot;        receipt[&#x27;namespace_executed&#x27;] = namespace_executed&quot;</code> |
| trinity_read.py:1078 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;SANDBOX.json&#x27;, receipt)&quot;</code> |
| trinity_read.py:1079 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;PROBE.json&#x27;, report)&quot;</code> |
| trinity_read.py:1080 | BEYOND | ∅ (added file) | <code>&quot;    return report&quot;</code> |
| trinity_read.py:1081 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1082 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1083 | BEYOND | ∅ (added file) | <code>&quot;def launch(args):&quot;</code> |
| trinity_read.py:1084 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(args.root)&quot;</code> |
| trinity_read.py:1085 | BEYOND | ∅ (added file) | <code>&quot;    if not re.fullmatch(&#x27;[a-z][0-9a-f]{8,32}&#x27;, args.token):&quot;</code> |
| trinity_read.py:1086 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Token must be a letter followed by 8\u201332 lowercase hex digits&#x27;)&quot;</code> |
| trinity_read.py:1087 | BEYOND | ∅ (added file) | <code>&quot;    repeat = getattr(args, &#x27;repeat&#x27;, 1)&quot;</code> |
| trinity_read.py:1088 | BEYOND | ∅ (added file) | <code>&quot;    if repeat not in (1, 2) or (args.command != &#x27;proof&#x27; and repeat != 1):&quot;</code> |
| trinity_read.py:1089 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;proof --repeat must be 1 or 2&#x27;)&quot;</code> |
| trinity_read.py:1090 | BEYOND | ∅ (added file) | <code>&quot;    parent = root/&#x27;runs&#x27;/args.token if args.command == &#x27;proof&#x27; else writable(args.out)&quot;</code> |
| trinity_read.py:1091 | BEYOND | ∅ (added file) | <code>&quot;    if not inside(parent, root): raise ValueError(&#x27;Runtime output must be under --root&#x27;)&quot;</code> |
| trinity_read.py:1092 | BEYOND | ∅ (added file) | <code>&quot;    if parent.exists(): raise ValueError(&#x27;Run output exists; no automatic retry&#x27;)&quot;</code> |
| trinity_read.py:1093 | BEYOND | ∅ (added file) | <code>&quot;    outputs = []&quot;</code> |
| trinity_read.py:1094 | BEYOND | ∅ (added file) | <code>&quot;    if repeat == 2:&quot;</code> |
| trinity_read.py:1095 | BEYOND | ∅ (added file) | <code>&quot;        for i in (1, 2):&quot;</code> |
| trinity_read.py:1096 | BEYOND | ∅ (added file) | <code>&quot;            if (root/&#x27;runs&#x27;/(args.token+&#x27;_r&#x27;+str(i))).exists():&quot;</code> |
| trinity_read.py:1097 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Repeated run output exists; no automatic retry&#x27;)&quot;</code> |
| trinity_read.py:1098 | BEYOND | ∅ (added file) | <code>&quot;        tokens = root/&#x27;tokens&#x27;; tokens.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:1099 | BEYOND | ∅ (added file) | <code>&quot;        with (tokens/args.token).open(&#x27;x&#x27;) as f: f.write(str(parent)+&#x27;\\n&#x27;)&quot;</code> |
| trinity_read.py:1100 | BEYOND | ∅ (added file) | <code>&quot;        parent.mkdir(parents=True)&quot;</code> |
| trinity_read.py:1101 | BEYOND | ∅ (added file) | <code>&quot;    failure = None&quot;</code> |
| trinity_read.py:1102 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:1103 | BEYOND | ∅ (added file) | <code>&quot;        for i in range(1, repeat+1):&quot;</code> |
| trinity_read.py:1104 | BEYOND | ∅ (added file) | <code>&quot;            child = argparse.Namespace(**vars(args))&quot;</code> |
| trinity_read.py:1105 | BEYOND | ∅ (added file) | <code>&quot;            child.run_name = args.token if repeat == 1 else args.token+&#x27;_r&#x27;+str(i)&quot;</code> |
| trinity_read.py:1106 | BEYOND | ∅ (added file) | <code>&quot;            out = root/&#x27;runs&#x27;/child.run_name if args.command == &#x27;proof&#x27; else parent&quot;</code> |
| trinity_read.py:1107 | BEYOND | ∅ (added file) | <code>&quot;            try:&quot;</code> |
| trinity_read.py:1108 | BEYOND | ∅ (added file) | <code>&quot;                _launch_one(child)&quot;</code> |
| trinity_read.py:1109 | BEYOND | ∅ (added file) | <code>&quot;                outputs.append(out)&quot;</code> |
| trinity_read.py:1110 | BEYOND | ∅ (added file) | <code>&quot;            finally:&quot;</code> |
| trinity_read.py:1111 | BEYOND | ∅ (added file) | <code>&quot;                # Preflight refusals still leave a receipt, with no fabricated execution.&quot;</code> |
| trinity_read.py:1112 | BEYOND | ∅ (added file) | <code>&quot;                if not (out/&#x27;SANDBOX.json&#x27;).exists():&quot;</code> |
| trinity_read.py:1113 | BEYOND | ∅ (added file) | <code>&quot;                    out.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:1114 | BEYOND | ∅ (added file) | <code>&quot;                    overlay = llguidance_evidence(False)&quot;</code> |
| trinity_read.py:1115 | BEYOND | ∅ (added file) | <code>&quot;                    overlay[&#x27;enabled&#x27;] = getattr(args, &#x27;llguidance_stub&#x27;, True)&quot;</code> |
| trinity_read.py:1116 | BEYOND | ∅ (added file) | <code>&quot;                    receipt = sandbox_receipt(overlay=overlay)&quot;</code> |
| trinity_read.py:1117 | BEYOND | ∅ (added file) | <code>&quot;                    receipt[&#x27;unavailable_reason&#x27;] = &#x27;Reader namespace not executed; preflight refused&#x27;&quot;</code> |
| trinity_read.py:1118 | BEYOND | ∅ (added file) | <code>&quot;                    dump(out/&#x27;SANDBOX.json&#x27;, receipt)&quot;</code> |
| trinity_read.py:1119 | BEYOND | ∅ (added file) | <code>&quot;    except Exception as error:&quot;</code> |
| trinity_read.py:1120 | BEYOND | ∅ (added file) | <code>&quot;        failure = error&quot;</code> |
| trinity_read.py:1121 | BEYOND | ∅ (added file) | <code>&quot;        raise&quot;</code> |
| trinity_read.py:1122 | BEYOND | ∅ (added file) | <code>&quot;    finally:&quot;</code> |
| trinity_read.py:1123 | BEYOND | ∅ (added file) | <code>&quot;        if repeat == 2:&quot;</code> |
| trinity_read.py:1124 | BEYOND | ∅ (added file) | <code>&quot;            import compare_tokens&quot;</code> |
| trinity_read.py:1125 | BEYOND | ∅ (added file) | <code>&quot;            comparison = compare_tokens.write_repeated(root, args.token, parent, str(failure) if failure else None)&quot;</code> |
| trinity_read.py:1126 | BEYOND | ∅ (added file) | <code>&quot;            dump(parent/&#x27;SANDBOX.json&#x27;, dict(runs=[dict(path=str(root/&#x27;runs&#x27;/(args.token+&#x27;_r&#x27;+str(i))/&#x27;SANDBOX.json&#x27;),&quot;</code> |
| trinity_read.py:1127 | BEYOND | ∅ (added file) | <code>&quot;                receipt=load(root/&#x27;runs&#x27;/(args.token+&#x27;_r&#x27;+str(i))/&#x27;SANDBOX.json&#x27;)&quot;</code> |
| trinity_read.py:1128 | BEYOND | ∅ (added file) | <code>&quot;                if (root/&#x27;runs&#x27;/(args.token+&#x27;_r&#x27;+str(i))/&#x27;SANDBOX.json&#x27;).exists() else None) for i in (1, 2)]))&quot;</code> |
| trinity_read.py:1129 | BEYOND | ∅ (added file) | <code>&quot;    if args.command == &#x27;proof&#x27;:&quot;</code> |
| trinity_read.py:1130 | BEYOND | ∅ (added file) | <code>&quot;        passed = comparison[&#x27;passed&#x27;] if repeat == 2 else load(outputs[0]/&#x27;PROOF.json&#x27;)[&#x27;passed&#x27;]&quot;</code> |
| trinity_read.py:1131 | BEYOND | ∅ (added file) | <code>&quot;        if not passed: raise RuntimeError(&#x27;Token proof differs; inspect &#x27;+str(parent/&#x27;PROOF.json&#x27;))&quot;</code> |
| trinity_read.py:1132 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1133 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1134 | BEYOND | ∅ (added file) | <code>&quot;def _launch_one(args):&quot;</code> |
| trinity_read.py:1135 | BEYOND | ∅ (added file) | <code>&quot;    root = writable(args.root); config = require_stage(root)&quot;</code> |
| trinity_read.py:1136 | BEYOND | ∅ (added file) | <code>&quot;    pattern = yield_pattern(getattr(args, &#x27;yield_glob&#x27;, None))&quot;</code> |
| trinity_read.py:1137 | PATH/ENV | ∅ (added file) | <code>&quot;    shm = shm_directory(root, getattr(args, &#x27;shm&#x27;, None))&quot;</code> |
| trinity_read.py:1138 | PATH/ENV | ∅ (added file) | <code>&quot;    bwrap = getattr(args, &#x27;bwrap&#x27;, DEFAULT_BWRAP)&quot;</code> |
| trinity_read.py:1139 | BEYOND | ∅ (added file) | <code>&quot;    llguidance_stub = getattr(args, &#x27;llguidance_stub&#x27;, True)&quot;</code> |
| trinity_read.py:1140 | BEYOND | ∅ (added file) | <code>&quot;    overlay = llguidance_evidence(llguidance_stub)&quot;</code> |
| trinity_read.py:1141 | BEYOND | ∅ (added file) | <code>&quot;    if not re.fullmatch(&#x27;[a-z][0-9a-f]{8,32}&#x27;, args.token): raise ValueError(&#x27;Token must be a letter followed by 8\u201332 lowercase hex digits&#x27;)&quot;</code> |
| trinity_read.py:1142 | BEYOND | ∅ (added file) | <code>&quot;    # Preflight selection and missing frames before checking or using any GPU.&quot;</code> |
| trinity_read.py:1143 | BEYOND | ∅ (added file) | <code>&quot;    result = cpu_need(root, &#x27;main&#x27; if args.command == &#x27;proof&#x27; else args.family,&quot;</code> |
| trinity_read.py:1144 | BEYOND | ∅ (added file) | <code>&quot;                      read_ids(args.ids) if args.command == &#x27;read&#x27; and args.ids else None,&quot;</code> |
| trinity_read.py:1145 | BEYOND | ∅ (added file) | <code>&quot;                      20 if args.command == &#x27;proof&#x27; else args.first, shm, bwrap, llguidance_stub)&quot;</code> |
| trinity_read.py:1146 | BEYOND | ∅ (added file) | <code>&quot;    missing = sorted(set(result[&#x27;need&#x27;])-set(store_index(root)))&quot;</code> |
| trinity_read.py:1147 | BEYOND | ∅ (added file) | <code>&quot;    if missing:&quot;</code> |
| trinity_read.py:1148 | BEYOND | ∅ (added file) | <code>&quot;        print(&#x27;NEED\\n&#x27;+&#x27;\\n&#x27;.join(missing))&quot;</code> |
| trinity_read.py:1149 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Missing frames; no GPU launched&#x27;)&quot;</code> |
| trinity_read.py:1150 | BEYOND | ∅ (added file) | <code>&quot;    if args.command == &#x27;proof&#x27;:&quot;</code> |
| trinity_read.py:1151 | BEYOND | ∅ (added file) | <code>&quot;        accepted = load(package(root, config)/&#x27;parity/DEV20.json&#x27;)&quot;</code> |
| trinity_read.py:1152 | BEYOND | ∅ (added file) | <code>&quot;        if result[&#x27;ids&#x27;] != accepted[&#x27;ids&#x27;] or set(result[&#x27;need&#x27;]) != set(accepted[&#x27;need&#x27;]):&quot;</code> |
| trinity_read.py:1153 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Proof selection differs from accepted DEV20&#x27;)&quot;</code> |
| trinity_read.py:1154 | BEYOND | ∅ (added file) | <code>&quot;        out = root/&#x27;runs&#x27;/getattr(args, &#x27;run_name&#x27;, args.token)&quot;</code> |
| trinity_read.py:1155 | BEYOND | ∅ (added file) | <code>&quot;    else:&quot;</code> |
| trinity_read.py:1156 | BEYOND | ∅ (added file) | <code>&quot;        out = writable(args.out)&quot;</code> |
| trinity_read.py:1157 | BEYOND | ∅ (added file) | <code>&quot;        config[&#x27;spec&#x27;][&#x27;artifact&#x27;] = dict(kind=&#x27;c1_export&#x27;, path=logical_artifact(root, args.artifact, args.step), sha256=args.sha256)&quot;</code> |
| trinity_read.py:1158 | BEYOND | ∅ (added file) | <code>&quot;        if not re.fullmatch(&#x27;[0-9a-f]{64}&#x27;, args.sha256): raise ValueError(&#x27;Require full export SHA256&#x27;)&quot;</code> |
| trinity_read.py:1159 | BEYOND | ∅ (added file) | <code>&quot;        config[&#x27;spec&#x27;][&#x27;models&#x27;][&#x27;cp1m200&#x27;] = config[&#x27;spec&#x27;][&#x27;artifact&#x27;].copy()&quot;</code> |
| trinity_read.py:1160 | BEYOND | ∅ (added file) | <code>&quot;        config[&#x27;spec&#x27;][&#x27;step&#x27;] = args.step&quot;</code> |
| trinity_read.py:1161 | BEYOND | ∅ (added file) | <code>&quot;    reserve = read_space(root, config, result)&quot;</code> |
| trinity_read.py:1162 | BEYOND | ∅ (added file) | <code>&quot;    out = writable(out)&quot;</code> |
| trinity_read.py:1163 | BEYOND | ∅ (added file) | <code>&quot;    if not inside(out, root): raise ValueError(&#x27;Runtime output must be under --root&#x27;)&quot;</code> |
| trinity_read.py:1164 | BEYOND | ∅ (added file) | <code>&quot;    if out.exists(): raise ValueError(&#x27;Run output exists; no automatic retry&#x27;)&quot;</code> |
| trinity_read.py:1165 | BEYOND | ∅ (added file) | <code>&quot;    tokens = root/&#x27;tokens&#x27;; tokens.mkdir(exist_ok=True)&quot;</code> |
| trinity_read.py:1166 | BEYOND | ∅ (added file) | <code>&quot;    with (tokens/getattr(args, &#x27;run_name&#x27;, args.token)).open(&#x27;x&#x27;) as f: f.write(str(out)+&#x27;\\n&#x27;)&quot;</code> |
| trinity_read.py:1167 | BEYOND | ∅ (added file) | <code>&quot;    out.mkdir(parents=True)&quot;</code> |
| trinity_read.py:1168 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;SPACE.json&#x27;, dict(reserved_estimate_bytes=reserve, free_bytes=shutil.disk_usage(root).free,&quot;</code> |
| trinity_read.py:1169 | BEYOND | ∅ (added file) | <code>&quot;                              minimum_remaining_bytes=kit_stage().MIN_FREE))&quot;</code> |
| trinity_read.py:1170 | BEYOND | ∅ (added file) | <code>&quot;    config[&#x27;token&#x27;] = args.token; config[&#x27;spec&#x27;][&#x27;run&#x27;] = str(out); config[&#x27;output&#x27;] = str(out)&quot;</code> |
| trinity_read.py:1171 | BEYOND | ∅ (added file) | <code>&quot;    config[&#x27;spec&#x27;][&#x27;llguidance_stub&#x27;] = overlay&quot;</code> |
| trinity_read.py:1172 | BEYOND | ∅ (added file) | <code>&quot;    config[&#x27;plan_sha256&#x27;] = hashlib.sha256(json.dumps(config[&#x27;spec&#x27;], sort_keys=True).encode()).hexdigest()&quot;</code> |
| trinity_read.py:1173 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;CONFIG.json&#x27;, config)&quot;</code> |
| trinity_read.py:1174 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;SPEC.json&#x27;, config[&#x27;spec&#x27;])&quot;</code> |
| trinity_read.py:1175 | BEYOND | ∅ (added file) | <code>&quot;    if args.command == &#x27;proof&#x27;:&quot;</code> |
| trinity_read.py:1176 | BEYOND | ∅ (added file) | <code>&quot;        script = Path(config[&#x27;spec&#x27;][&#x27;package&#x27;])/&#x27;proof/phase_b.py&#x27;; extra = []&quot;</code> |
| trinity_read.py:1177 | BEYOND | ∅ (added file) | <code>&quot;    else:&quot;</code> |
| trinity_read.py:1178 | BEYOND | ∅ (added file) | <code>&quot;        request = dict(action=&#x27;read&#x27;, family=args.family, ids=result[&#x27;ids&#x27;], first=None,&quot;</code> |
| trinity_read.py:1179 | BEYOND | ∅ (added file) | <code>&quot;                       work=str(out), config=str(out/&#x27;CONFIG.json&#x27;), attempt=args.token)&quot;</code> |
| trinity_read.py:1180 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;INPUT.json&#x27;, request)&quot;</code> |
| trinity_read.py:1181 | BEYOND | ∅ (added file) | <code>&quot;        script = &#x27;/trinity-build/namespace_worker.py&#x27;; extra = [&#x27;--input&#x27;, str(out/&#x27;INPUT.json&#x27;)]&quot;</code> |
| trinity_read.py:1182 | PATH/ENV | ∅ (added file) | <code>&quot;    env = environment(root, str(args.gpu), args.token, shm)&quot;</code> |
| trinity_read.py:1183 | BEYOND | ∅ (added file) | <code>&quot;    log_path = out/&#x27;llg_stub_calls.jsonl&#x27;; log_path.touch(exist_ok=False)&quot;</code> |
| trinity_read.py:1184 | BEYOND | ∅ (added file) | <code>&quot;    env[&#x27;LLG_STUB_LOG&#x27;] = str(log_path)&quot;</code> |
| trinity_read.py:1185 | BEYOND | ∅ (added file) | <code>&quot;    executed = bwrap_evidence(root, bwrap)&quot;</code> |
| trinity_read.py:1186 | BEYOND | ∅ (added file) | <code>&quot;    command = ns_command(root, out/&#x27;CONFIG.json&#x27;, script, extra, gpu=True, shm=shm, bwrap=executed[&#x27;path&#x27;], llguidance_stub=llguidance_stub)&quot;</code> |
| trinity_read.py:1187 | BEYOND | ∅ (added file) | <code>&quot;    probe_report = None&quot;</code> |
| trinity_read.py:1188 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:1189 | BEYOND | ∅ (added file) | <code>&quot;        probe_report = probe(root, shm, bwrap, llguidance_stub)&quot;</code> |
| trinity_read.py:1190 | BEYOND | ∅ (added file) | <code>&quot;    except Exception as error:&quot;</code> |
| trinity_read.py:1191 | BEYOND | ∅ (added file) | <code>&quot;        probe_report = getattr(error, &#x27;probe_report&#x27;, dict(passed=False, error=str(error)))&quot;</code> |
| trinity_read.py:1192 | BEYOND | ∅ (added file) | <code>&quot;        raise&quot;</code> |
| trinity_read.py:1193 | BEYOND | ∅ (added file) | <code>&quot;    finally:&quot;</code> |
| trinity_read.py:1194 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;PROBE.json&#x27;, probe_report)&quot;</code> |
| trinity_read.py:1195 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;SANDBOX.json&#x27;, sandbox_receipt(command, executed, overlay, probe_report))&quot;</code> |
| trinity_read.py:1196 | BEYOND | ∅ (added file) | <code>&quot;    card = check_card(str(args.gpu)); dump(out/&#x27;CARD.json&#x27;, card)&quot;</code> |
| trinity_read.py:1197 | BEYOND | ∅ (added file) | <code>&quot;    # vnice expands ${*} through bash: pass one shell-quoted command string.&quot;</code> |
| trinity_read.py:1198 | BEYOND | ∅ (added file) | <code>&quot;    command = [VNICE, &#x27; &#x27;.join(shlex.quote(s) for s in command)]&quot;</code> |
| trinity_read.py:1199 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;COMMAND.json&#x27;, dict(argv=command, bwrap=executed, llguidance_stub=overlay))&quot;</code> |
| trinity_read.py:1200 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;ENV.json&#x27;, env)&quot;</code> |
| trinity_read.py:1201 | BEYOND | ∅ (added file) | <code>&quot;    before = host_shm_ours()&quot;</code> |
| trinity_read.py:1202 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;HOST_SHM_BEFORE.json&#x27;, dict(host_dev_shm_ours=before, time=time.time()))&quot;</code> |
| trinity_read.py:1203 | BEYOND | ∅ (added file) | <code>&quot;    sampler = Sampler(str(args.gpu), out/&#x27;MEMORY.jsonl&#x27;); sampler.thread.start()&quot;</code> |
| trinity_read.py:1204 | BEYOND | ∅ (added file) | <code>&quot;    started = time.monotonic(); code = None; yielded = None&quot;</code> |
| trinity_read.py:1205 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| trinity_read.py:1206 | BEYOND | ∅ (added file) | <code>&quot;        with (out/&#x27;run.log&#x27;).open(&#x27;xb&#x27;) as log:&quot;</code> |
| trinity_read.py:1207 | BEYOND | ∅ (added file) | <code>&quot;            receipt = load(out/&#x27;SANDBOX.json&#x27;); receipt[&#x27;namespace_executed&#x27;] = True&quot;</code> |
| trinity_read.py:1208 | BEYOND | ∅ (added file) | <code>&quot;            dump(out/&#x27;SANDBOX.json&#x27;, receipt)&quot;</code> |
| trinity_read.py:1209 | BEYOND | ∅ (added file) | <code>&quot;            code, yielded = run_reader(command, env, root, log, pattern)&quot;</code> |
| trinity_read.py:1210 | BEYOND | ∅ (added file) | <code>&quot;    finally:&quot;</code> |
| trinity_read.py:1211 | BEYOND | ∅ (added file) | <code>&quot;        sampler.stop.set(); sampler.thread.join(timeout=35)&quot;</code> |
| trinity_read.py:1212 | BEYOND | ∅ (added file) | <code>&quot;        usage = stub_usage(log_path, llguidance_stub)&quot;</code> |
| trinity_read.py:1213 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;LLGUIDANCE.json&#x27;, dict(llguidance_stub=overlay, usage=usage))&quot;</code> |
| trinity_read.py:1214 | BEYOND | ∅ (added file) | <code>&quot;        # Phase B&#x27;s packet is nested; read packets use the run directory itself.&quot;</code> |
| trinity_read.py:1215 | BEYOND | ∅ (added file) | <code>&quot;        packet = out/&#x27;b0/d0&#x27; if args.command == &#x27;proof&#x27; else out&quot;</code> |
| trinity_read.py:1216 | BEYOND | ∅ (added file) | <code>&quot;        packet.mkdir(parents=True, exist_ok=True)&quot;</code> |
| trinity_read.py:1217 | BEYOND | ∅ (added file) | <code>&quot;        for name in (&#x27;SANDBOX.json&#x27;, &#x27;LLGUIDANCE.json&#x27;):&quot;</code> |
| trinity_read.py:1218 | BEYOND | ∅ (added file) | <code>&quot;            if packet != out: dump(packet/name, load(out/name))&quot;</code> |
| trinity_read.py:1219 | BEYOND | ∅ (added file) | <code>&quot;        dump(out/&#x27;EXIT.json&#x27;, dict(returncode=code, wall_seconds=time.monotonic()-started, sampler_errors=sampler.errors, bwrap=executed, llguidance_stub=overlay, stub_usage=usage,&quot;</code> |
| trinity_read.py:1220 | BEYOND | ∅ (added file) | <code>&quot;                                  host_dev_shm_ours_before=before, host_dev_shm_ours=host_shm_ours(), yielded=bool(yielded)))&quot;</code> |
| trinity_read.py:1221 | BEYOND | ∅ (added file) | <code>&quot;        try:&quot;</code> |
| trinity_read.py:1222 | BEYOND | ∅ (added file) | <code>&quot;            if args.command == &#x27;proof&#x27;:&quot;</code> |
| trinity_read.py:1223 | BEYOND | ∅ (added file) | <code>&quot;                sys.path.insert(0, str(BUILD))&quot;</code> |
| trinity_read.py:1224 | BEYOND | ∅ (added file) | <code>&quot;                import compare_tokens&quot;</code> |
| trinity_read.py:1225 | BEYOND | ∅ (added file) | <code>&quot;                report = compare_tokens.write_report(package(root, config)/&#x27;parity/DEV20.json&#x27;, out/&#x27;b0/d0&#x27;, &#x27;b0&#x27;, out,&quot;</code> |
| trinity_read.py:1226 | BEYOND | ∅ (added file) | <code>&quot;                                                      out/&#x27;MEMORY.jsonl&#x27;, out/&#x27;EXIT.json&#x27;)&quot;</code> |
| trinity_read.py:1227 | BEYOND | ∅ (added file) | <code>&quot;            else:&quot;</code> |
| trinity_read.py:1228 | BEYOND | ∅ (added file) | <code>&quot;                report = None&quot;</code> |
| trinity_read.py:1229 | BEYOND | ∅ (added file) | <code>&quot;        finally:&quot;</code> |
| trinity_read.py:1230 | BEYOND | ∅ (added file) | <code>&quot;            if yielded:&quot;</code> |
| trinity_read.py:1231 | BEYOND | ∅ (added file) | <code>&quot;                models = out/&#x27;b0/d0/models&#x27; if args.command == &#x27;proof&#x27; else out/&#x27;direct&#x27;/args.family/&#x27;models&#x27;&quot;</code> |
| trinity_read.py:1232 | BEYOND | ∅ (added file) | <code>&quot;                yielded.update(run_directory=str(out), files=disk_listing(out), model_directory=str(models),&quot;</code> |
| trinity_read.py:1233 | BEYOND | ∅ (added file) | <code>&quot;                               model_copies=disk_listing(models), inventory_note=&#x27;Metadata snapshot before YIELD.json; no cleanup.&#x27;)&quot;</code> |
| trinity_read.py:1234 | BEYOND | ∅ (added file) | <code>&quot;                dump(out/&#x27;YIELD.json&#x27;, yielded)&quot;</code> |
| trinity_read.py:1235 | BEYOND | ∅ (added file) | <code>&quot;    if code or sampler.errors: raise RuntimeError(&#x27;Run or memory sampler failed; inspect &#x27;+str(out)+&#x27;; do not retry automatically&#x27;)&quot;</code> |
| trinity_read.py:1236 | BEYOND | ∅ (added file) | <code>&quot;    if not usage[&#x27;passed&#x27;]: raise RuntimeError(&#x27;llguidance audit failed: &#x27;+&#x27;; &#x27;.join(usage[&#x27;errors&#x27;]))&quot;</code> |
| trinity_read.py:1237 | BEYOND | ∅ (added file) | <code>&quot;    print(json.dumps(dict(output=str(out), returncode=code)))&quot;</code> |
| trinity_read.py:1238 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1239 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1240 | BEYOND | ∅ (added file) | <code>&quot;def main():&quot;</code> |
| trinity_read.py:1241 | BEYOND | ∅ (added file) | <code>&quot;    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest=&#x27;command&#x27;); sub.required = True&quot;</code> |
| trinity_read.py:1242 | BEYOND | ∅ (added file) | <code>&quot;    for name in (&#x27;stage&#x27;, &#x27;frames&#x27;, &#x27;need&#x27;, &#x27;proof&#x27;, &#x27;read&#x27;, &#x27;selfcheck&#x27;, &#x27;probe&#x27;):&quot;</code> |
| trinity_read.py:1243 | BEYOND | ∅ (added file) | <code>&quot;        q = sub.add_parser(name); q.add_argument(&#x27;--root&#x27;, default=str(DEFAULT_ROOT))&quot;</code> |
| trinity_read.py:1244 | BEYOND | ∅ (added file) | <code>&quot;        if name in (&#x27;proof&#x27;, &#x27;read&#x27;, &#x27;need&#x27;, &#x27;selfcheck&#x27;, &#x27;probe&#x27;):&quot;</code> |
| trinity_read.py:1245 | PATH/ENV | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--bwrap&#x27;, default=DEFAULT_BWRAP, help=&#x27;Host bubblewrap executable (default: /usr/bin/bwrap); never the pinned Orchard binary&#x27;)&quot;</code> |
| trinity_read.py:1246 | BEYOND | ∅ (added file) | <code>&quot;        if name in (&#x27;proof&#x27;, &#x27;read&#x27;, &#x27;need&#x27;, &#x27;probe&#x27;):&quot;</code> |
| trinity_read.py:1247 | BEYOND | ∅ (added file) | <code>&quot;            overlay = q.add_mutually_exclusive_group()&quot;</code> |
| trinity_read.py:1248 | BEYOND | ∅ (added file) | <code>&quot;            overlay.add_argument(&#x27;--llguidance-stub&#x27;, dest=&#x27;llguidance_stub&#x27;, action=&#x27;store_true&#x27;, default=True,&quot;</code> |
| trinity_read.py:1249 | BEYOND | ∅ (added file) | <code>&quot;                                 help=&#x27;Bind the pinned import-only llguidance stub (default: on)&#x27;)&quot;</code> |
| trinity_read.py:1250 | BEYOND | ∅ (added file) | <code>&quot;            overlay.add_argument(&#x27;--no-llguidance-stub&#x27;, dest=&#x27;llguidance_stub&#x27;, action=&#x27;store_false&#x27;)&quot;</code> |
| trinity_read.py:1251 | BEYOND | ∅ (added file) | <code>&quot;        if name == &#x27;proof&#x27;: q.add_argument(&#x27;--repeat&#x27;, type=int, choices=(1, 2), default=1)&quot;</code> |
| trinity_read.py:1252 | BEYOND | ∅ (added file) | <code>&quot;        if name == &#x27;stage&#x27;: q.add_argument(&#x27;--dl&#x27;, default=str(AREA/&#x27;dl&#x27;))&quot;</code> |
| trinity_read.py:1253 | BEYOND | ∅ (added file) | <code>&quot;        if name == &#x27;frames&#x27;: q.add_argument(&#x27;--tar&#x27;, action=&#x27;append&#x27;, required=True)&quot;</code> |
| trinity_read.py:1254 | BEYOND | ∅ (added file) | <code>&quot;        if name in (&#x27;need&#x27;, &#x27;read&#x27;):&quot;</code> |
| trinity_read.py:1255 | BEYOND | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--family&#x27;, choices=FAMILIES, required=name == &#x27;read&#x27;)&quot;</code> |
| trinity_read.py:1256 | BEYOND | ∅ (added file) | <code>&quot;            selection = q.add_mutually_exclusive_group(required=True)&quot;</code> |
| trinity_read.py:1257 | BEYOND | ∅ (added file) | <code>&quot;            selection.add_argument(&#x27;--ids&#x27;); selection.add_argument(&#x27;--first&#x27;, type=int)&quot;</code> |
| trinity_read.py:1258 | BEYOND | ∅ (added file) | <code>&quot;            if name == &#x27;need&#x27;: selection.add_argument(&#x27;--all&#x27;, action=&#x27;store_true&#x27;)&quot;</code> |
| trinity_read.py:1259 | BEYOND | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--out&#x27;, required=True)&quot;</code> |
| trinity_read.py:1260 | BEYOND | ∅ (added file) | <code>&quot;        if name in (&#x27;proof&#x27;, &#x27;read&#x27;):&quot;</code> |
| trinity_read.py:1261 | BEYOND | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--gpu&#x27;, required=True); q.add_argument(&#x27;--token&#x27;, required=True)&quot;</code> |
| trinity_read.py:1262 | BEYOND | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--yield-glob&#x27;, help=&#x27;Local nonrecursive file glob; poll every 30 seconds&#x27;)&quot;</code> |
| trinity_read.py:1263 | BEYOND | ∅ (added file) | <code>&quot;        if name in (&#x27;proof&#x27;, &#x27;read&#x27;, &#x27;probe&#x27;):&quot;</code> |
| trinity_read.py:1264 | PATH/ENV | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--shm&#x27;, help=&#x27;Private /dev/shm backing directory (default: ROOT/shm)&#x27;)&quot;</code> |
| trinity_read.py:1265 | BEYOND | ∅ (added file) | <code>&quot;        if name == &#x27;read&#x27;:&quot;</code> |
| trinity_read.py:1266 | BEYOND | ∅ (added file) | <code>&quot;            q.add_argument(&#x27;--artifact&#x27;, required=True); q.add_argument(&#x27;--sha256&#x27;, required=True); q.add_argument(&#x27;--step&#x27;, type=int, required=True)&quot;</code> |
| trinity_read.py:1267 | BEYOND | ∅ (added file) | <code>&quot;    args = p.parse_args()&quot;</code> |
| trinity_read.py:1268 | BEYOND | ∅ (added file) | <code>&quot;    if args.command == &#x27;need&#x27; and not args.all and not args.family: p.error(&#x27;need requires --family unless --all&#x27;)&quot;</code> |
| trinity_read.py:1269 | BEYOND | ∅ (added file) | <code>&quot;    if args.command == &#x27;need&#x27; and args.all and args.family: p.error(&#x27;--all spans all three families; omit --family&#x27;)&quot;</code> |
| trinity_read.py:1270 | BEYOND | ∅ (added file) | <code>&quot;    if args.command == &#x27;stage&#x27;: print(json.dumps(stage(args.root, args.dl), sort_keys=True))&quot;</code> |
| trinity_read.py:1271 | BEYOND | ∅ (added file) | <code>&quot;    elif args.command == &#x27;frames&#x27;: print(json.dumps(frames(args.root, args.tar), sort_keys=True))&quot;</code> |
| trinity_read.py:1272 | BEYOND | ∅ (added file) | <code>&quot;    elif args.command == &#x27;need&#x27;: need_command(args)&quot;</code> |
| trinity_read.py:1273 | BEYOND | ∅ (added file) | <code>&quot;    elif args.command == &#x27;probe&#x27;:&quot;</code> |
| trinity_read.py:1274 | BEYOND | ∅ (added file) | <code>&quot;        print(json.dumps(probe(args.root, args.shm, args.bwrap, args.llguidance_stub), sort_keys=True, indent=2))&quot;</code> |
| trinity_read.py:1275 | BEYOND | ∅ (added file) | <code>&quot;    elif args.command == &#x27;selfcheck&#x27;:&quot;</code> |
| trinity_read.py:1276 | BEYOND | ∅ (added file) | <code>&quot;        result = selfcheck(args.root, args.bwrap); print(json.dumps(result, sort_keys=True, indent=2))&quot;</code> |
| trinity_read.py:1277 | BEYOND | ∅ (added file) | <code>&quot;        if not result[&#x27;passed&#x27;]: raise RuntimeError(&#x27;Selfcheck incomplete or failed; inspect the JSON report&#x27;)&quot;</code> |
| trinity_read.py:1278 | BEYOND | ∅ (added file) | <code>&quot;    else: launch(args)&quot;</code> |
| trinity_read.py:1279 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1280 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| trinity_read.py:1281 | BEYOND | ∅ (added file) | <code>&quot;if __name__ == &#x27;__main__&#x27;:&quot;</code> |
| trinity_read.py:1282 | BEYOND | ∅ (added file) | <code>&quot;    try: main()&quot;</code> |
| trinity_read.py:1283 | BEYOND | ∅ (added file) | <code>&quot;    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:&quot;</code> |
| trinity_read.py:1284 | BEYOND | ∅ (added file) | <code>&quot;        print(&#x27;REFUSED: &#x27;+str(error), file=sys.stderr); sys.exit(2)&quot;</code> |
| namespace_worker.py:1 | BEYOND | ∅ (added file) | <code>&quot;\&quot;\&quot;\&quot;CPU planning and production wrapper, executed inside the staged namespace.\&quot;\&quot;\&quot;&quot;</code> |
| namespace_worker.py:2 | BEYOND | ∅ (added file) | <code>&quot;import argparse&quot;</code> |
| namespace_worker.py:3 | BEYOND | ∅ (added file) | <code>&quot;import hashlib&quot;</code> |
| namespace_worker.py:4 | BEYOND | ∅ (added file) | <code>&quot;import json&quot;</code> |
| namespace_worker.py:5 | BEYOND | ∅ (added file) | <code>&quot;import os&quot;</code> |
| namespace_worker.py:6 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| namespace_worker.py:7 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| namespace_worker.py:8 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace as NS&quot;</code> |
| namespace_worker.py:9 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:10 | BEYOND | ∅ (added file) | <code>&quot;sys.dont_write_bytecode = True&quot;</code> |
| namespace_worker.py:11 | BEYOND | ∅ (added file) | <code>&quot;sys.path.insert(0, str(Path(__file__).resolve().parent))&quot;</code> |
| namespace_worker.py:12 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| namespace_worker.py:13 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:14 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:15 | BEYOND | ∅ (added file) | <code>&quot;def bind_plan(config, family, work, ids=None, first=None, reader=None, kit=None):&quot;</code> |
| namespace_worker.py:16 | BEYOND | ∅ (added file) | <code>&quot;    if family not in T.FAMILIES:&quot;</code> |
| namespace_worker.py:17 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;Only main, away and forward dev-S1 direct families are allowed&#x27;)&quot;</code> |
| namespace_worker.py:18 | BEYOND | ∅ (added file) | <code>&quot;    reader = Path(reader or &#x27;/scratch/jjyeung/orch_cd/legs1_reads&#x27;)&quot;</code> |
| namespace_worker.py:19 | BEYOND | ∅ (added file) | <code>&quot;    kit = Path(kit or &#x27;/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt&#x27;)&quot;</code> |
| namespace_worker.py:20 | BEYOND | ∅ (added file) | <code>&quot;    sys.path.insert(0, str(reader/&#x27;out&#x27;))&quot;</code> |
| namespace_worker.py:21 | BEYOND | ∅ (added file) | <code>&quot;    import direct&quot;</code> |
| namespace_worker.py:22 | BEYOND | ∅ (added file) | <code>&quot;    spec = config[&#x27;spec&#x27;]; work = Path(work)&quot;</code> |
| namespace_worker.py:23 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(work/&#x27;models.json&#x27;, spec[&#x27;models&#x27;])&quot;</code> |
| namespace_worker.py:24 | BEYOND | ∅ (added file) | <code>&quot;    dest = work/&#x27;direct&#x27;/family&quot;</code> |
| namespace_worker.py:25 | BEYOND | ∅ (added file) | <code>&quot;    direct.bind(NS(dest=str(dest), models=str(work/&#x27;models.json&#x27;), export=spec[&#x27;artifact&#x27;][&#x27;path&#x27;],&quot;</code> |
| namespace_worker.py:26 | BEYOND | ∅ (added file) | <code>&quot;                   sha256=spec[&#x27;artifact&#x27;][&#x27;sha256&#x27;], step=spec[&#x27;step&#x27;], family=family, kit=str(kit),&quot;</code> |
| namespace_worker.py:27 | BEYOND | ∅ (added file) | <code>&quot;                   frames_root=str(work/&#x27;pulled&#x27;), dry=True, parent_standin=False))&quot;</code> |
| namespace_worker.py:28 | BEYOND | ∅ (added file) | <code>&quot;    cfg = T.load(dest/&#x27;request.json&#x27;)&quot;</code> |
| namespace_worker.py:29 | BEYOND | ∅ (added file) | <code>&quot;    vendor, _ = direct.modules(); origin = vendor.R3 if family == &#x27;main&#x27; else vendor.R4&quot;</code> |
| namespace_worker.py:30 | BEYOND | ∅ (added file) | <code>&quot;    data, media, _ = origin.kit_import(dest/&#x27;kit&#x27;)&quot;</code> |
| namespace_worker.py:31 | BEYOND | ∅ (added file) | <code>&quot;    from worker import select_tasks&quot;</code> |
| namespace_worker.py:32 | BEYOND | ∅ (added file) | <code>&quot;    all_tasks = select_tasks(data.tasks_for(cfg[&#x27;datasets&#x27;][0], cfg[&#x27;roots&#x27;]), cfg[&#x27;cells&#x27;][0])&quot;</code> |
| namespace_worker.py:33 | BEYOND | ∅ (added file) | <code>&quot;    tasks = T.selected_tasks(all_tasks, ids, first)&quot;</code> |
| namespace_worker.py:34 | BEYOND | ∅ (added file) | <code>&quot;    _, _, _, captures = origin.payload(direct.PAYLOADS[family])&quot;</code> |
| namespace_worker.py:35 | BEYOND | ∅ (added file) | <code>&quot;    captures = {t[&#x27;native&#x27;]:captures[t[&#x27;native&#x27;]] for t in tasks}&quot;</code> |
| namespace_worker.py:36 | BEYOND | ∅ (added file) | <code>&quot;    need = T.needed(captures, tasks)&quot;</code> |
| namespace_worker.py:37 | BEYOND | ∅ (added file) | <code>&quot;    estimates = {f[&#x27;sha256&#x27;]:c[&#x27;hw&#x27;][0]*c[&#x27;hw&#x27;][1]*3 for c in captures.values() for f in c[&#x27;frames&#x27;]}&quot;</code> |
| namespace_worker.py:38 | BEYOND | ∅ (added file) | <code>&quot;    report = dict(family=family, items=len(tasks), family_items=len(all_tasks), ids=[t[&#x27;example_id&#x27;] for t in tasks],&quot;</code> |
| namespace_worker.py:39 | BEYOND | ∅ (added file) | <code>&quot;                  need=need, frames=len(need), captures=len(captures), estimated_frame_bytes=estimates)&quot;</code> |
| namespace_worker.py:40 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(work/&#x27;NEED.json&#x27;, report)&quot;</code> |
| namespace_worker.py:41 | BEYOND | ∅ (added file) | <code>&quot;    return direct, origin, data, media, dest, cfg, tasks, captures, report&quot;</code> |
| namespace_worker.py:42 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:43 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:44 | BEYOND | ∅ (added file) | <code>&quot;def install_filter(data, ids):&quot;</code> |
| namespace_worker.py:45 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Filter the shared loader and its already imported aliases; preserve sorted worker order.\&quot;\&quot;\&quot;&quot;</code> |
| namespace_worker.py:46 | BEYOND | ∅ (added file) | <code>&quot;    original = data.tasks_for; wanted = set(ids)&quot;</code> |
| namespace_worker.py:47 | BEYOND | ∅ (added file) | <code>&quot;    def filtered(spec, roots):&quot;</code> |
| namespace_worker.py:48 | BEYOND | ∅ (added file) | <code>&quot;        if spec[&#x27;benchmark&#x27;] != &#x27;devrows&#x27;: raise ValueError(&#x27;Only devrows may reach the reader&#x27;)&quot;</code> |
| namespace_worker.py:49 | BEYOND | ∅ (added file) | <code>&quot;        tasks = original(spec, roots)&quot;</code> |
| namespace_worker.py:50 | BEYOND | ∅ (added file) | <code>&quot;        return T.selected_tasks(tasks, list(wanted))&quot;</code> |
| namespace_worker.py:51 | BEYOND | ∅ (added file) | <code>&quot;    for module in list(sys.modules.values()):&quot;</code> |
| namespace_worker.py:52 | BEYOND | ∅ (added file) | <code>&quot;        if module is not None and getattr(module, &#x27;tasks_for&#x27;, None) is original:&quot;</code> |
| namespace_worker.py:53 | BEYOND | ∅ (added file) | <code>&quot;            module.tasks_for = filtered&quot;</code> |
| namespace_worker.py:54 | BEYOND | ∅ (added file) | <code>&quot;    data.tasks_for = filtered&quot;</code> |
| namespace_worker.py:55 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:56 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:57 | BEYOND | ∅ (added file) | <code>&quot;def run(request, config):&quot;</code> |
| namespace_worker.py:58 | BEYOND | ∅ (added file) | <code>&quot;    work = Path(request[&#x27;work&#x27;])&quot;</code> |
| namespace_worker.py:59 | BEYOND | ∅ (added file) | <code>&quot;    direct, origin, data, media, dest, cfg, tasks, captures, report = bind_plan(&quot;</code> |
| namespace_worker.py:60 | BEYOND | ∅ (added file) | <code>&quot;        config, request[&#x27;family&#x27;], work, request.get(&#x27;ids&#x27;), request.get(&#x27;first&#x27;))&quot;</code> |
| namespace_worker.py:61 | BEYOND | ∅ (added file) | <code>&quot;    if request[&#x27;action&#x27;] == &#x27;need&#x27;:&quot;</code> |
| namespace_worker.py:62 | BEYOND | ∅ (added file) | <code>&quot;        return report&quot;</code> |
| namespace_worker.py:63 | BEYOND | ∅ (added file) | <code>&quot;    if request[&#x27;action&#x27;] != &#x27;read&#x27;: raise ValueError(&#x27;Unknown worker action&#x27;)&quot;</code> |
| namespace_worker.py:64 | BEYOND | ∅ (added file) | <code>&quot;    root = Path(os.environ[&#x27;A_JOB_ROOT&#x27;])&quot;</code> |
| namespace_worker.py:65 | BEYOND | ∅ (added file) | <code>&quot;    missing = sorted(set(report[&#x27;need&#x27;])-set(T.store_index(root)))&quot;</code> |
| namespace_worker.py:66 | BEYOND | ∅ (added file) | <code>&quot;    if missing:&quot;</code> |
| namespace_worker.py:67 | BEYOND | ∅ (added file) | <code>&quot;        (work/&#x27;NEED.txt&#x27;).write_text(&#x27;&#x27;.join(h+&#x27;\\n&#x27; for h in missing))&quot;</code> |
| namespace_worker.py:68 | BEYOND | ∅ (added file) | <code>&quot;        raise ValueError(&#x27;NEED: frames absent; refusing launch&#x27;)&quot;</code> |
| namespace_worker.py:69 | BEYOND | ∅ (added file) | <code>&quot;    spec = config[&#x27;spec&#x27;]&quot;</code> |
| namespace_worker.py:70 | BEYOND | ∅ (added file) | <code>&quot;    cfg[&#x27;smoke_items&#x27;] = len(tasks) if len(tasks) &lt; report[&#x27;family_items&#x27;] else 0&quot;</code> |
| namespace_worker.py:71 | BEYOND | ∅ (added file) | <code>&quot;    cfg[&#x27;build_only&#x27;] = False&quot;</code> |
| namespace_worker.py:72 | BEYOND | ∅ (added file) | <code>&quot;    cfg[&#x27;legs1&#x27;][&#x27;export_verification&#x27;] = direct.check_export(&quot;</code> |
| namespace_worker.py:73 | BEYOND | ∅ (added file) | <code>&quot;        spec[&#x27;artifact&#x27;][&#x27;path&#x27;], spec[&#x27;artifact&#x27;][&#x27;sha256&#x27;], spec[&#x27;models&#x27;][&#x27;base&#x27;][&#x27;path&#x27;], spec[&#x27;step&#x27;])&quot;</code> |
| namespace_worker.py:74 | BEYOND | ∅ (added file) | <code>&quot;    cfg[&#x27;legs1&#x27;][&#x27;export_bytes_verified&#x27;] = True&quot;</code> |
| namespace_worker.py:75 | BEYOND | ∅ (added file) | <code>&quot;    selection = dict(ids=report[&#x27;ids&#x27;], family=request[&#x27;family&#x27;],&quot;</code> |
| namespace_worker.py:76 | BEYOND | ∅ (added file) | <code>&quot;                     order=[&#x27;benchmark&#x27;, &#x27;example_id&#x27;], wrapper_sha256=T.sha(__file__))&quot;</code> |
| namespace_worker.py:77 | BEYOND | ∅ (added file) | <code>&quot;    cfg[&#x27;trinity_selection&#x27;] = selection&quot;</code> |
| namespace_worker.py:78 | BEYOND | ∅ (added file) | <code>&quot;    cfg[&#x27;binding&#x27;] = hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in (&#x27;binding&#x27;,&#x27;output&#x27;)}, sort_keys=True).encode()).hexdigest()&quot;</code> |
| namespace_worker.py:79 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(dest/&#x27;request.json&#x27;, cfg)&quot;</code> |
| namespace_worker.py:80 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(dest/&#x27;SELECTION.json&#x27;, selection)&quot;</code> |
| namespace_worker.py:81 | BEYOND | ∅ (added file) | <code>&quot;    sys.path.insert(0, str(Path(spec[&#x27;package&#x27;])/&#x27;proof&#x27;))&quot;</code> |
| namespace_worker.py:82 | BEYOND | ∅ (added file) | <code>&quot;    import phase_b&quot;</code> |
| namespace_worker.py:83 | BEYOND | ∅ (added file) | <code>&quot;    phase_b.pull_frames(set(report[&#x27;need&#x27;]), T.STORE, work/&#x27;pulled&#x27;, spec[&#x27;interpreters&#x27;][&#x27;p1cpu&#x27;])&quot;</code> |
| namespace_worker.py:84 | BEYOND | ∅ (added file) | <code>&quot;    frame_sha = origin.make_frames(cfg, tasks, captures, media, work/&#x27;pulled&#x27;, dest/&#x27;frames&#x27;)&quot;</code> |
| namespace_worker.py:85 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(dest/&#x27;BIND_STATUS.json&#x27;, dict(ready=True, dry=False, tasks=len(tasks),&quot;</code> |
| namespace_worker.py:86 | BEYOND | ∅ (added file) | <code>&quot;                                      smoke_items=cfg[&#x27;smoke_items&#x27;], frames_sha256=frame_sha))&quot;</code> |
| namespace_worker.py:87 | BEYOND | ∅ (added file) | <code>&quot;    install_filter(data, report[&#x27;ids&#x27;])&quot;</code> |
| namespace_worker.py:88 | BEYOND | ∅ (added file) | <code>&quot;    direct.launch(NS(dest=str(dest), attempt=request[&#x27;attempt&#x27;]))&quot;</code> |
| namespace_worker.py:89 | BEYOND | ∅ (added file) | <code>&quot;    summaries = {}&quot;</code> |
| namespace_worker.py:90 | BEYOND | ∅ (added file) | <code>&quot;    for arm, rel in [(&#x27;ON16k&#x27;,&#x27;0&#x27;), (&#x27;B2048&#x27;,&#x27;budget_2048/0&#x27;), (&#x27;B4096&#x27;,&#x27;budget_4096/0&#x27;)]:&quot;</code> |
| namespace_worker.py:91 | BEYOND | ∅ (added file) | <code>&quot;        summary = T.load(dest/&#x27;results&#x27;/rel/(&#x27;summary_&#x27;+request[&#x27;attempt&#x27;]+&#x27;.json&#x27;))&quot;</code> |
| namespace_worker.py:92 | BEYOND | ∅ (added file) | <code>&quot;        summaries[arm] = summary&quot;</code> |
| namespace_worker.py:93 | BEYOND | ∅ (added file) | <code>&quot;        if not summary[&#x27;parity_pass&#x27;]:&quot;</code> |
| namespace_worker.py:94 | BEYOND | ∅ (added file) | <code>&quot;            raise ValueError(&#x27;Prompt/pixel parity failed for &#x27;+arm)&quot;</code> |
| namespace_worker.py:95 | BEYOND | ∅ (added file) | <code>&quot;        for benchmark in summary[&#x27;benchmarks&#x27;].values():&quot;</code> |
| namespace_worker.py:96 | BEYOND | ∅ (added file) | <code>&quot;            if benchmark[&#x27;missing&#x27;] or benchmark[&#x27;completed&#x27;] != benchmark[&#x27;expected&#x27;]:&quot;</code> |
| namespace_worker.py:97 | BEYOND | ∅ (added file) | <code>&quot;                raise ValueError(&#x27;Incomplete item coverage for &#x27;+arm)&quot;</code> |
| namespace_worker.py:98 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(work/&#x27;SUMMARIES.json&#x27;, summaries)&quot;</code> |
| namespace_worker.py:99 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(work/&#x27;SPEC.json&#x27;, spec)&quot;</code> |
| namespace_worker.py:100 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(work/&#x27;CODE_PINS.json&#x27;, dict(wrapper=T.sha(__file__), direct=T.sha(direct.__file__),&quot;</code> |
| namespace_worker.py:101 | BEYOND | ∅ (added file) | <code>&quot;                                     evaluator=T.load(dest/&#x27;kit/CODE_PINS.json&#x27;)))&quot;</code> |
| namespace_worker.py:102 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(work/&#x27;COMPLETE.json&#x27;, dict(family=request[&#x27;family&#x27;], ids=report[&#x27;ids&#x27;], arms=list(summaries)))&quot;</code> |
| namespace_worker.py:103 | BEYOND | ∅ (added file) | <code>&quot;    return report&quot;</code> |
| namespace_worker.py:104 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:105 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| namespace_worker.py:106 | BEYOND | ∅ (added file) | <code>&quot;if __name__ == &#x27;__main__&#x27;:&quot;</code> |
| namespace_worker.py:107 | BEYOND | ∅ (added file) | <code>&quot;    parser = argparse.ArgumentParser(); parser.add_argument(&#x27;--input&#x27;, required=True)&quot;</code> |
| namespace_worker.py:108 | BEYOND | ∅ (added file) | <code>&quot;    args = parser.parse_args(); request = T.load(args.input)&quot;</code> |
| namespace_worker.py:109 | BEYOND | ∅ (added file) | <code>&quot;    config = T.load(request.get(&#x27;config&#x27;, os.environ[&#x27;A_JOB_CONFIG&#x27;]))&quot;</code> |
| namespace_worker.py:110 | BEYOND | ∅ (added file) | <code>&quot;    result = run(request, config)&quot;</code> |
| namespace_worker.py:111 | BEYOND | ∅ (added file) | <code>&quot;    print(json.dumps({k:result[k] for k in (&#x27;family&#x27;,&#x27;items&#x27;,&#x27;frames&#x27;)}, sort_keys=True))&quot;</code> |
| compare_tokens.py:1 | BEYOND | ∅ (added file) | <code>&quot;#!/usr/bin/env python3&quot;</code> |
| compare_tokens.py:2 | BEYOND | ∅ (added file) | <code>&quot;\&quot;\&quot;\&quot;Exact accepted/actual token comparison, with explicit missing data and timing scope.\&quot;\&quot;\&quot;&quot;</code> |
| compare_tokens.py:3 | BEYOND | ∅ (added file) | <code>&quot;import argparse&quot;</code> |
| compare_tokens.py:4 | BEYOND | ∅ (added file) | <code>&quot;import json&quot;</code> |
| compare_tokens.py:5 | BEYOND | ∅ (added file) | <code>&quot;import math&quot;</code> |
| compare_tokens.py:6 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| compare_tokens.py:7 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:8 | BEYOND | ∅ (added file) | <code>&quot;ARMS = {&#x27;ON16k&#x27;:&#x27;0&#x27;, &#x27;B2048&#x27;:&#x27;budget_2048/0&#x27;, &#x27;B4096&#x27;:&#x27;budget_4096/0&#x27;}&quot;</code> |
| compare_tokens.py:9 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:10 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:11 | BEYOND | ∅ (added file) | <code>&quot;def load(path):&quot;</code> |
| compare_tokens.py:12 | BEYOND | ∅ (added file) | <code>&quot;    return json.loads(Path(path).read_text())&quot;</code> |
| compare_tokens.py:13 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:14 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:15 | BEYOND | ∅ (added file) | <code>&quot;def rows(path):&quot;</code> |
| compare_tokens.py:16 | BEYOND | ∅ (added file) | <code>&quot;    path = Path(path)&quot;</code> |
| compare_tokens.py:17 | BEYOND | ∅ (added file) | <code>&quot;    if not path.exists(): return []&quot;</code> |
| compare_tokens.py:18 | BEYOND | ∅ (added file) | <code>&quot;    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]&quot;</code> |
| compare_tokens.py:19 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:20 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:21 | BEYOND | ∅ (added file) | <code>&quot;def compare_row(accepted, actual):&quot;</code> |
| compare_tokens.py:22 | BEYOND | ∅ (added file) | <code>&quot;    actual = actual or {}&quot;</code> |
| compare_tokens.py:23 | BEYOND | ∅ (added file) | <code>&quot;    left, right = accepted.get(&#x27;token_ids&#x27;), actual.get(&#x27;token_ids&#x27;)&quot;</code> |
| compare_tokens.py:24 | BEYOND | ∅ (added file) | <code>&quot;    valid = (isinstance(left, list) and isinstance(right, list)&quot;</code> |
| compare_tokens.py:25 | BEYOND | ∅ (added file) | <code>&quot;             and all(type(i) is int and i &gt;= 0 for i in left+right))&quot;</code> |
| compare_tokens.py:26 | BEYOND | ∅ (added file) | <code>&quot;    divergence = None&quot;</code> |
| compare_tokens.py:27 | BEYOND | ∅ (added file) | <code>&quot;    if valid:&quot;</code> |
| compare_tokens.py:28 | BEYOND | ∅ (added file) | <code>&quot;        divergence = next((i for i, (a,b) in enumerate(zip(left,right)) if a != b), None)&quot;</code> |
| compare_tokens.py:29 | BEYOND | ∅ (added file) | <code>&quot;        if divergence is None and len(left) != len(right): divergence = min(len(left),len(right))&quot;</code> |
| compare_tokens.py:30 | BEYOND | ∅ (added file) | <code>&quot;    fields = (&#x27;raw_generation&#x27;,&#x27;extracted_answer&#x27;,&#x27;score&#x27;)&quot;</code> |
| compare_tokens.py:31 | BEYOND | ∅ (added file) | <code>&quot;    return dict(example_id=accepted[&#x27;example_id&#x27;], present=bool(actual), token_ids_identical=valid and left == right,&quot;</code> |
| compare_tokens.py:32 | BEYOND | ∅ (added file) | <code>&quot;                first_divergence_index=divergence, accepted_length=len(left) if isinstance(left,list) else None,&quot;</code> |
| compare_tokens.py:33 | BEYOND | ∅ (added file) | <code>&quot;                actual_length=len(right) if isinstance(right,list) else None,&quot;</code> |
| compare_tokens.py:34 | BEYOND | ∅ (added file) | <code>&quot;                **{key+&#x27;_equal&#x27;:key in accepted and key in actual and accepted[key] == actual[key] for key in fields},&quot;</code> |
| compare_tokens.py:35 | BEYOND | ∅ (added file) | <code>&quot;                accepted_answer=accepted.get(&#x27;extracted_answer&#x27;), actual_answer=actual.get(&#x27;extracted_answer&#x27;),&quot;</code> |
| compare_tokens.py:36 | BEYOND | ∅ (added file) | <code>&quot;                accepted_score=accepted.get(&#x27;score&#x27;), actual_score=actual.get(&#x27;score&#x27;))&quot;</code> |
| compare_tokens.py:37 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:38 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:39 | BEYOND | ∅ (added file) | <code>&quot;def unique(values):&quot;</code> |
| compare_tokens.py:40 | BEYOND | ∅ (added file) | <code>&quot;    result = {}&quot;</code> |
| compare_tokens.py:41 | BEYOND | ∅ (added file) | <code>&quot;    for row in values:&quot;</code> |
| compare_tokens.py:42 | BEYOND | ∅ (added file) | <code>&quot;        key = row[&#x27;example_id&#x27;]&quot;</code> |
| compare_tokens.py:43 | BEYOND | ∅ (added file) | <code>&quot;        if key in result: raise ValueError(&#x27;Duplicate result ID: &#x27;+key)&quot;</code> |
| compare_tokens.py:44 | BEYOND | ∅ (added file) | <code>&quot;        result[key] = row&quot;</code> |
| compare_tokens.py:45 | BEYOND | ∅ (added file) | <code>&quot;    return result&quot;</code> |
| compare_tokens.py:46 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:47 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:48 | BEYOND | ∅ (added file) | <code>&quot;def positive_seconds(row):&quot;</code> |
| compare_tokens.py:49 | BEYOND | ∅ (added file) | <code>&quot;    value = row.get(&#x27;seconds&#x27;)&quot;</code> |
| compare_tokens.py:50 | BEYOND | ∅ (added file) | <code>&quot;    return float(value) if isinstance(value, (int,float)) and math.isfinite(value) and value &gt; 0 else None&quot;</code> |
| compare_tokens.py:51 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:52 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:53 | BEYOND | ∅ (added file) | <code>&quot;def timing(dest, arm, ids):&quot;</code> |
| compare_tokens.py:54 | BEYOND | ∅ (added file) | <code>&quot;    # Read worker journals; budget meta distinguishes reused ON rows from fresh generations.&quot;</code> |
| compare_tokens.py:55 | BEYOND | ∅ (added file) | <code>&quot;    base = Path(dest)/&#x27;results/0&#x27;&quot;</code> |
| compare_tokens.py:56 | BEYOND | ∅ (added file) | <code>&quot;    path = base/&#x27;g0.jsonl&#x27; if arm == &#x27;ON16k&#x27; else base/(&#x27;budget_&#x27;+arm[1:]+&#x27;.g0.jsonl&#x27;)&quot;</code> |
| compare_tokens.py:57 | BEYOND | ∅ (added file) | <code>&quot;    journal = unique(rows(path)); meta = {}&quot;</code> |
| compare_tokens.py:58 | BEYOND | ∅ (added file) | <code>&quot;    if arm != &#x27;ON16k&#x27;:&quot;</code> |
| compare_tokens.py:59 | BEYOND | ∅ (added file) | <code>&quot;        for row in rows(path.with_suffix(&#x27;.meta.jsonl&#x27;)):&quot;</code> |
| compare_tokens.py:60 | BEYOND | ∅ (added file) | <code>&quot;            key = row.get(&#x27;source_key&#x27;, &#x27;&#x27;).split(&#x27;:&#x27;, 1)[-1]&quot;</code> |
| compare_tokens.py:61 | BEYOND | ∅ (added file) | <code>&quot;            if key in meta and meta[key] != row: raise ValueError(&#x27;Conflicting budget timing receipts&#x27;)&quot;</code> |
| compare_tokens.py:62 | BEYOND | ∅ (added file) | <code>&quot;            meta[key] = row&quot;</code> |
| compare_tokens.py:63 | BEYOND | ∅ (added file) | <code>&quot;    items = []&quot;</code> |
| compare_tokens.py:64 | BEYOND | ∅ (added file) | <code>&quot;    for key in ids:&quot;</code> |
| compare_tokens.py:65 | BEYOND | ∅ (added file) | <code>&quot;        row = journal.get(key, {}); receipt = meta.get(key, {})&quot;</code> |
| compare_tokens.py:66 | BEYOND | ∅ (added file) | <code>&quot;        reused = arm != &#x27;ON16k&#x27; and receipt.get(&#x27;answer_cap_policy&#x27;) == &#x27;reuse_full_on_answer&#x27;&quot;</code> |
| compare_tokens.py:67 | BEYOND | ∅ (added file) | <code>&quot;        generated = arm == &#x27;ON16k&#x27; or (receipt.get(&#x27;answer_cap_policy&#x27;) == &#x27;continuation_64&#x27; and not receipt.get(&#x27;derivation_error&#x27;))&quot;</code> |
| compare_tokens.py:68 | BEYOND | ∅ (added file) | <code>&quot;        seconds = positive_seconds(row) if generated else None&quot;</code> |
| compare_tokens.py:69 | BEYOND | ∅ (added file) | <code>&quot;        count = len(row[&#x27;token_ids&#x27;]) if generated and isinstance(row.get(&#x27;token_ids&#x27;),list) else None&quot;</code> |
| compare_tokens.py:70 | BEYOND | ∅ (added file) | <code>&quot;        items.append(dict(example_id=key, seconds=seconds, generated_tokens=count,&quot;</code> |
| compare_tokens.py:71 | BEYOND | ∅ (added file) | <code>&quot;                          generated_tokens_per_second=count/seconds if count is not None and seconds else None,&quot;</code> |
| compare_tokens.py:72 | BEYOND | ∅ (added file) | <code>&quot;                          reused_on_generation=reused,&quot;</code> |
| compare_tokens.py:73 | BEYOND | ∅ (added file) | <code>&quot;                          timing_kind=&#x27;generation_latency&#x27; if generated else &#x27;no_new_generation_or_missing_receipt&#x27;))&quot;</code> |
| compare_tokens.py:74 | BEYOND | ∅ (added file) | <code>&quot;    measured = [r for r in items if r[&#x27;seconds&#x27;] is not None and r[&#x27;generated_tokens&#x27;] is not None]&quot;</code> |
| compare_tokens.py:75 | BEYOND | ∅ (added file) | <code>&quot;    return dict(items=items, measured_items=len(measured),&quot;</code> |
| compare_tokens.py:76 | BEYOND | ∅ (added file) | <code>&quot;                mean_seconds_per_measured_item=sum(r[&#x27;seconds&#x27;] for r in measured)/len(measured) if measured else None,&quot;</code> |
| compare_tokens.py:77 | BEYOND | ∅ (added file) | <code>&quot;                generated_tokens_per_sum_latency=sum(r[&#x27;generated_tokens&#x27;] for r in measured)/sum(r[&#x27;seconds&#x27;] for r in measured) if measured else None,&quot;</code> |
| compare_tokens.py:78 | BEYOND | ∅ (added file) | <code>&quot;                note=&#x27;Concurrent per-request latencies, not wall-clock throughput. Reused ON rows are not counted as new budget generations.&#x27;)&quot;</code> |
| compare_tokens.py:79 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:80 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:81 | BEYOND | ∅ (added file) | <code>&quot;def compare(reference, actual_by_arm):&quot;</code> |
| compare_tokens.py:82 | BEYOND | ∅ (added file) | <code>&quot;    ids = reference[&#x27;ids&#x27;]; arms = {}; passed = True&quot;</code> |
| compare_tokens.py:83 | BEYOND | ∅ (added file) | <code>&quot;    if not ids or len(ids) != len(set(ids)): raise ValueError(&#x27;Invalid reference membership&#x27;)&quot;</code> |
| compare_tokens.py:84 | BEYOND | ∅ (added file) | <code>&quot;    for arm in ARMS:&quot;</code> |
| compare_tokens.py:85 | BEYOND | ∅ (added file) | <code>&quot;        expected = unique(reference[&#x27;arms&#x27;][arm]); actual = unique(actual_by_arm.get(arm, []))&quot;</code> |
| compare_tokens.py:86 | BEYOND | ∅ (added file) | <code>&quot;        if set(expected) != set(ids): raise ValueError(&#x27;Reference arm membership differs&#x27;)&quot;</code> |
| compare_tokens.py:87 | BEYOND | ∅ (added file) | <code>&quot;        checks = [compare_row(expected[key], actual.get(key)) for key in ids]&quot;</code> |
| compare_tokens.py:88 | BEYOND | ∅ (added file) | <code>&quot;        equal = all(c[&#x27;token_ids_identical&#x27;] and all(c[k+&#x27;_equal&#x27;] for k in (&#x27;raw_generation&#x27;,&#x27;extracted_answer&#x27;,&#x27;score&#x27;)) for c in checks)&quot;</code> |
| compare_tokens.py:89 | BEYOND | ∅ (added file) | <code>&quot;        complete = set(actual) == set(ids)&quot;</code> |
| compare_tokens.py:90 | BEYOND | ∅ (added file) | <code>&quot;        scores = [actual[key].get(&#x27;score&#x27;) for key in ids if key in actual]&quot;</code> |
| compare_tokens.py:91 | BEYOND | ∅ (added file) | <code>&quot;        numeric = len(scores) == len(ids) and all(isinstance(s,(int,float)) and math.isfinite(s) for s in scores)&quot;</code> |
| compare_tokens.py:92 | BEYOND | ∅ (added file) | <code>&quot;        arms[arm] = dict(items=checks, identical_items=sum(c[&#x27;token_ids_identical&#x27;] for c in checks),&quot;</code> |
| compare_tokens.py:93 | BEYOND | ∅ (added file) | <code>&quot;                         membership_equal=complete, unexpected_ids=sorted(set(actual)-set(ids)),&quot;</code> |
| compare_tokens.py:94 | BEYOND | ∅ (added file) | <code>&quot;                         mean_score_actual=sum(scores)/len(ids) if numeric else None,&quot;</code> |
| compare_tokens.py:95 | BEYOND | ∅ (added file) | <code>&quot;                         mean_score_accepted=sum(expected[key][&#x27;score&#x27;] for key in ids)/len(ids))&quot;</code> |
| compare_tokens.py:96 | BEYOND | ∅ (added file) | <code>&quot;        passed = passed and equal and complete&quot;</code> |
| compare_tokens.py:97 | BEYOND | ∅ (added file) | <code>&quot;    return dict(passed=passed, items=len(ids), arms=arms)&quot;</code> |
| compare_tokens.py:98 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:99 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:100 | BEYOND | ∅ (added file) | <code>&quot;def write_report(reference_path, dest, attempt, out, memory=None, exit_path=None):&quot;</code> |
| compare_tokens.py:101 | BEYOND | ∅ (added file) | <code>&quot;    from trinity_read import writable&quot;</code> |
| compare_tokens.py:102 | BEYOND | ∅ (added file) | <code>&quot;    reference = load(reference_path); dest = Path(dest); out = writable(out)&quot;</code> |
| compare_tokens.py:103 | BEYOND | ∅ (added file) | <code>&quot;    errors = []; actual = {}&quot;</code> |
| compare_tokens.py:104 | BEYOND | ∅ (added file) | <code>&quot;    for arm,rel in ARMS.items():&quot;</code> |
| compare_tokens.py:105 | BEYOND | ∅ (added file) | <code>&quot;        try:&quot;</code> |
| compare_tokens.py:106 | BEYOND | ∅ (added file) | <code>&quot;            actual[arm] = rows(dest/&#x27;results&#x27;/rel/(&#x27;items_&#x27;+attempt+&#x27;.jsonl&#x27;))&quot;</code> |
| compare_tokens.py:107 | BEYOND | ∅ (added file) | <code>&quot;            unique(actual[arm])&quot;</code> |
| compare_tokens.py:108 | BEYOND | ∅ (added file) | <code>&quot;        except (ValueError, KeyError, OSError) as error:&quot;</code> |
| compare_tokens.py:109 | BEYOND | ∅ (added file) | <code>&quot;            errors.append(arm+&#x27; results: &#x27;+str(error)); actual[arm] = []&quot;</code> |
| compare_tokens.py:110 | BEYOND | ∅ (added file) | <code>&quot;    report = compare(reference, actual)&quot;</code> |
| compare_tokens.py:111 | BEYOND | ∅ (added file) | <code>&quot;    for arm in ARMS:&quot;</code> |
| compare_tokens.py:112 | BEYOND | ∅ (added file) | <code>&quot;        try: report[&#x27;arms&#x27;][arm][&#x27;timing&#x27;] = timing(dest,arm,reference[&#x27;ids&#x27;])&quot;</code> |
| compare_tokens.py:113 | BEYOND | ∅ (added file) | <code>&quot;        except (ValueError, KeyError, OSError) as error:&quot;</code> |
| compare_tokens.py:114 | BEYOND | ∅ (added file) | <code>&quot;            errors.append(arm+&#x27; timing: &#x27;+str(error))&quot;</code> |
| compare_tokens.py:115 | BEYOND | ∅ (added file) | <code>&quot;            report[&#x27;arms&#x27;][arm][&#x27;timing&#x27;] = dict(items=[dict(example_id=k,seconds=None,generated_tokens_per_second=None) for k in reference[&#x27;ids&#x27;]], error=str(error))&quot;</code> |
| compare_tokens.py:116 | BEYOND | ∅ (added file) | <code>&quot;    try: samples = rows(memory) if memory else []&quot;</code> |
| compare_tokens.py:117 | BEYOND | ∅ (added file) | <code>&quot;    except (ValueError, OSError) as error:&quot;</code> |
| compare_tokens.py:118 | BEYOND | ∅ (added file) | <code>&quot;        errors.append(&#x27;memory: &#x27;+str(error)); samples = []&quot;</code> |
| compare_tokens.py:119 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;peak_card_memory_mib&#x27;] = max((s[&#x27;memory_used_mib&#x27;] for s in samples), default=None)&quot;</code> |
| compare_tokens.py:120 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;memory_samples&#x27;] = len(samples)&quot;</code> |
| compare_tokens.py:121 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;memory_note&#x27;] = &#x27;Maximum observed 1 s nvidia-smi sample; shorter peaks may be missed.&#x27;&quot;</code> |
| compare_tokens.py:122 | BEYOND | ∅ (added file) | <code>&quot;    exit_info = load(exit_path) if exit_path and Path(exit_path).exists() else None&quot;</code> |
| compare_tokens.py:123 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;execution&#x27;] = exit_info&quot;</code> |
| compare_tokens.py:124 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;bwrap&#x27;] = exit_info.get(&#x27;bwrap&#x27;) if exit_info else None&quot;</code> |
| compare_tokens.py:125 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;llguidance_stub&#x27;] = exit_info.get(&#x27;llguidance_stub&#x27;) if exit_info else None&quot;</code> |
| compare_tokens.py:126 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;host_dev_shm_ours&#x27;] = exit_info.get(&#x27;host_dev_shm_ours&#x27;) if exit_info else None&quot;</code> |
| compare_tokens.py:127 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;host_dev_shm_ours_before&#x27;] = exit_info.get(&#x27;host_dev_shm_ours_before&#x27;) if exit_info else None&quot;</code> |
| compare_tokens.py:128 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;stub_usage&#x27;] = exit_info.get(&#x27;stub_usage&#x27;) if exit_info else None&quot;</code> |
| compare_tokens.py:129 | BEYOND | ∅ (added file) | <code>&quot;    if report[&#x27;stub_usage&#x27;] or (report[&#x27;llguidance_stub&#x27;] and report[&#x27;llguidance_stub&#x27;].get(&#x27;enabled&#x27;)):&quot;</code> |
| compare_tokens.py:130 | BEYOND | ∅ (added file) | <code>&quot;        usage = report[&#x27;stub_usage&#x27;]&quot;</code> |
| compare_tokens.py:131 | BEYOND | ∅ (added file) | <code>&quot;        if not usage or not usage.get(&#x27;passed&#x27;):&quot;</code> |
| compare_tokens.py:132 | BEYOND | ∅ (added file) | <code>&quot;            errors.extend(usage.get(&#x27;errors&#x27;, [&#x27;llguidance audit failed&#x27;]) if usage else [&#x27;Missing llguidance audit&#x27;])&quot;</code> |
| compare_tokens.py:133 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;sandbox&#x27;] = load(out/&#x27;SANDBOX.json&#x27;) if (out/&#x27;SANDBOX.json&#x27;).exists() else None&quot;</code> |
| compare_tokens.py:134 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;errors&#x27;] = errors&quot;</code> |
| compare_tokens.py:135 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;passed&#x27;] = report[&#x27;passed&#x27;] and not errors and bool(samples) and bool(exit_info and exit_info[&#x27;returncode&#x27;] == 0 and not exit_info.get(&#x27;sampler_errors&#x27;))&quot;</code> |
| compare_tokens.py:136 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;accepted_job&#x27;] = 169526&quot;</code> |
| compare_tokens.py:137 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;accepted_source&#x27;] = str(reference_path)&quot;</code> |
| compare_tokens.py:138 | BEYOND | ∅ (added file) | <code>&quot;    report[&#x27;first_divergence_note&#x27;] = &#x27;Zero-based; a pure length difference diverges at the shorter length. Null also means tokens were unavailable; consult present and lengths.&#x27;&quot;</code> |
| compare_tokens.py:139 | BEYOND | ∅ (added file) | <code>&quot;    out.mkdir(parents=True, exist_ok=True)&quot;</code> |
| compare_tokens.py:140 | BEYOND | ∅ (added file) | <code>&quot;    (out/&#x27;PROOF.json&#x27;).write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+&#x27;\\n&#x27;)&quot;</code> |
| compare_tokens.py:141 | BEYOND | ∅ (added file) | <code>&quot;    text = [&#x27;Token proof passed: &#x27;+str(report[&#x27;passed&#x27;])+&#x27;.&#x27;, &#x27;&#x27;,&quot;</code> |
| compare_tokens.py:142 | BEYOND | ∅ (added file) | <code>&quot;            &#x27;Peak sampled card memory (MiB): &#x27;+str(report[&#x27;peak_card_memory_mib&#x27;])+&#x27;.&#x27;, &#x27;&#x27;,&quot;</code> |
| compare_tokens.py:143 | BEYOND | ∅ (added file) | <code>&quot;            &#x27;| Arm | Identical token arrays | Mean actual score | Mean accepted score |&#x27;,&quot;</code> |
| compare_tokens.py:144 | BEYOND | ∅ (added file) | <code>&quot;            &#x27;|---|---:|---:|---:|&#x27;]&quot;</code> |
| compare_tokens.py:145 | BEYOND | ∅ (added file) | <code>&quot;    for arm,a in report[&#x27;arms&#x27;].items():&quot;</code> |
| compare_tokens.py:146 | BEYOND | ∅ (added file) | <code>&quot;        text.append(&#x27;| {} | {}/{} | {} | {} |&#x27;.format(arm,a[&#x27;identical_items&#x27;],len(reference[&#x27;ids&#x27;]),a[&#x27;mean_score_actual&#x27;],a[&#x27;mean_score_accepted&#x27;]))&quot;</code> |
| compare_tokens.py:147 | BEYOND | ∅ (added file) | <code>&quot;    text += [&#x27;&#x27;, &#x27;Per-item comparison (zero-based divergence; no numerical rounding):&#x27;, &#x27;&#x27;,&quot;</code> |
| compare_tokens.py:148 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;| Arm | ID | Tokens equal | First divergence | Accepted length | Actual length | Raw equal | Answer equal | Score equal | Seconds | Tokens/s |&#x27;,&quot;</code> |
| compare_tokens.py:149 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;|---|---|---|---|---|---|---|---|---|---|---|&#x27;]&quot;</code> |
| compare_tokens.py:150 | BEYOND | ∅ (added file) | <code>&quot;    for arm,a in report[&#x27;arms&#x27;].items():&quot;</code> |
| compare_tokens.py:151 | BEYOND | ∅ (added file) | <code>&quot;        times = {r[&#x27;example_id&#x27;]:r for r in a[&#x27;timing&#x27;][&#x27;items&#x27;]}&quot;</code> |
| compare_tokens.py:152 | BEYOND | ∅ (added file) | <code>&quot;        for r in a[&#x27;items&#x27;]:&quot;</code> |
| compare_tokens.py:153 | BEYOND | ∅ (added file) | <code>&quot;            t = times[r[&#x27;example_id&#x27;]]&quot;</code> |
| compare_tokens.py:154 | BEYOND | ∅ (added file) | <code>&quot;            values = [arm,r[&#x27;example_id&#x27;],r[&#x27;token_ids_identical&#x27;],r[&#x27;first_divergence_index&#x27;],r[&#x27;accepted_length&#x27;],r[&#x27;actual_length&#x27;],&quot;</code> |
| compare_tokens.py:155 | BEYOND | ∅ (added file) | <code>&quot;                      r[&#x27;raw_generation_equal&#x27;],r[&#x27;extracted_answer_equal&#x27;],r[&#x27;score_equal&#x27;],t[&#x27;seconds&#x27;],t[&#x27;generated_tokens_per_second&#x27;]]&quot;</code> |
| compare_tokens.py:156 | BEYOND | ∅ (added file) | <code>&quot;            text.append(&#x27;| &#x27;+&#x27; | &#x27;.join(str(v) for v in values)+&#x27; |&#x27;)&quot;</code> |
| compare_tokens.py:157 | BEYOND | ∅ (added file) | <code>&quot;    text += [&#x27;&#x27;, &#x27;llguidance audit: &#x27;+json.dumps(report[&#x27;stub_usage&#x27;], sort_keys=True), &#x27;Failure reasons: &#x27;+json.dumps(errors), &#x27;&#x27;, report[&#x27;memory_note&#x27;], &#x27;&#x27;, &#x27;Timing uses worker journals and budget receipts. Reused rows have no new budget latency. Missing values remain null. Concurrent request latency is not wall-clock throughput.&#x27;, &#x27;&#x27;]&quot;</code> |
| compare_tokens.py:158 | BEYOND | ∅ (added file) | <code>&quot;    (out/&#x27;PROOF.md&#x27;).write_text(&#x27;\\n&#x27;.join(text))&quot;</code> |
| compare_tokens.py:159 | BEYOND | ∅ (added file) | <code>&quot;    return report&quot;</code> |
| compare_tokens.py:160 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:161 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:162 | BEYOND | ∅ (added file) | <code>&quot;def write_repeated(root, token, out, failure=None):&quot;</code> |
| compare_tokens.py:163 | BEYOND | ∅ (added file) | <code>&quot;    \&quot;\&quot;\&quot;Compare completed phase-B packets without rerunning a failed execution.\&quot;\&quot;\&quot;&quot;</code> |
| compare_tokens.py:164 | BEYOND | ∅ (added file) | <code>&quot;    from trinity_read import dump&quot;</code> |
| compare_tokens.py:165 | BEYOND | ∅ (added file) | <code>&quot;    paths = [Path(root)/&#x27;runs&#x27;/(token+&#x27;_r&#x27;+str(i)) for i in (1, 2)]&quot;</code> |
| compare_tokens.py:166 | BEYOND | ∅ (added file) | <code>&quot;    proofs = [load(p/&#x27;PROOF.json&#x27;) if (p/&#x27;PROOF.json&#x27;).exists() else None for p in paths]&quot;</code> |
| compare_tokens.py:167 | BEYOND | ∅ (added file) | <code>&quot;    errors = [failure] if failure else []&quot;</code> |
| compare_tokens.py:168 | BEYOND | ∅ (added file) | <code>&quot;    ids = []&quot;</code> |
| compare_tokens.py:169 | BEYOND | ∅ (added file) | <code>&quot;    for proof in proofs:&quot;</code> |
| compare_tokens.py:170 | BEYOND | ∅ (added file) | <code>&quot;        if proof:&quot;</code> |
| compare_tokens.py:171 | BEYOND | ∅ (added file) | <code>&quot;            ids = [r[&#x27;example_id&#x27;] for r in proof[&#x27;arms&#x27;][&#x27;ON16k&#x27;][&#x27;items&#x27;]]&quot;</code> |
| compare_tokens.py:172 | BEYOND | ∅ (added file) | <code>&quot;            break&quot;</code> |
| compare_tokens.py:173 | BEYOND | ∅ (added file) | <code>&quot;    arms = {}; passed = bool(ids)&quot;</code> |
| compare_tokens.py:174 | BEYOND | ∅ (added file) | <code>&quot;    for arm, rel in ARMS.items():&quot;</code> |
| compare_tokens.py:175 | BEYOND | ∅ (added file) | <code>&quot;        data = []&quot;</code> |
| compare_tokens.py:176 | BEYOND | ∅ (added file) | <code>&quot;        for path in paths:&quot;</code> |
| compare_tokens.py:177 | BEYOND | ∅ (added file) | <code>&quot;            try: data.append(unique(rows(path/&#x27;b0/d0/results&#x27;/rel/&#x27;items_b0.jsonl&#x27;)))&quot;</code> |
| compare_tokens.py:178 | BEYOND | ∅ (added file) | <code>&quot;            except (ValueError, KeyError, OSError) as error:&quot;</code> |
| compare_tokens.py:179 | BEYOND | ∅ (added file) | <code>&quot;                errors.append(str(error)); data.append({})&quot;</code> |
| compare_tokens.py:180 | BEYOND | ∅ (added file) | <code>&quot;        left, right = data&quot;</code> |
| compare_tokens.py:181 | BEYOND | ∅ (added file) | <code>&quot;        checks = [compare_row(left.get(key, dict(example_id=key)), right.get(key)) for key in ids]&quot;</code> |
| compare_tokens.py:182 | BEYOND | ∅ (added file) | <code>&quot;        complete = bool(ids) and set(left) == set(right) == set(ids)&quot;</code> |
| compare_tokens.py:183 | BEYOND | ∅ (added file) | <code>&quot;        tokens = complete and all(c[&#x27;token_ids_identical&#x27;] for c in checks)&quot;</code> |
| compare_tokens.py:184 | BEYOND | ∅ (added file) | <code>&quot;        answers = complete and all(c[&#x27;extracted_answer_equal&#x27;] for c in checks)&quot;</code> |
| compare_tokens.py:185 | BEYOND | ∅ (added file) | <code>&quot;        scores = complete and all(c[&#x27;score_equal&#x27;] for c in checks)&quot;</code> |
| compare_tokens.py:186 | BEYOND | ∅ (added file) | <code>&quot;        raw = complete and all(c[&#x27;raw_generation_equal&#x27;] for c in checks)&quot;</code> |
| compare_tokens.py:187 | BEYOND | ∅ (added file) | <code>&quot;        arms[arm] = dict(items=checks, membership_equal=complete, token_ids_equal=tokens,&quot;</code> |
| compare_tokens.py:188 | BEYOND | ∅ (added file) | <code>&quot;                         answers_equal=answers, scores_equal=scores, raw_generation_equal=raw)&quot;</code> |
| compare_tokens.py:189 | BEYOND | ∅ (added file) | <code>&quot;        passed = passed and tokens and answers and scores and raw&quot;</code> |
| compare_tokens.py:190 | BEYOND | ∅ (added file) | <code>&quot;    comparison = dict(passed=bool(passed and not errors), runs=[str(p) for p in paths], arms=arms, errors=errors,&quot;</code> |
| compare_tokens.py:191 | BEYOND | ∅ (added file) | <code>&quot;                      labels=dict(accepted=&#x27;run1&#x27;, actual=&#x27;run2&#x27;),&quot;</code> |
| compare_tokens.py:192 | BEYOND | ∅ (added file) | <code>&quot;                      first_divergence_note=&#x27;Zero-based; missing arrays cannot pass, even if both runs are missing.&#x27;)&quot;</code> |
| compare_tokens.py:193 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;RUN_TO_RUN.json&#x27;, comparison)&quot;</code> |
| compare_tokens.py:194 | BEYOND | ∅ (added file) | <code>&quot;    summary = dict(passed=comparison[&#x27;passed&#x27;] and all(p and p[&#x27;passed&#x27;] for p in proofs),&quot;</code> |
| compare_tokens.py:195 | BEYOND | ∅ (added file) | <code>&quot;                   runs=[dict(path=str(path), vs_accepted=proof) for path, proof in zip(paths, proofs)],&quot;</code> |
| compare_tokens.py:196 | BEYOND | ∅ (added file) | <code>&quot;                   run_to_run=comparison)&quot;</code> |
| compare_tokens.py:197 | BEYOND | ∅ (added file) | <code>&quot;    dump(out/&#x27;PROOF.json&#x27;, summary)&quot;</code> |
| compare_tokens.py:198 | BEYOND | ∅ (added file) | <code>&quot;    text = [&#x27;Repeated token proof passed: &#x27;+str(summary[&#x27;passed&#x27;])+&#x27;.&#x27;, &#x27;&#x27;,&quot;</code> |
| compare_tokens.py:199 | BEYOND | ∅ (added file) | <code>&quot;            &#x27;| Comparison | ON16k tokens | B2048 tokens | B4096 tokens | Passed |&#x27;,&quot;</code> |
| compare_tokens.py:200 | BEYOND | ∅ (added file) | <code>&quot;            &#x27;|---|---|---|---|---|&#x27;]&quot;</code> |
| compare_tokens.py:201 | BEYOND | ∅ (added file) | <code>&quot;    for i, proof in enumerate(proofs, 1):&quot;</code> |
| compare_tokens.py:202 | BEYOND | ∅ (added file) | <code>&quot;        counts = [str(proof[&#x27;arms&#x27;][arm][&#x27;identical_items&#x27;])+&#x27;/&#x27;+str(proof[&#x27;items&#x27;]) if proof else &#x27;not executed/completed&#x27; for arm in ARMS]&quot;</code> |
| compare_tokens.py:203 | BEYOND | ∅ (added file) | <code>&quot;        text.append(&#x27;| Run {} vs accepted | {} | {} |&#x27;.format(i, &#x27; | &#x27;.join(counts), bool(proof and proof[&#x27;passed&#x27;])))&quot;</code> |
| compare_tokens.py:204 | BEYOND | ∅ (added file) | <code>&quot;    text.append(&#x27;| Run 1 vs run 2 | {} | {} |&#x27;.format(&#x27; | &#x27;.join(str(arms[arm][&#x27;token_ids_equal&#x27;]) for arm in ARMS), comparison[&#x27;passed&#x27;]))&quot;</code> |
| compare_tokens.py:205 | BEYOND | ∅ (added file) | <code>&quot;    text += [&#x27;&#x27;, &#x27;| Arm | Answers equal between runs | Scores equal between runs |&#x27;, &#x27;|---|---|---|&#x27;]&quot;</code> |
| compare_tokens.py:206 | BEYOND | ∅ (added file) | <code>&quot;    for arm in ARMS: text.append(&#x27;| {} | {} | {} |&#x27;.format(arm, arms[arm][&#x27;answers_equal&#x27;], arms[arm][&#x27;scores_equal&#x27;]))&quot;</code> |
| compare_tokens.py:207 | BEYOND | ∅ (added file) | <code>&quot;    text += [&#x27;&#x27;, &#x27;Per-item arrays and first divergence are in RUN_TO_RUN.json. Each run retains its full accepted comparison and sandbox receipt.&#x27;,&quot;</code> |
| compare_tokens.py:208 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;Failure reasons: &#x27;+json.dumps(errors), &#x27;&#x27;]&quot;</code> |
| compare_tokens.py:209 | BEYOND | ∅ (added file) | <code>&quot;    (out/&#x27;PROOF.md&#x27;).write_text(&#x27;\\n&#x27;.join(text))&quot;</code> |
| compare_tokens.py:210 | BEYOND | ∅ (added file) | <code>&quot;    return summary&quot;</code> |
| compare_tokens.py:211 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:212 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| compare_tokens.py:213 | BEYOND | ∅ (added file) | <code>&quot;if __name__ == &#x27;__main__&#x27;:&quot;</code> |
| compare_tokens.py:214 | BEYOND | ∅ (added file) | <code>&quot;    p = argparse.ArgumentParser(description=__doc__)&quot;</code> |
| compare_tokens.py:215 | BEYOND | ∅ (added file) | <code>&quot;    for name in (&#x27;reference&#x27;,&#x27;dest&#x27;,&#x27;attempt&#x27;,&#x27;out&#x27;): p.add_argument(&#x27;--&#x27;+name, required=True)&quot;</code> |
| compare_tokens.py:216 | BEYOND | ∅ (added file) | <code>&quot;    p.add_argument(&#x27;--memory&#x27;); p.add_argument(&#x27;--exit&#x27;, dest=&#x27;exit_path&#x27;)&quot;</code> |
| compare_tokens.py:217 | BEYOND | ∅ (added file) | <code>&quot;    a = p.parse_args()&quot;</code> |
| compare_tokens.py:218 | BEYOND | ∅ (added file) | <code>&quot;    result = write_report(a.reference,a.dest,a.attempt,a.out,a.memory,a.exit_path)&quot;</code> |
| compare_tokens.py:219 | BEYOND | ∅ (added file) | <code>&quot;    raise SystemExit(0 if result[&#x27;passed&#x27;] else 1)&quot;</code> |
| tests/conftest.py:1 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/conftest.py:2 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/conftest.py:3 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/conftest.py:4 | BEYOND | ∅ (added file) | <code>&quot;sys.dont_write_bytecode = True&quot;</code> |
| tests/conftest.py:5 | BEYOND | ∅ (added file) | <code>&quot;sys.path.insert(0, str(Path(__file__).resolve().parents[1]))&quot;</code> |
| tests/test_runner.py:1 | BEYOND | ∅ (added file) | <code>&quot;import copy&quot;</code> |
| tests/test_runner.py:2 | BEYOND | ∅ (added file) | <code>&quot;import gzip&quot;</code> |
| tests/test_runner.py:3 | BEYOND | ∅ (added file) | <code>&quot;import hashlib&quot;</code> |
| tests/test_runner.py:4 | BEYOND | ∅ (added file) | <code>&quot;import io&quot;</code> |
| tests/test_runner.py:5 | BEYOND | ∅ (added file) | <code>&quot;import json&quot;</code> |
| tests/test_runner.py:6 | BEYOND | ∅ (added file) | <code>&quot;import os&quot;</code> |
| tests/test_runner.py:7 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/test_runner.py:8 | BEYOND | ∅ (added file) | <code>&quot;import subprocess&quot;</code> |
| tests/test_runner.py:9 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/test_runner.py:10 | BEYOND | ∅ (added file) | <code>&quot;import tarfile&quot;</code> |
| tests/test_runner.py:11 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace as NS&quot;</code> |
| tests/test_runner.py:12 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:13 | BEYOND | ∅ (added file) | <code>&quot;import pytest&quot;</code> |
| tests/test_runner.py:14 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| tests/test_runner.py:15 | BEYOND | ∅ (added file) | <code>&quot;import compare_tokens as C&quot;</code> |
| tests/test_runner.py:16 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:17 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:18 | BEYOND | ∅ (added file) | <code>&quot;def archive(path, entries):&quot;</code> |
| tests/test_runner.py:19 | BEYOND | ∅ (added file) | <code>&quot;    with tarfile.open(path, &#x27;w&#x27;) as tf:&quot;</code> |
| tests/test_runner.py:20 | BEYOND | ∅ (added file) | <code>&quot;        for name, raw in entries:&quot;</code> |
| tests/test_runner.py:21 | BEYOND | ∅ (added file) | <code>&quot;            item = tarfile.TarInfo(name); item.size = len(raw)&quot;</code> |
| tests/test_runner.py:22 | BEYOND | ∅ (added file) | <code>&quot;            tf.addfile(item, io.BytesIO(raw))&quot;</code> |
| tests/test_runner.py:23 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:24 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:25 | BEYOND | ∅ (added file) | <code>&quot;def png(color):&quot;</code> |
| tests/test_runner.py:26 | BEYOND | ∅ (added file) | <code>&quot;    from PIL import Image&quot;</code> |
| tests/test_runner.py:27 | BEYOND | ∅ (added file) | <code>&quot;    out = io.BytesIO(); Image.new(&#x27;RGB&#x27;,(8,8),color).save(out,format=&#x27;PNG&#x27;)&quot;</code> |
| tests/test_runner.py:28 | BEYOND | ∅ (added file) | <code>&quot;    raw = out.getvalue(); h = hashlib.sha256(raw).hexdigest()&quot;</code> |
| tests/test_runner.py:29 | BEYOND | ∅ (added file) | <code>&quot;    return h, raw&quot;</code> |
| tests/test_runner.py:30 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:31 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:32 | BEYOND | ∅ (added file) | <code>&quot;def test_bootstrap_matches_accepted():&quot;</code> |
| tests/test_runner.py:33 | BEYOND | ∅ (added file) | <code>&quot;    cfg, files = T.reference_bundle()&quot;</code> |
| tests/test_runner.py:34 | BEYOND | ∅ (added file) | <code>&quot;    assert cfg[&#x27;token&#x27;] == &#x27;pb59bef09f3&#x27;&quot;</code> |
| tests/test_runner.py:35 | BEYOND | ∅ (added file) | <code>&quot;    assert hashlib.sha256(files[&#x27;bootstrap/payload.tar.gz&#x27;]).hexdigest() == cfg[&#x27;payload_sha256&#x27;]&quot;</code> |
| tests/test_runner.py:36 | BEYOND | ∅ (added file) | <code>&quot;    assert files[&#x27;bootstrap/trace_runtime.py&#x27;] == (T.KIT/&#x27;launcher/trace_runtime.py&#x27;).read_bytes()&quot;</code> |
| tests/test_runner.py:37 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:38 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:39 | BEYOND | ∅ (added file) | <code>&quot;def test_partial_stage_refused(tmp_path):&quot;</code> |
| tests/test_runner.py:40 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;STAGING.json&#x27;, {&#x27;pieces&#x27;:{&#x27;runtime_0&#x27;:{&#x27;status&#x27;:&#x27;partial&#x27;}}})&quot;</code> |
| tests/test_runner.py:41 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;Partial stage refused&#x27;):&quot;</code> |
| tests/test_runner.py:42 | BEYOND | ∅ (added file) | <code>&quot;        T.stage(tmp_path,tmp_path/&#x27;dl&#x27;)&quot;</code> |
| tests/test_runner.py:43 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:44 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:45 | BEYOND | ∅ (added file) | <code>&quot;def test_piece_idempotent_and_failure_retained(tmp_path):&quot;</code> |
| tests/test_runner.py:46 | BEYOND | ∅ (added file) | <code>&quot;    state = {&#x27;pieces&#x27;:{}}; calls = []&quot;</code> |
| tests/test_runner.py:47 | BEYOND | ∅ (added file) | <code>&quot;    T.piece(tmp_path,state,&#x27;ok&#x27;,lambda:calls.append(1))&quot;</code> |
| tests/test_runner.py:48 | BEYOND | ∅ (added file) | <code>&quot;    T.piece(tmp_path,state,&#x27;ok&#x27;,lambda:calls.append(2))&quot;</code> |
| tests/test_runner.py:49 | BEYOND | ∅ (added file) | <code>&quot;    assert calls == [1]&quot;</code> |
| tests/test_runner.py:50 | BEYOND | ∅ (added file) | <code>&quot;    def fail(): raise ValueError(&#x27;bad payload&#x27;)&quot;</code> |
| tests/test_runner.py:51 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.piece(tmp_path,state,&#x27;bad&#x27;,fail)&quot;</code> |
| tests/test_runner.py:52 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;Partial&#x27;): T.piece(tmp_path,state,&#x27;bad&#x27;,lambda:None)&quot;</code> |
| tests/test_runner.py:53 | BEYOND | ∅ (added file) | <code>&quot;    assert T.load(tmp_path/&#x27;STAGING.json&#x27;)[&#x27;pieces&#x27;][&#x27;bad&#x27;][&#x27;status&#x27;] == &#x27;partial&#x27;&quot;</code> |
| tests/test_runner.py:54 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:55 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:56 | BEYOND | ∅ (added file) | <code>&quot;def test_runtime_part_hashes(tmp_path):&quot;</code> |
| tests/test_runner.py:57 | BEYOND | ∅ (added file) | <code>&quot;    p = tmp_path/&#x27;rt.tar&#x27;; p.write_bytes(b&#x27;abcdef&#x27;)&quot;</code> |
| tests/test_runner.py:58 | BEYOND | ∅ (added file) | <code>&quot;    rows = [(&#x27;a&#x27;,3,hashlib.sha256(b&#x27;abc&#x27;).hexdigest()),(&#x27;b&#x27;,3,hashlib.sha256(b&#x27;def&#x27;).hexdigest())]&quot;</code> |
| tests/test_runner.py:59 | BEYOND | ∅ (added file) | <code>&quot;    assert T.authenticate_parts(p,rows) == hashlib.sha256(b&#x27;abcdef&#x27;).hexdigest()&quot;</code> |
| tests/test_runner.py:60 | BEYOND | ∅ (added file) | <code>&quot;    rows[1] = (&#x27;b&#x27;,3,&#x27;0&#x27;*64)&quot;</code> |
| tests/test_runner.py:61 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;SHA256&#x27;): T.authenticate_parts(p,rows)&quot;</code> |
| tests/test_runner.py:62 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:63 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:64 | BEYOND | ∅ (added file) | <code>&quot;def test_receipt_required(tmp_path):&quot;</code> |
| tests/test_runner.py:65 | BEYOND | ∅ (added file) | <code>&quot;    p = tmp_path/&#x27;a.tar&#x27;; p.write_bytes(b&#x27;abc&#x27;)&quot;</code> |
| tests/test_runner.py:66 | BEYOND | ∅ (added file) | <code>&quot;    assert not T.receipt_ready(p)&quot;</code> |
| tests/test_runner.py:67 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(str(p)+&#x27;.RECEIPT.json&#x27;,dict(bytes=3,sha256=hashlib.sha256(b&#x27;abc&#x27;).hexdigest()))&quot;</code> |
| tests/test_runner.py:68 | BEYOND | ∅ (added file) | <code>&quot;    assert T.receipt_ready(p)&quot;</code> |
| tests/test_runner.py:69 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:70 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:71 | BEYOND | ∅ (added file) | <code>&quot;def test_store_append_and_unchanged_pull(tmp_path,monkeypatch):&quot;</code> |
| tests/test_runner.py:72 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.kit_stage(),&#x27;room&#x27;,lambda *a:None)&quot;</code> |
| tests/test_runner.py:73 | BEYOND | ∅ (added file) | <code>&quot;    a,ar = png(&#x27;red&#x27;); b,br = png(&#x27;blue&#x27;)&quot;</code> |
| tests/test_runner.py:74 | BEYOND | ∅ (added file) | <code>&quot;    archive(tmp_path/&#x27;a.tar&#x27;,[(a[:2]+&#x27;/&#x27;+a+&#x27;.png&#x27;,ar)])&quot;</code> |
| tests/test_runner.py:75 | BEYOND | ∅ (added file) | <code>&quot;    archive(tmp_path/&#x27;b.tar&#x27;,[(a[:2]+&#x27;/&#x27;+a+&#x27;.png&#x27;,ar),(b[:2]+&#x27;/&#x27;+b+&#x27;.png&#x27;,br)])&quot;</code> |
| tests/test_runner.py:76 | BEYOND | ∅ (added file) | <code>&quot;    assert T.frames(tmp_path,[tmp_path/&#x27;a.tar&#x27;])[&#x27;added&#x27;] == 1&quot;</code> |
| tests/test_runner.py:77 | BEYOND | ∅ (added file) | <code>&quot;    original = (tmp_path/&#x27;k6tk/MEMBERS.tsv.gz&#x27;).read_bytes()&quot;</code> |
| tests/test_runner.py:78 | BEYOND | ∅ (added file) | <code>&quot;    original_index = T.store_index(tmp_path)&quot;</code> |
| tests/test_runner.py:79 | BEYOND | ∅ (added file) | <code>&quot;    assert T.frames(tmp_path,[tmp_path/&#x27;b.tar&#x27;])[&#x27;added&#x27;] == 1&quot;</code> |
| tests/test_runner.py:80 | BEYOND | ∅ (added file) | <code>&quot;    assert (tmp_path/&#x27;k6tk/MEMBERS.tsv.gz&#x27;).read_bytes().startswith(original)&quot;</code> |
| tests/test_runner.py:81 | BEYOND | ∅ (added file) | <code>&quot;    assert T.store_index(tmp_path)[a] == original_index[a]&quot;</code> |
| tests/test_runner.py:82 | BEYOND | ∅ (added file) | <code>&quot;    assert T.frames(tmp_path,[tmp_path/&#x27;b.tar&#x27;])[&#x27;added&#x27;] == 0&quot;</code> |
| tests/test_runner.py:83 | BEYOND | ∅ (added file) | <code>&quot;    listing = tmp_path/&#x27;NEED.txt&#x27;; listing.write_text(a+&#x27;\\n&#x27;+b+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:84 | BEYOND | ∅ (added file) | <code>&quot;    raw = subprocess.check_output([sys.executable,&#x27;-B&#x27;,str(T.KIT/&#x27;proof/pull.py&#x27;),str(listing),str(tmp_path/&#x27;k6tk&#x27;)])&quot;</code> |
| tests/test_runner.py:85 | BEYOND | ∅ (added file) | <code>&quot;    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:&quot;</code> |
| tests/test_runner.py:86 | BEYOND | ∅ (added file) | <code>&quot;        assert {hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf} == {a,b}&quot;</code> |
| tests/test_runner.py:87 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:88 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:89 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;bad_name,bad_bytes&#x27;, [(True,False),(False,True)])&quot;</code> |
| tests/test_runner.py:90 | BEYOND | ∅ (added file) | <code>&quot;def test_store_sha_refusal(tmp_path, monkeypatch, bad_name, bad_bytes):&quot;</code> |
| tests/test_runner.py:91 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.kit_stage(),&#x27;room&#x27;,lambda *a:None)&quot;</code> |
| tests/test_runner.py:92 | BEYOND | ∅ (added file) | <code>&quot;    h,raw = png(&#x27;red&#x27;)&quot;</code> |
| tests/test_runner.py:93 | BEYOND | ∅ (added file) | <code>&quot;    archive(tmp_path/&#x27;bad.tar&#x27;,[((&#x27;../&#x27; if bad_name else &#x27;&#x27;)+h[:2]+&#x27;/&#x27;+h+&#x27;.png&#x27;,raw+b&#x27;x&#x27; if bad_bytes else raw)])&quot;</code> |
| tests/test_runner.py:94 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.frames(tmp_path,[tmp_path/&#x27;bad.tar&#x27;])&quot;</code> |
| tests/test_runner.py:95 | BEYOND | ∅ (added file) | <code>&quot;    assert not (tmp_path/&#x27;k6tk/MEMBERS.tsv.gz&#x27;).exists()&quot;</code> |
| tests/test_runner.py:96 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:97 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:98 | BEYOND | ∅ (added file) | <code>&quot;def test_system_python_store(tmp_path):&quot;</code> |
| tests/test_runner.py:99 | BEYOND | ∅ (added file) | <code>&quot;    h,raw = png(&#x27;red&#x27;); archive(tmp_path/&#x27;p.tar&#x27;,[(h[:2]+&#x27;/&#x27;+h+&#x27;.png&#x27;,raw)])&quot;</code> |
| tests/test_runner.py:100 | BEYOND | ∅ (added file) | <code>&quot;    script = &#x27;import trinity_read as T; T.kit_stage().room=lambda *a:None; print(T.frames(T.Path(%r),[T.Path(%r)]))&#x27; % (str(tmp_path),str(tmp_path/&#x27;p.tar&#x27;))&quot;</code> |
| tests/test_runner.py:101 | BEYOND | ∅ (added file) | <code>&quot;    subprocess.run([&#x27;/usr/bin/python3&#x27;,&#x27;-B&#x27;,&#x27;-c&#x27;,script],cwd=T.BUILD,check=True)&quot;</code> |
| tests/test_runner.py:102 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:103 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:104 | BEYOND | ∅ (added file) | <code>&quot;def test_selection_and_need():&quot;</code> |
| tests/test_runner.py:105 | BEYOND | ∅ (added file) | <code>&quot;    tasks = [dict(benchmark=&#x27;devrows&#x27;,example_id=i,native=n) for i,n in [(&#x27;b&#x27;,&#x27;x&#x27;),(&#x27;a&#x27;,&#x27;y&#x27;),(&#x27;c&#x27;,&#x27;x&#x27;)]]&quot;</code> |
| tests/test_runner.py:106 | BEYOND | ∅ (added file) | <code>&quot;    captures = {&#x27;x&#x27;:{&#x27;frames&#x27;:[{&#x27;sha256&#x27;:&#x27;1&#x27;*64}]},&#x27;y&#x27;:{&#x27;frames&#x27;:[{&#x27;sha256&#x27;:&#x27;2&#x27;*64}]}}&quot;</code> |
| tests/test_runner.py:107 | BEYOND | ∅ (added file) | <code>&quot;    assert [t[&#x27;example_id&#x27;] for t in T.selected_tasks(tasks,ids=[&#x27;c&#x27;,&#x27;a&#x27;])] == [&#x27;a&#x27;,&#x27;c&#x27;]&quot;</code> |
| tests/test_runner.py:108 | BEYOND | ∅ (added file) | <code>&quot;    assert T.needed(captures,T.selected_tasks(tasks,first=1)) == [&#x27;2&#x27;*64]&quot;</code> |
| tests/test_runner.py:109 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;outside&#x27;): T.selected_tasks(tasks,ids=[&#x27;not-dev&#x27;])&quot;</code> |
| tests/test_runner.py:110 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;unique&#x27;): T.selected_tasks(tasks,ids=[&#x27;a&#x27;,&#x27;a&#x27;])&quot;</code> |
| tests/test_runner.py:111 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.selected_tasks(tasks,first=4)&quot;</code> |
| tests/test_runner.py:112 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.selected_tasks([dict(benchmark=&#x27;official5130&#x27;,example_id=&#x27;1&#x27;)])&quot;</code> |
| tests/test_runner.py:113 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:114 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:115 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;family&#x27;, T.FAMILIES)&quot;</code> |
| tests/test_runner.py:116 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;prefix&#x27;, [20, None])&quot;</code> |
| tests/test_runner.py:117 | BEYOND | ∅ (added file) | <code>&quot;def test_need_real_payload_with_kit_fakes(tmp_path,family,prefix):&quot;</code> |
| tests/test_runner.py:118 | BEYOND | ∅ (added file) | <code>&quot;    # A fresh process is required by origin.kit_import; fake only tensor/processor imports.&quot;</code> |
| tests/test_runner.py:119 | BEYOND | ∅ (added file) | <code>&quot;    script = &#x27;&#x27;&#x27;&quot;</code> |
| tests/test_runner.py:120 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/test_runner.py:121 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/test_runner.py:122 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| tests/test_runner.py:123 | BEYOND | ∅ (added file) | <code>&quot;sys.path.insert(0,str(T.KIT/&#x27;proof&#x27;))&quot;</code> |
| tests/test_runner.py:124 | BEYOND | ∅ (added file) | <code>&quot;import fakes&quot;</code> |
| tests/test_runner.py:125 | BEYOND | ∅ (added file) | <code>&quot;fakes.install()&quot;</code> |
| tests/test_runner.py:126 | BEYOND | ∅ (added file) | <code>&quot;import namespace_worker as W&quot;</code> |
| tests/test_runner.py:127 | BEYOND | ∅ (added file) | <code>&quot;cfg=T.load(T.REFERENCE/&#x27;CONFIG.json&#x27;)&quot;</code> |
| tests/test_runner.py:128 | BEYOND | ∅ (added file) | <code>&quot;runtime=Path(&#x27;/scratch/jjyeung/orch_n30/evalx27/work/pull/x27c/r2/sj/orch_cd&#x27;)&quot;</code> |
| tests/test_runner.py:129 | BEYOND | ∅ (added file) | <code>&quot;reader=runtime/&#x27;legs1_reads&#x27;&quot;</code> |
| tests/test_runner.py:130 | BEYOND | ∅ (added file) | <code>&quot;assert T.sha(reader/&#x27;out/direct.py&#x27;) == &#x27;d16b64b902a651f0d3989cfe3eb3dc5ea599e960ef5158e5e36a0901dcfb1f8a&#x27;&quot;</code> |
| tests/test_runner.py:131 | BEYOND | ∅ (added file) | <code>&quot;W.bind_plan(cfg,sys.argv[1],Path(sys.argv[2]),first=int(sys.argv[3]) if sys.argv[3]!=&#x27;all&#x27; else None,reader=reader,kit=runtime/&#x27;rv_merge_fix/work/r3/aws_vl64rt&#x27;)&quot;</code> |
| tests/test_runner.py:132 | BEYOND | ∅ (added file) | <code>&quot;&#x27;&#x27;&#x27;&quot;</code> |
| tests/test_runner.py:133 | BEYOND | ∅ (added file) | <code>&quot;    subprocess.run([sys.executable,&#x27;-B&#x27;,&#x27;-c&#x27;,script,family,str(tmp_path),str(prefix) if prefix else &#x27;all&#x27;],cwd=T.BUILD,check=True)&quot;</code> |
| tests/test_runner.py:134 | BEYOND | ∅ (added file) | <code>&quot;    result = T.load(tmp_path/&#x27;NEED.json&#x27;)&quot;</code> |
| tests/test_runner.py:135 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;items&#x27;] == (20 if prefix else result[&#x27;family_items&#x27;])&quot;</code> |
| tests/test_runner.py:136 | BEYOND | ∅ (added file) | <code>&quot;    assert len(result[&#x27;need&#x27;]) == len(set(result[&#x27;need&#x27;]))&quot;</code> |
| tests/test_runner.py:137 | BEYOND | ∅ (added file) | <code>&quot;    assert sum(result[&#x27;estimated_frame_bytes&#x27;].values()) &gt; 0&quot;</code> |
| tests/test_runner.py:138 | BEYOND | ∅ (added file) | <code>&quot;    if family == &#x27;main&#x27; and prefix == 20:&quot;</code> |
| tests/test_runner.py:139 | BEYOND | ∅ (added file) | <code>&quot;        reference = T.load(T.KIT/&#x27;parity/DEV20.json&#x27;)&quot;</code> |
| tests/test_runner.py:140 | BEYOND | ∅ (added file) | <code>&quot;        assert result[&#x27;ids&#x27;] == reference[&#x27;ids&#x27;]&quot;</code> |
| tests/test_runner.py:141 | BEYOND | ∅ (added file) | <code>&quot;        expected = (T.BUILD/&#x27;NEED20.fixture.txt&#x27;).read_text().splitlines()&quot;</code> |
| tests/test_runner.py:142 | BEYOND | ∅ (added file) | <code>&quot;        assert result[&#x27;need&#x27;] == sorted(expected)&quot;</code> |
| tests/test_runner.py:143 | BEYOND | ∅ (added file) | <code>&quot;        assert len(result[&#x27;need&#x27;]) == 576&quot;</code> |
| tests/test_runner.py:144 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:145 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:146 | BEYOND | ∅ (added file) | <code>&quot;def test_filter_updates_existing_and_future_imports(monkeypatch):&quot;</code> |
| tests/test_runner.py:147 | BEYOND | ∅ (added file) | <code>&quot;    import namespace_worker as W&quot;</code> |
| tests/test_runner.py:148 | BEYOND | ∅ (added file) | <code>&quot;    import types&quot;</code> |
| tests/test_runner.py:149 | BEYOND | ∅ (added file) | <code>&quot;    data = types.ModuleType(&#x27;test_data&#x27;); consumer = types.ModuleType(&#x27;test_consumer&#x27;)&quot;</code> |
| tests/test_runner.py:150 | BEYOND | ∅ (added file) | <code>&quot;    data.tasks_for = lambda *a:[dict(benchmark=&#x27;devrows&#x27;,example_id=k) for k in [&#x27;b&#x27;,&#x27;a&#x27;,&#x27;c&#x27;]]&quot;</code> |
| tests/test_runner.py:151 | BEYOND | ∅ (added file) | <code>&quot;    consumer.tasks_for = data.tasks_for&quot;</code> |
| tests/test_runner.py:152 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setitem(sys.modules,&#x27;test_data&#x27;,data); monkeypatch.setitem(sys.modules,&#x27;test_consumer&#x27;,consumer)&quot;</code> |
| tests/test_runner.py:153 | BEYOND | ∅ (added file) | <code>&quot;    W.install_filter(data,[&#x27;c&#x27;,&#x27;a&#x27;])&quot;</code> |
| tests/test_runner.py:154 | BEYOND | ∅ (added file) | <code>&quot;    assert consumer.tasks_for is data.tasks_for&quot;</code> |
| tests/test_runner.py:155 | BEYOND | ∅ (added file) | <code>&quot;    assert [r[&#x27;example_id&#x27;] for r in consumer.tasks_for({&#x27;benchmark&#x27;:&#x27;devrows&#x27;}, {})] == [&#x27;a&#x27;,&#x27;c&#x27;]&quot;</code> |
| tests/test_runner.py:156 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): consumer.tasks_for({&#x27;benchmark&#x27;:&#x27;revsi&#x27;}, {})&quot;</code> |
| tests/test_runner.py:157 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:158 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:159 | BEYOND | ∅ (added file) | <code>&quot;def record(tokens=(1,2,3)):&quot;</code> |
| tests/test_runner.py:160 | BEYOND | ∅ (added file) | <code>&quot;    return dict(example_id=&#x27;item&#x27;,token_ids=list(tokens),raw_generation=&#x27;answer&#x27;,extracted_answer=&#x27;A&#x27;,score=1.0)&quot;</code> |
| tests/test_runner.py:161 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:162 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:163 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;actual,k,equal&#x27;, [([1,2,3],None,True),([1,9,3],1,False),([1,2],2,False),([1,2,3,4],3,False)])&quot;</code> |
| tests/test_runner.py:164 | BEYOND | ∅ (added file) | <code>&quot;def test_token_comparison(actual,k,equal):&quot;</code> |
| tests/test_runner.py:165 | BEYOND | ∅ (added file) | <code>&quot;    report = C.compare_row(record(),record(actual))&quot;</code> |
| tests/test_runner.py:166 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;token_ids_identical&#x27;] is equal&quot;</code> |
| tests/test_runner.py:167 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;first_divergence_index&#x27;] == k&quot;</code> |
| tests/test_runner.py:168 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;accepted_length&#x27;] == 3 and report[&#x27;actual_length&#x27;] == len(actual)&quot;</code> |
| tests/test_runner.py:169 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:170 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:171 | BEYOND | ∅ (added file) | <code>&quot;def test_comparison_missing_and_duplicates():&quot;</code> |
| tests/test_runner.py:172 | BEYOND | ∅ (added file) | <code>&quot;    reference = dict(ids=[&#x27;item&#x27;],arms={arm:[record()] for arm in C.ARMS})&quot;</code> |
| tests/test_runner.py:173 | BEYOND | ∅ (added file) | <code>&quot;    good = {arm:[record()] for arm in C.ARMS}&quot;</code> |
| tests/test_runner.py:174 | BEYOND | ∅ (added file) | <code>&quot;    assert C.compare(reference,good)[&#x27;passed&#x27;]&quot;</code> |
| tests/test_runner.py:175 | BEYOND | ∅ (added file) | <code>&quot;    bad = copy.deepcopy(good); bad[&#x27;ON16k&#x27;] = []&quot;</code> |
| tests/test_runner.py:176 | BEYOND | ∅ (added file) | <code>&quot;    result = C.compare(reference,bad)&quot;</code> |
| tests/test_runner.py:177 | BEYOND | ∅ (added file) | <code>&quot;    assert not result[&#x27;passed&#x27;] and result[&#x27;arms&#x27;][&#x27;ON16k&#x27;][&#x27;mean_score_actual&#x27;] is None&quot;</code> |
| tests/test_runner.py:178 | BEYOND | ∅ (added file) | <code>&quot;    bad[&#x27;ON16k&#x27;] = [record(),record()]&quot;</code> |
| tests/test_runner.py:179 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;Duplicate&#x27;): C.compare(reference,bad)&quot;</code> |
| tests/test_runner.py:180 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:181 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:182 | BEYOND | ∅ (added file) | <code>&quot;def test_budget_reuse_not_counted_as_new_generation(tmp_path):&quot;</code> |
| tests/test_runner.py:183 | BEYOND | ∅ (added file) | <code>&quot;    d = tmp_path/&#x27;results/0&#x27;; d.mkdir(parents=True)&quot;</code> |
| tests/test_runner.py:184 | BEYOND | ∅ (added file) | <code>&quot;    row = dict(record(),seconds=2.0)&quot;</code> |
| tests/test_runner.py:185 | BEYOND | ∅ (added file) | <code>&quot;    (d/&#x27;g0.jsonl&#x27;).write_text(json.dumps(row)+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:186 | BEYOND | ∅ (added file) | <code>&quot;    (d/&#x27;budget_2048.g0.jsonl&#x27;).write_text(json.dumps(row)+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:187 | BEYOND | ∅ (added file) | <code>&quot;    (d/&#x27;budget_2048.g0.meta.jsonl&#x27;).write_text(json.dumps(dict(source_key=&#x27;devrows:item&#x27;,answer_cap_policy=&#x27;reuse_full_on_answer&#x27;))+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:188 | BEYOND | ∅ (added file) | <code>&quot;    assert C.timing(tmp_path,&#x27;ON16k&#x27;,[&#x27;item&#x27;])[&#x27;items&#x27;][0][&#x27;generated_tokens_per_second&#x27;] == 1.5&quot;</code> |
| tests/test_runner.py:189 | BEYOND | ∅ (added file) | <code>&quot;    assert C.timing(tmp_path,&#x27;B2048&#x27;,[&#x27;item&#x27;])[&#x27;items&#x27;][0][&#x27;seconds&#x27;] is None&quot;</code> |
| tests/test_runner.py:190 | BEYOND | ∅ (added file) | <code>&quot;    # A stopped-unclosed source also generates a continuation; forced_close alone is insufficient.&quot;</code> |
| tests/test_runner.py:191 | BEYOND | ∅ (added file) | <code>&quot;    (d/&#x27;budget_2048.g0.meta.jsonl&#x27;).write_text(json.dumps(dict(source_key=&#x27;devrows:item&#x27;,&quot;</code> |
| tests/test_runner.py:192 | BEYOND | ∅ (added file) | <code>&quot;        answer_cap_policy=&#x27;continuation_64&#x27;,stopped_unclosed=True,forced_close=False))+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:193 | BEYOND | ∅ (added file) | <code>&quot;    assert C.timing(tmp_path,&#x27;B2048&#x27;,[&#x27;item&#x27;])[&#x27;items&#x27;][0][&#x27;seconds&#x27;] == 2.0&quot;</code> |
| tests/test_runner.py:194 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:195 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:196 | BEYOND | ∅ (added file) | <code>&quot;def test_card_checks_are_mocked(monkeypatch):&quot;</code> |
| tests/test_runner.py:197 | BEYOND | ∅ (added file) | <code>&quot;    def smi(args):&quot;</code> |
| tests/test_runner.py:198 | BEYOND | ∅ (added file) | <code>&quot;        return &#x27;0, GPU-a, RTX 6000 Ada, 49140, 99\\n&#x27; if &#x27;index,uuid,name,memory.total,memory.used&#x27; in &#x27; &#x27;.join(args) else &#x27;&#x27;&quot;</code> |
| tests/test_runner.py:199 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;smi&#x27;,smi)&quot;</code> |
| tests/test_runner.py:200 | BEYOND | ∅ (added file) | <code>&quot;    assert T.check_card(&#x27;0&#x27;)[&#x27;total_mib&#x27;] == 49140&quot;</code> |
| tests/test_runner.py:201 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;smi&#x27;,lambda args:smi(args).replace(&#x27;, 99&#x27;,&#x27;, 100&#x27;))&quot;</code> |
| tests/test_runner.py:202 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.check_card(&#x27;0&#x27;)&quot;</code> |
| tests/test_runner.py:203 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:204 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:205 | BEYOND | ∅ (added file) | <code>&quot;def test_namespace_is_local_and_cpu_has_no_gpu_devices(tmp_path):&quot;</code> |
| tests/test_runner.py:206 | BEYOND | ∅ (added file) | <code>&quot;    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)&quot;</code> |
| tests/test_runner.py:207 | BEYOND | ∅ (added file) | <code>&quot;    command = T.namespace(tmp_path)&quot;</code> |
| tests/test_runner.py:208 | BEYOND | ∅ (added file) | <code>&quot;    assert &#x27;--unshare-net&#x27; in command and &#x27;--dev-bind&#x27; not in command&quot;</code> |
| tests/test_runner.py:209 | BEYOND | ∅ (added file) | <code>&quot;    assert command[command.index(T.STORE)-1] == str(tmp_path/&#x27;k6tk&#x27;)&quot;</code> |
| tests/test_runner.py:210 | BEYOND | ∅ (added file) | <code>&quot;    assert not any(&#x27;MEDIA_MANIFEST&#x27; in x for x in command)&quot;</code> |
| tests/test_runner.py:211 | BEYOND | ∅ (added file) | <code>&quot;    assert T.environment(tmp_path)[&#x27;CUDA_VISIBLE_DEVICES&#x27;] == &#x27;&#x27;&quot;</code> |
| tests/test_runner.py:212 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:213 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:214 | BEYOND | ∅ (added file) | <code>&quot;def test_missing_frames_stop_before_card(tmp_path,monkeypatch,capsys):&quot;</code> |
| tests/test_runner.py:215 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;require_stage&#x27;,lambda root:{})&quot;</code> |
| tests/test_runner.py:216 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;cpu_need&#x27;,lambda *a:dict(need=[&#x27;a&#x27;*64],ids=[&#x27;item&#x27;]))&quot;</code> |
| tests/test_runner.py:217 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;check_card&#x27;,lambda *a:pytest.fail(&#x27;GPU boundary reached&#x27;))&quot;</code> |
| tests/test_runner.py:218 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;Missing frames&#x27;):&quot;</code> |
| tests/test_runner.py:219 | BEYOND | ∅ (added file) | <code>&quot;        T.launch(NS(root=str(tmp_path),command=&#x27;proof&#x27;,token=&#x27;p12345678&#x27;))&quot;</code> |
| tests/test_runner.py:220 | BEYOND | ∅ (added file) | <code>&quot;    assert &#x27;NEED\\n&#x27; in capsys.readouterr().out&quot;</code> |
| tests/test_runner.py:221 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:222 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:223 | BEYOND | ∅ (added file) | <code>&quot;def test_lineage_and_write_boundary(tmp_path):&quot;</code> |
| tests/test_runner.py:224 | BEYOND | ∅ (added file) | <code>&quot;    logical = str(T.LINEAGE/&#x27;m544/artifact.json&#x27;)&quot;</code> |
| tests/test_runner.py:225 | BEYOND | ∅ (added file) | <code>&quot;    assert T.logical_artifact(tmp_path,str(T.physical(tmp_path,logical)),544) == logical&quot;</code> |
| tests/test_runner.py:226 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.logical_artifact(tmp_path,logical,545)&quot;</code> |
| tests/test_runner.py:227 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.writable(T.KIT/&#x27;forbidden&#x27;)&quot;</code> |
| tests/test_runner.py:228 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:229 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:230 | BEYOND | ∅ (added file) | <code>&quot;def test_stage_piecewise_and_complete(tmp_path,monkeypatch):&quot;</code> |
| tests/test_runner.py:231 | BEYOND | ∅ (added file) | <code>&quot;    root = tmp_path/&#x27;root&#x27;; dl = tmp_path/&#x27;dl&#x27;; dl.mkdir()&quot;</code> |
| tests/test_runner.py:232 | BEYOND | ∅ (added file) | <code>&quot;    assets = dict(groups=[],camera_archive={},bwrap_pin={},base_manifest={})&quot;</code> |
| tests/test_runner.py:233 | BEYOND | ∅ (added file) | <code>&quot;    manifest = json.dumps(dict(files=[dict(path=&#x27;config.json&#x27;,bytes=2,sha256=hashlib.sha256(b&#x27;{}&#x27;).hexdigest())])).encode()&quot;</code> |
| tests/test_runner.py:234 | BEYOND | ∅ (added file) | <code>&quot;    for i in range(3):&quot;</code> |
| tests/test_runner.py:235 | BEYOND | ∅ (added file) | <code>&quot;        entries = [(&#x27;sj/runtime&#x27;+str(i),b&#x27;fixture&#x27;)]&quot;</code> |
| tests/test_runner.py:236 | BEYOND | ∅ (added file) | <code>&quot;        if i == 2: entries.append((&#x27;m/ap/90da7ac2/m/base_manifest.json&#x27;,manifest))&quot;</code> |
| tests/test_runner.py:237 | BEYOND | ∅ (added file) | <code>&quot;        archive(dl/(&#x27;runtime_&#x27;+str(i)+&#x27;.tar&#x27;),entries)&quot;</code> |
| tests/test_runner.py:238 | BEYOND | ∅ (added file) | <code>&quot;        p = dl/(&#x27;runtime_&#x27;+str(i)+&#x27;.tar&#x27;)&quot;</code> |
| tests/test_runner.py:239 | BEYOND | ∅ (added file) | <code>&quot;        assets[&#x27;groups&#x27;].append([[&#x27;unused&#x27;,p.stat().st_size,T.sha(p)]])&quot;</code> |
| tests/test_runner.py:240 | BEYOND | ∅ (added file) | <code>&quot;    archive(dl/&#x27;camera.tar&#x27;,[(&#x27;sj/camera&#x27;,b&#x27;fixture&#x27;)])&quot;</code> |
| tests/test_runner.py:241 | BEYOND | ∅ (added file) | <code>&quot;    (dl/&#x27;bwrap&#x27;).write_bytes(b&#x27;fixture&#x27;)&quot;</code> |
| tests/test_runner.py:242 | BEYOND | ∅ (added file) | <code>&quot;    for key,filename in [(&#x27;camera_archive&#x27;,&#x27;camera.tar&#x27;),(&#x27;bwrap_pin&#x27;,&#x27;bwrap&#x27;)]:&quot;</code> |
| tests/test_runner.py:243 | BEYOND | ∅ (added file) | <code>&quot;        p = dl/filename; assets[key] = dict(bytes=p.stat().st_size,sha256=T.sha(p))&quot;</code> |
| tests/test_runner.py:244 | BEYOND | ∅ (added file) | <code>&quot;    archive(dl/&#x27;base.tar&#x27;,[(&#x27;a/b/c/config.json&#x27;,b&#x27;{}&#x27;)])&quot;</code> |
| tests/test_runner.py:245 | BEYOND | ∅ (added file) | <code>&quot;    assets[&#x27;base_archive_bytes&#x27;] = (dl/&#x27;base.tar&#x27;).stat().st_size&quot;</code> |
| tests/test_runner.py:246 | BEYOND | ∅ (added file) | <code>&quot;    assets[&#x27;base_manifest&#x27;] = dict(path=str(T.AP/&#x27;90da7ac2/m/base_manifest.json&#x27;),sha256=hashlib.sha256(manifest).hexdigest())&quot;</code> |
| tests/test_runner.py:247 | BEYOND | ∅ (added file) | <code>&quot;    p = tmp_path/&#x27;payload.tar&#x27;; archive(p,[(&#x27;sj/fixture/p/code.py&#x27;,b&#x27;pass\\n&#x27;)])&quot;</code> |
| tests/test_runner.py:248 | BEYOND | ∅ (added file) | <code>&quot;    config = dict(assets=assets,payload_sha256=T.sha(p))&quot;</code> |
| tests/test_runner.py:249 | BEYOND | ∅ (added file) | <code>&quot;    bootstrap = {&#x27;bootstrap/CONFIG.json&#x27;:json.dumps(config).encode(),&#x27;bootstrap/payload.tar.gz&#x27;:p.read_bytes()}&quot;</code> |
| tests/test_runner.py:250 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;reference_bundle&#x27;,lambda:(config,bootstrap))&quot;</code> |
| tests/test_runner.py:251 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;verify_export_local&#x27;,lambda *a:dict(fixture=True))&quot;</code> |
| tests/test_runner.py:252 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.kit_stage(),&#x27;room&#x27;,lambda *a:None)&quot;</code> |
| tests/test_runner.py:253 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(str(dl/&#x27;runtime_2.tar&#x27;)+&#x27;.RECEIPT.json&#x27;,{})&quot;</code> |
| tests/test_runner.py:254 | BEYOND | ∅ (added file) | <code>&quot;    initial = T.stage(root,dl)&quot;</code> |
| tests/test_runner.py:255 | BEYOND | ∅ (added file) | <code>&quot;    assert not initial[&#x27;complete&#x27;] and initial[&#x27;pieces&#x27;][&#x27;runtime_2&#x27;][&#x27;status&#x27;] == &#x27;complete&#x27;&quot;</code> |
| tests/test_runner.py:256 | BEYOND | ∅ (added file) | <code>&quot;    for p in dl.iterdir():&quot;</code> |
| tests/test_runner.py:257 | BEYOND | ∅ (added file) | <code>&quot;        if p.name.endswith(&#x27;.RECEIPT.json&#x27;): continue&quot;</code> |
| tests/test_runner.py:258 | BEYOND | ∅ (added file) | <code>&quot;        T.dump(str(p)+&#x27;.RECEIPT.json&#x27;,{})&quot;</code> |
| tests/test_runner.py:259 | BEYOND | ∅ (added file) | <code>&quot;    complete = T.stage(root,dl)&quot;</code> |
| tests/test_runner.py:260 | BEYOND | ∅ (added file) | <code>&quot;    assert complete[&#x27;complete&#x27;]&quot;</code> |
| tests/test_runner.py:261 | BEYOND | ∅ (added file) | <code>&quot;    assert (root/&#x27;m/ap/85fc3486/config.json&#x27;).read_bytes() == b&#x27;{}&#x27;&quot;</code> |
| tests/test_runner.py:262 | BEYOND | ∅ (added file) | <code>&quot;    assert T.stage(root,dl)[&#x27;pieces&#x27;] == complete[&#x27;pieces&#x27;]&quot;</code> |
| tests/test_runner.py:263 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:264 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:265 | BEYOND | ∅ (added file) | <code>&quot;def test_unregistered_stage_destination_refused(tmp_path,monkeypatch):&quot;</code> |
| tests/test_runner.py:266 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.kit_stage(),&#x27;room&#x27;,lambda *a:None)&quot;</code> |
| tests/test_runner.py:267 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;bootstrap&#x27;).mkdir()&quot;</code> |
| tests/test_runner.py:268 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError,match=&#x27;Unrecorded bootstrap&#x27;):&quot;</code> |
| tests/test_runner.py:269 | BEYOND | ∅ (added file) | <code>&quot;        T.stage(tmp_path,tmp_path/&#x27;dl&#x27;)&quot;</code> |
| tests/test_runner.py:270 | BEYOND | ∅ (added file) | <code>&quot;    assert T.load(tmp_path/&#x27;STAGING.json&#x27;)[&#x27;pieces&#x27;][&#x27;bootstrap&#x27;][&#x27;status&#x27;] == &#x27;partial&#x27;&quot;</code> |
| tests/test_runner.py:271 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:272 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:273 | BEYOND | ∅ (added file) | <code>&quot;def test_runtime_absolute_link_policy(tmp_path):&quot;</code> |
| tests/test_runner.py:274 | BEYOND | ∅ (added file) | <code>&quot;    raw = io.BytesIO()&quot;</code> |
| tests/test_runner.py:275 | BEYOND | ∅ (added file) | <code>&quot;    link = &#x27;m/ap/19252904/e/bin/python&#x27;&quot;</code> |
| tests/test_runner.py:276 | BEYOND | ∅ (added file) | <code>&quot;    target = T.kit_stage().RUNTIME_ABSOLUTE_LINKS[link]&quot;</code> |
| tests/test_runner.py:277 | BEYOND | ∅ (added file) | <code>&quot;    with tarfile.open(fileobj=raw,mode=&#x27;w&#x27;) as tf:&quot;</code> |
| tests/test_runner.py:278 | BEYOND | ∅ (added file) | <code>&quot;        m = tarfile.TarInfo(link); m.type = tarfile.SYMTYPE; m.linkname = target; tf.addfile(m)&quot;</code> |
| tests/test_runner.py:279 | BEYOND | ∅ (added file) | <code>&quot;    T.kit_stage().extract_stream(io.BytesIO(raw.getvalue()),tmp_path,None,len(raw.getvalue()),links=True)&quot;</code> |
| tests/test_runner.py:280 | BEYOND | ∅ (added file) | <code>&quot;    assert os.readlink(tmp_path/link) == target&quot;</code> |
| tests/test_runner.py:281 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:282 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:283 | BEYOND | ∅ (added file) | <code>&quot;def test_full_comparison_report(tmp_path):&quot;</code> |
| tests/test_runner.py:284 | BEYOND | ∅ (added file) | <code>&quot;    reference = dict(ids=[&#x27;item&#x27;],arms={arm:[record()] for arm in C.ARMS})&quot;</code> |
| tests/test_runner.py:285 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;reference.json&#x27;,reference)&quot;</code> |
| tests/test_runner.py:286 | BEYOND | ∅ (added file) | <code>&quot;    for arm,rel in C.ARMS.items():&quot;</code> |
| tests/test_runner.py:287 | BEYOND | ∅ (added file) | <code>&quot;        directory = tmp_path/&#x27;actual/results&#x27;/rel; directory.mkdir(parents=True)&quot;</code> |
| tests/test_runner.py:288 | BEYOND | ∅ (added file) | <code>&quot;        (directory/&#x27;items_test.jsonl&#x27;).write_text(json.dumps(record())+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:289 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;memory.jsonl&#x27;).write_text(json.dumps(dict(memory_used_mib=123.0))+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_runner.py:290 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;exit.json&#x27;,dict(returncode=0,sampler_errors=[]))&quot;</code> |
| tests/test_runner.py:291 | BEYOND | ∅ (added file) | <code>&quot;    report = C.write_report(tmp_path/&#x27;reference.json&#x27;,tmp_path/&#x27;actual&#x27;,&#x27;test&#x27;,tmp_path/&#x27;report&#x27;,tmp_path/&#x27;memory.jsonl&#x27;,tmp_path/&#x27;exit.json&#x27;)&quot;</code> |
| tests/test_runner.py:292 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;passed&#x27;] and report[&#x27;peak_card_memory_mib&#x27;] == 123.0&quot;</code> |
| tests/test_runner.py:293 | BEYOND | ∅ (added file) | <code>&quot;    assert (tmp_path/&#x27;report/PROOF.md&#x27;).is_file()&quot;</code> |
| tests/test_runner.py:294 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:295 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:296 | BEYOND | ∅ (added file) | <code>&quot;def test_corrupt_result_still_writes_failed_report(tmp_path):&quot;</code> |
| tests/test_runner.py:297 | BEYOND | ∅ (added file) | <code>&quot;    reference = dict(ids=[&#x27;item&#x27;],arms={arm:[record()] for arm in C.ARMS})&quot;</code> |
| tests/test_runner.py:298 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;reference.json&#x27;,reference)&quot;</code> |
| tests/test_runner.py:299 | BEYOND | ∅ (added file) | <code>&quot;    directory = tmp_path/&#x27;actual/results/0&#x27;; directory.mkdir(parents=True)&quot;</code> |
| tests/test_runner.py:300 | BEYOND | ∅ (added file) | <code>&quot;    (directory/&#x27;items_test.jsonl&#x27;).write_text(&#x27;{broken\\n&#x27;)&quot;</code> |
| tests/test_runner.py:301 | BEYOND | ∅ (added file) | <code>&quot;    report = C.write_report(tmp_path/&#x27;reference.json&#x27;,tmp_path/&#x27;actual&#x27;,&#x27;test&#x27;,tmp_path/&#x27;report&#x27;)&quot;</code> |
| tests/test_runner.py:302 | BEYOND | ∅ (added file) | <code>&quot;    assert not report[&#x27;passed&#x27;] and report[&#x27;errors&#x27;]&quot;</code> |
| tests/test_runner.py:303 | BEYOND | ∅ (added file) | <code>&quot;    assert (tmp_path/&#x27;report/PROOF.json&#x27;).exists()&quot;</code> |
| tests/test_runner.py:304 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:305 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_runner.py:306 | BEYOND | ∅ (added file) | <code>&quot;def test_read_space_reserves_model_copies(tmp_path,monkeypatch):&quot;</code> |
| tests/test_runner.py:307 | BEYOND | ∅ (added file) | <code>&quot;    base_path = T.AP/&#x27;manifest.json&#x27;; artifact_path = T.LINEAGE/&#x27;m544/artifact.json&#x27;&quot;</code> |
| tests/test_runner.py:308 | BEYOND | ∅ (added file) | <code>&quot;    weight_path = T.LINEAGE/&#x27;m544/full_weights/full_weights.json&#x27;&quot;</code> |
| tests/test_runner.py:309 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(T.physical(tmp_path,base_path),dict(files=[dict(bytes=100)]))&quot;</code> |
| tests/test_runner.py:310 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(T.physical(tmp_path,weight_path),dict(files=[dict(bytes=200)]))&quot;</code> |
| tests/test_runner.py:311 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(T.physical(tmp_path,artifact_path),dict(full_weights=dict(path=str(weight_path),sha256=T.sha(T.physical(tmp_path,weight_path)))))&quot;</code> |
| tests/test_runner.py:312 | BEYOND | ∅ (added file) | <code>&quot;    cfg = dict(spec=dict(models=dict(base=dict(manifest=dict(path=str(base_path),sha256=T.sha(T.physical(tmp_path,base_path))))),&quot;</code> |
| tests/test_runner.py:313 | BEYOND | ∅ (added file) | <code>&quot;                         artifact=dict(path=str(artifact_path),sha256=T.sha(T.physical(tmp_path,artifact_path)))))&quot;</code> |
| tests/test_runner.py:314 | BEYOND | ∅ (added file) | <code>&quot;    observed = []&quot;</code> |
| tests/test_runner.py:315 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.kit_stage(),&#x27;room&#x27;,lambda root,extra:observed.append(extra))&quot;</code> |
| tests/test_runner.py:316 | BEYOND | ∅ (added file) | <code>&quot;    reserve = T.read_space(tmp_path,cfg,dict(estimated_frame_bytes={&#x27;frame&#x27;:50}))&quot;</code> |
| tests/test_runner.py:317 | BEYOND | ∅ (added file) | <code>&quot;    assert reserve == 400+2*1024**3 and observed == [reserve]&quot;</code> |
| tests/test_followup.py:1 | BEYOND | ∅ (added file) | <code>&quot;import copy&quot;</code> |
| tests/test_followup.py:2 | BEYOND | ∅ (added file) | <code>&quot;import os&quot;</code> |
| tests/test_followup.py:3 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/test_followup.py:4 | BEYOND | ∅ (added file) | <code>&quot;import signal&quot;</code> |
| tests/test_followup.py:5 | BEYOND | ∅ (added file) | <code>&quot;import subprocess&quot;</code> |
| tests/test_followup.py:6 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/test_followup.py:7 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace as NS&quot;</code> |
| tests/test_followup.py:8 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:9 | BEYOND | ∅ (added file) | <code>&quot;import pytest&quot;</code> |
| tests/test_followup.py:10 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| tests/test_followup.py:11 | BEYOND | ∅ (added file) | <code>&quot;import compare_tokens as C&quot;</code> |
| tests/test_followup.py:12 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:13 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:14 | BEYOND | ∅ (added file) | <code>&quot;def test_private_shm_and_all_caches(tmp_path):&quot;</code> |
| tests/test_followup.py:15 | BEYOND | ∅ (added file) | <code>&quot;    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)&quot;</code> |
| tests/test_followup.py:16 | BEYOND | ∅ (added file) | <code>&quot;    custom = tmp_path/&#x27;private/shm&#x27;&quot;</code> |
| tests/test_followup.py:17 | BEYOND | ∅ (added file) | <code>&quot;    command = T.namespace(tmp_path, gpu=True, shm=custom)&quot;</code> |
| tests/test_followup.py:18 | BEYOND | ∅ (added file) | <code>&quot;    device = command.index(&#x27;--dev-bind&#x27;)&quot;</code> |
| tests/test_followup.py:19 | BEYOND | ∅ (added file) | <code>&quot;    assert command[device:device+6] == [&#x27;--dev-bind&#x27;, &#x27;/dev&#x27;, &#x27;/dev&#x27;, &#x27;--bind&#x27;, str(custom), &#x27;/dev/shm&#x27;]&quot;</code> |
| tests/test_followup.py:20 | BEYOND | ∅ (added file) | <code>&quot;    assert custom.is_dir()&quot;</code> |
| tests/test_followup.py:21 | BEYOND | ∅ (added file) | <code>&quot;    assert str(T.KIT) not in command and str(T.BUILD) not in command&quot;</code> |
| tests/test_followup.py:22 | BEYOND | ∅ (added file) | <code>&quot;    assert str(tmp_path/&#x27;trinity_runner&#x27;) in command&quot;</code> |
| tests/test_followup.py:23 | BEYOND | ∅ (added file) | <code>&quot;    env = T.environment(tmp_path, &#x27;0&#x27;, &#x27;p12345678&#x27;, custom)&quot;</code> |
| tests/test_followup.py:24 | BEYOND | ∅ (added file) | <code>&quot;    for key in (&#x27;TMPDIR&#x27;, &#x27;HOME&#x27;, &#x27;XDG_CACHE_HOME&#x27;, &#x27;HF_HOME&#x27;, &#x27;TRITON_CACHE_DIR&#x27;, &#x27;TORCHINDUCTOR_CACHE_DIR&#x27;, &#x27;VLLM_CACHE_ROOT&#x27;):&quot;</code> |
| tests/test_followup.py:25 | BEYOND | ∅ (added file) | <code>&quot;        assert T.inside(Path(env[key]), tmp_path) and Path(env[key]).is_dir()&quot;</code> |
| tests/test_followup.py:26 | BEYOND | ∅ (added file) | <code>&quot;    assert env[&#x27;CUDA_VISIBLE_DEVICES&#x27;] == &#x27;0&#x27;&quot;</code> |
| tests/test_followup.py:27 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:28 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:29 | BEYOND | ∅ (added file) | <code>&quot;def test_host_shm_is_shallow_and_does_not_follow_links(tmp_path):&quot;</code> |
| tests/test_followup.py:30 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;sub&#x27;).mkdir(); (tmp_path/&#x27;sub/hidden&#x27;).write_bytes(b&#x27;abc&#x27;)&quot;</code> |
| tests/test_followup.py:31 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;link&#x27;).symlink_to(tmp_path/&#x27;sub/hidden&#x27;)&quot;</code> |
| tests/test_followup.py:32 | BEYOND | ∅ (added file) | <code>&quot;    rows = T.host_shm_ours(tmp_path)&quot;</code> |
| tests/test_followup.py:33 | BEYOND | ∅ (added file) | <code>&quot;    assert {Path(r[&#x27;path&#x27;]).name for r in rows} == {&#x27;sub&#x27;, &#x27;link&#x27;}&quot;</code> |
| tests/test_followup.py:34 | BEYOND | ∅ (added file) | <code>&quot;    assert all(r[&#x27;bytes&#x27;] &gt;= 0 for r in rows)&quot;</code> |
| tests/test_followup.py:35 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:36 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:37 | BEYOND | ∅ (added file) | <code>&quot;def test_host_shm_filters_uid(tmp_path, monkeypatch):&quot;</code> |
| tests/test_followup.py:38 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;file&#x27;).write_bytes(b&#x27;a&#x27;)&quot;</code> |
| tests/test_followup.py:39 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.os, &#x27;getuid&#x27;, lambda: -1)&quot;</code> |
| tests/test_followup.py:40 | BEYOND | ∅ (added file) | <code>&quot;    assert T.host_shm_ours(tmp_path) == []&quot;</code> |
| tests/test_followup.py:41 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:42 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:43 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;pattern&#x27;, [&#x27;/data3/x/*.stop&#x27;, &#x27;/home/user/stop&#x27;, &#x27;/tmp/*/*.stop&#x27;, &#x27;**/*.stop&#x27;])&quot;</code> |
| tests/test_followup.py:44 | BEYOND | ∅ (added file) | <code>&quot;def test_yield_glob_rejects_shared_or_recursive_search(pattern):&quot;</code> |
| tests/test_followup.py:45 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.yield_pattern(pattern)&quot;</code> |
| tests/test_followup.py:46 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:47 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:48 | BEYOND | ∅ (added file) | <code>&quot;def test_yield_glob_local(tmp_path):&quot;</code> |
| tests/test_followup.py:49 | BEYOND | ∅ (added file) | <code>&quot;    assert T.yield_pattern(str(tmp_path/&#x27;*.stop&#x27;)) == str(tmp_path/&#x27;*.stop&#x27;)&quot;</code> |
| tests/test_followup.py:50 | BEYOND | ∅ (added file) | <code>&quot;    assert T.yield_pattern(None) is None&quot;</code> |
| tests/test_followup.py:51 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:52 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:53 | BEYOND | ∅ (added file) | <code>&quot;def test_process_group_escalation_only_targets_child(monkeypatch):&quot;</code> |
| tests/test_followup.py:54 | BEYOND | ∅ (added file) | <code>&quot;    signals = []; waited = []&quot;</code> |
| tests/test_followup.py:55 | BEYOND | ∅ (added file) | <code>&quot;    child = NS(pid=os.getpgrp()+100000, wait=lambda: waited.append(True) or -9)&quot;</code> |
| tests/test_followup.py:56 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.os, &#x27;killpg&#x27;, lambda group, sig: signals.append((group, sig)))&quot;</code> |
| tests/test_followup.py:57 | BEYOND | ∅ (added file) | <code>&quot;    assert T.stop_group(child, grace=0) == -9&quot;</code> |
| tests/test_followup.py:58 | BEYOND | ∅ (added file) | <code>&quot;    assert signals == [(child.pid, signal.SIGTERM), (child.pid, signal.SIGKILL)]&quot;</code> |
| tests/test_followup.py:59 | BEYOND | ∅ (added file) | <code>&quot;    assert waited == [True]&quot;</code> |
| tests/test_followup.py:60 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(RuntimeError): T.stop_group(NS(pid=os.getpgrp()), grace=0)&quot;</code> |
| tests/test_followup.py:61 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:62 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:63 | BEYOND | ∅ (added file) | <code>&quot;def test_process_group_grace_waits_even_if_leader_exits(monkeypatch):&quot;</code> |
| tests/test_followup.py:64 | BEYOND | ∅ (added file) | <code>&quot;    events = []&quot;</code> |
| tests/test_followup.py:65 | BEYOND | ∅ (added file) | <code>&quot;    child = NS(pid=os.getpgrp()+100000, wait=lambda: events.append(&#x27;reap&#x27;) or 0)&quot;</code> |
| tests/test_followup.py:66 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.time, &#x27;sleep&#x27;, lambda seconds: events.append((&#x27;wait&#x27;, seconds)))&quot;</code> |
| tests/test_followup.py:67 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.os, &#x27;killpg&#x27;, lambda group, sig: events.append(sig))&quot;</code> |
| tests/test_followup.py:68 | BEYOND | ∅ (added file) | <code>&quot;    T.stop_group(child)&quot;</code> |
| tests/test_followup.py:69 | BEYOND | ∅ (added file) | <code>&quot;    assert events == [signal.SIGTERM, (&#x27;wait&#x27;, 60), signal.SIGKILL, &#x27;reap&#x27;]&quot;</code> |
| tests/test_followup.py:70 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:71 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:72 | BEYOND | ∅ (added file) | <code>&quot;def test_reader_polls_30_seconds_and_yields(tmp_path, monkeypatch):&quot;</code> |
| tests/test_followup.py:73 | BEYOND | ∅ (added file) | <code>&quot;    flag = tmp_path/&#x27;please.stop&#x27;; waits = []; launches = []; stopped = []&quot;</code> |
| tests/test_followup.py:74 | BEYOND | ∅ (added file) | <code>&quot;    class Child:&quot;</code> |
| tests/test_followup.py:75 | BEYOND | ∅ (added file) | <code>&quot;        pid = 1234567&quot;</code> |
| tests/test_followup.py:76 | BEYOND | ∅ (added file) | <code>&quot;        def wait(self, timeout=None):&quot;</code> |
| tests/test_followup.py:77 | BEYOND | ∅ (added file) | <code>&quot;            waits.append(timeout); flag.write_text(&#x27;yield&#x27;)&quot;</code> |
| tests/test_followup.py:78 | BEYOND | ∅ (added file) | <code>&quot;            raise subprocess.TimeoutExpired(&#x27;fixture&#x27;, timeout)&quot;</code> |
| tests/test_followup.py:79 | BEYOND | ∅ (added file) | <code>&quot;    def popen(*args, **kwargs):&quot;</code> |
| tests/test_followup.py:80 | BEYOND | ∅ (added file) | <code>&quot;        launches.append(kwargs); return Child()&quot;</code> |
| tests/test_followup.py:81 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;Popen&#x27;, popen)&quot;</code> |
| tests/test_followup.py:82 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;stop_group&#x27;, lambda child: stopped.append(child.pid))&quot;</code> |
| tests/test_followup.py:83 | BEYOND | ∅ (added file) | <code>&quot;    code, event = T.run_reader([&#x27;fixture&#x27;], {}, tmp_path, None, str(tmp_path/&#x27;*.stop&#x27;))&quot;</code> |
| tests/test_followup.py:84 | BEYOND | ∅ (added file) | <code>&quot;    assert code != 0 and event[&#x27;matched_file&#x27;] == str(flag)&quot;</code> |
| tests/test_followup.py:85 | BEYOND | ∅ (added file) | <code>&quot;    assert event[&#x27;utc&#x27;].endswith(&#x27;Z&#x27;) and event[&#x27;time&#x27;] &gt; 0&quot;</code> |
| tests/test_followup.py:86 | BEYOND | ∅ (added file) | <code>&quot;    assert waits == [30] and stopped == [Child.pid]&quot;</code> |
| tests/test_followup.py:87 | BEYOND | ∅ (added file) | <code>&quot;    assert launches[0][&#x27;start_new_session&#x27;] is True&quot;</code> |
| tests/test_followup.py:88 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:89 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:90 | BEYOND | ∅ (added file) | <code>&quot;def test_reader_normal_cpu_child(tmp_path):&quot;</code> |
| tests/test_followup.py:91 | BEYOND | ∅ (added file) | <code>&quot;    with (tmp_path/&#x27;log&#x27;).open(&#x27;wb&#x27;) as log:&quot;</code> |
| tests/test_followup.py:92 | BEYOND | ∅ (added file) | <code>&quot;        code, event = T.run_reader([sys.executable, &#x27;-B&#x27;, &#x27;-c&#x27;, &#x27;print(\&quot;ok\&quot;)&#x27;], {}, tmp_path, log)&quot;</code> |
| tests/test_followup.py:93 | BEYOND | ∅ (added file) | <code>&quot;    assert code == 0 and event is None and (tmp_path/&#x27;log&#x27;).read_text() == &#x27;ok\\n&#x27;&quot;</code> |
| tests/test_followup.py:94 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:95 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:96 | BEYOND | ∅ (added file) | <code>&quot;def test_disk_inventory_never_follows_symlinks(tmp_path):&quot;</code> |
| tests/test_followup.py:97 | BEYOND | ∅ (added file) | <code>&quot;    out = tmp_path/&#x27;run&#x27;; (out/&#x27;direct/main/models/base&#x27;).mkdir(parents=True)&quot;</code> |
| tests/test_followup.py:98 | BEYOND | ∅ (added file) | <code>&quot;    model = out/&#x27;direct/main/models/base/weights&#x27;; model.write_bytes(b&#x27;12345&#x27;)&quot;</code> |
| tests/test_followup.py:99 | BEYOND | ∅ (added file) | <code>&quot;    (out/&#x27;link&#x27;).symlink_to(tmp_path, target_is_directory=True)&quot;</code> |
| tests/test_followup.py:100 | BEYOND | ∅ (added file) | <code>&quot;    rows = T.disk_listing(out)&quot;</code> |
| tests/test_followup.py:101 | BEYOND | ∅ (added file) | <code>&quot;    assert next(r for r in rows if r[&#x27;path&#x27;] == str(model))[&#x27;bytes&#x27;] == 5&quot;</code> |
| tests/test_followup.py:102 | BEYOND | ∅ (added file) | <code>&quot;    assert next(r for r in rows if r[&#x27;path&#x27;] == str(out/&#x27;link&#x27;))[&#x27;kind&#x27;] == &#x27;symlink&#x27;&quot;</code> |
| tests/test_followup.py:103 | BEYOND | ∅ (added file) | <code>&quot;    assert len(rows) == 6&quot;</code> |
| tests/test_followup.py:104 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:105 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:106 | BEYOND | ∅ (added file) | <code>&quot;def test_cheap_hash_checks_small_files_and_large_sizes(tmp_path):&quot;</code> |
| tests/test_followup.py:107 | BEYOND | ∅ (added file) | <code>&quot;    small = tmp_path/&#x27;small&#x27;; small.write_bytes(b&#x27;abc&#x27;)&quot;</code> |
| tests/test_followup.py:108 | BEYOND | ∅ (added file) | <code>&quot;    big = tmp_path/&#x27;large&#x27;; big.write_bytes(b&#x27;x&#x27;*(T.SMALL_FILE_BYTES+1))&quot;</code> |
| tests/test_followup.py:109 | BEYOND | ∅ (added file) | <code>&quot;    rows = {p.name: dict(bytes=p.stat().st_size, sha256=T.sha(p)) for p in (small,big)}&quot;</code> |
| tests/test_followup.py:110 | BEYOND | ∅ (added file) | <code>&quot;    good = T.cheap_verify(tmp_path, rows)&quot;</code> |
| tests/test_followup.py:111 | BEYOND | ∅ (added file) | <code>&quot;    assert good == dict(files=2, hashed=1, size_only=1, errors=[])&quot;</code> |
| tests/test_followup.py:112 | BEYOND | ∅ (added file) | <code>&quot;    small.write_bytes(b&#x27;xyz&#x27;); big.write_bytes(b&#x27;x&#x27;)&quot;</code> |
| tests/test_followup.py:113 | BEYOND | ∅ (added file) | <code>&quot;    bad = T.cheap_verify(tmp_path, rows)&quot;</code> |
| tests/test_followup.py:114 | BEYOND | ∅ (added file) | <code>&quot;    assert len(bad[&#x27;errors&#x27;]) == 2&quot;</code> |
| tests/test_followup.py:115 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:116 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:117 | BEYOND | ∅ (added file) | <code>&quot;def test_cheap_verify_refuses_escape(tmp_path):&quot;</code> |
| tests/test_followup.py:118 | BEYOND | ∅ (added file) | <code>&quot;    assert T.cheap_verify(tmp_path, {&#x27;../escape&#x27;: dict(bytes=0, sha256=&#x27;0&#x27;*64)})[&#x27;errors&#x27;]&quot;</code> |
| tests/test_followup.py:119 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:120 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:121 | BEYOND | ∅ (added file) | <code>&quot;def test_config_audit_exposes_pinned_host_and_external_paths(tmp_path):&quot;</code> |
| tests/test_followup.py:122 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;bootstrap/CONFIG.json&#x27;, dict(assets=dict(observed_host=&#x27;orchard-login-001&#x27;, archive=&#x27;/project/legacy.tar&#x27;),&quot;</code> |
| tests/test_followup.py:123 | BEYOND | ∅ (added file) | <code>&quot;                                                local=str(tmp_path/&#x27;cache&#x27;), logical=str(T.AP/&#x27;model&#x27;), system=&#x27;/usr/bin/python3&#x27;))&quot;</code> |
| tests/test_followup.py:124 | BEYOND | ∅ (added file) | <code>&quot;    audit = T.config_audit(tmp_path)&quot;</code> |
| tests/test_followup.py:125 | BEYOND | ∅ (added file) | <code>&quot;    assert not audit[&#x27;passed&#x27;]&quot;</code> |
| tests/test_followup.py:126 | BEYOND | ∅ (added file) | <code>&quot;    assert {r[&#x27;kind&#x27;] for r in audit[&#x27;findings&#x27;]} == {&#x27;metadata&#x27;,&#x27;external_path&#x27;,&#x27;namespace_alias&#x27;,&#x27;allowed_path&#x27;}&quot;</code> |
| tests/test_followup.py:127 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:128 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:129 | BEYOND | ∅ (added file) | <code>&quot;def test_root_carries_wrapper_without_kit(tmp_path):&quot;</code> |
| tests/test_followup.py:130 | BEYOND | ∅ (added file) | <code>&quot;    T.install_runner(tmp_path)&quot;</code> |
| tests/test_followup.py:131 | BEYOND | ∅ (added file) | <code>&quot;    manifest = T.load(tmp_path/&#x27;trinity_runner/MANIFEST.json&#x27;)&quot;</code> |
| tests/test_followup.py:132 | BEYOND | ∅ (added file) | <code>&quot;    assert set(manifest) == {&#x27;trinity_read.py&#x27;,&#x27;namespace_worker.py&#x27;,&#x27;compare_tokens.py&#x27;}&quot;</code> |
| tests/test_followup.py:133 | BEYOND | ∅ (added file) | <code>&quot;    assert T.cheap_verify(tmp_path/&#x27;trinity_runner&#x27;, manifest)[&#x27;errors&#x27;] == []&quot;</code> |
| tests/test_followup.py:134 | BEYOND | ∅ (added file) | <code>&quot;    T.install_runner(tmp_path)&quot;</code> |
| tests/test_followup.py:135 | BEYOND | ∅ (added file) | <code>&quot;    result = subprocess.run([&#x27;/usr/bin/python3&#x27;,&#x27;-B&#x27;,str(tmp_path/&#x27;trinity_runner/trinity_read.py&#x27;),&#x27;selfcheck&#x27;,&#x27;--help&#x27;],&quot;</code> |
| tests/test_followup.py:136 | BEYOND | ∅ (added file) | <code>&quot;                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)&quot;</code> |
| tests/test_followup.py:137 | BEYOND | ∅ (added file) | <code>&quot;    assert result.returncode == 0&quot;</code> |
| tests/test_followup.py:138 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;trinity_runner/MANIFEST.json&#x27;, {})&quot;</code> |
| tests/test_followup.py:139 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;manifest differs&#x27;): T.install_runner(tmp_path)&quot;</code> |
| tests/test_followup.py:140 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:141 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:142 | BEYOND | ∅ (added file) | <code>&quot;def test_partial_selfcheck_reports_unverifiable_and_does_not_write(tmp_path, monkeypatch):&quot;</code> |
| tests/test_followup.py:143 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;STAGING.json&#x27;, dict(complete=False,pieces={&#x27;a0&#x27;:dict(status=&#x27;complete&#x27;,evidence=dict(sha256=&#x27;x&#x27;))}))&quot;</code> |
| tests/test_followup.py:144 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;bootstrap/CONFIG.json&#x27;, {})&quot;</code> |
| tests/test_followup.py:145 | BEYOND | ∅ (added file) | <code>&quot;    before = T.disk_listing(tmp_path)&quot;</code> |
| tests/test_followup.py:146 | BEYOND | ∅ (added file) | <code>&quot;    commands = []&quot;</code> |
| tests/test_followup.py:147 | BEYOND | ∅ (added file) | <code>&quot;    def run(cmd, **kwargs):&quot;</code> |
| tests/test_followup.py:148 | BEYOND | ∅ (added file) | <code>&quot;        commands.append(cmd); return NS(returncode=0, stderr=&#x27;&#x27;, stdout=&#x27;bubblewrap 0.4.0\\n&#x27;)&quot;</code> |
| tests/test_followup.py:149 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;run&#x27;, run)&quot;</code> |
| tests/test_followup.py:150 | BEYOND | ∅ (added file) | <code>&quot;    result = T.selfcheck(tmp_path)&quot;</code> |
| tests/test_followup.py:151 | BEYOND | ∅ (added file) | <code>&quot;    assert not result[&#x27;passed&#x27;] and &#x27;a0:&#x27; in result[&#x27;unverifiable&#x27;][0]&quot;</code> |
| tests/test_followup.py:152 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;checks&#x27;][&#x27;cpu_namespace&#x27;][&#x27;returncode&#x27;] == 0&quot;</code> |
| tests/test_followup.py:153 | BEYOND | ∅ (added file) | <code>&quot;    assert commands[0] == [&#x27;/usr/bin/bwrap&#x27;, &#x27;--version&#x27;]&quot;</code> |
| tests/test_followup.py:154 | BEYOND | ∅ (added file) | <code>&quot;    assert commands[1][-1] == &#x27;/bin/true&#x27;&quot;</code> |
| tests/test_followup.py:155 | BEYOND | ∅ (added file) | <code>&quot;    at = commands[1].index(&#x27;--dev-bind&#x27;)&quot;</code> |
| tests/test_followup.py:156 | BEYOND | ∅ (added file) | <code>&quot;    assert commands[1][at+1:at+3] == [&#x27;/dev/null&#x27;, &#x27;/dev/null&#x27;]&quot;</code> |
| tests/test_followup.py:157 | BEYOND | ∅ (added file) | <code>&quot;    assert T.disk_listing(tmp_path) == before&quot;</code> |
| tests/test_followup.py:158 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:159 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:160 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;command&#x27;, [&#x27;read&#x27;,&#x27;proof&#x27;])&quot;</code> |
| tests/test_followup.py:161 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;custom_bwrap&#x27;, [False, True])&quot;</code> |
| tests/test_followup.py:162 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;enabled&#x27;, [True, False])&quot;</code> |
| tests/test_followup.py:163 | BEYOND | ∅ (added file) | <code>&quot;def test_launch_yield_writes_exit_proof_and_model_inventory(tmp_path, monkeypatch, command, custom_bwrap, enabled):&quot;</code> |
| tests/test_followup.py:164 | BEYOND | ∅ (added file) | <code>&quot;    bwrap = &#x27;/usr/bin/bwrap&#x27;&quot;</code> |
| tests/test_followup.py:165 | BEYOND | ∅ (added file) | <code>&quot;    if custom_bwrap:&quot;</code> |
| tests/test_followup.py:166 | BEYOND | ∅ (added file) | <code>&quot;        selected = tmp_path/&#x27;selected-bwrap&#x27;&quot;</code> |
| tests/test_followup.py:167 | BEYOND | ∅ (added file) | <code>&quot;        selected.write_text(&#x27;#!/bin/sh\\nprintf \&quot;fixture bwrap 0.4.0\\\\n\&quot;\\n&#x27;)&quot;</code> |
| tests/test_followup.py:168 | BEYOND | ∅ (added file) | <code>&quot;        selected.chmod(0o700)&quot;</code> |
| tests/test_followup.py:169 | BEYOND | ∅ (added file) | <code>&quot;        bwrap = str(selected)&quot;</code> |
| tests/test_followup.py:170 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;probe&#x27;, lambda *a: dict(passed=True, versions={&#x27;python&#x27;:&#x27;fixture&#x27;}))&quot;</code> |
| tests/test_followup.py:171 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;capture_command&#x27;, lambda argv: dict(argv=argv, stdout=&#x27;&#x27;, returncode=None))&quot;</code> |
| tests/test_followup.py:172 | BEYOND | ∅ (added file) | <code>&quot;    cfg = dict(spec=dict(package=str(T.SJ/&#x27;pkg&#x27;),models={}), output=&#x27;old&#x27;)&quot;</code> |
| tests/test_followup.py:173 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;require_stage&#x27;, lambda root: copy.deepcopy(cfg))&quot;</code> |
| tests/test_followup.py:174 | BEYOND | ∅ (added file) | <code>&quot;    def need(*args):&quot;</code> |
| tests/test_followup.py:175 | BEYOND | ∅ (added file) | <code>&quot;        assert args[-2:] == (bwrap, enabled)&quot;</code> |
| tests/test_followup.py:176 | BEYOND | ∅ (added file) | <code>&quot;        return dict(ids=[&#x27;one&#x27;],need=[])&quot;</code> |
| tests/test_followup.py:177 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;cpu_need&#x27;, need)&quot;</code> |
| tests/test_followup.py:178 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;read_space&#x27;, lambda *a: 0)&quot;</code> |
| tests/test_followup.py:179 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;check_card&#x27;, lambda *a: {})&quot;</code> |
| tests/test_followup.py:180 | BEYOND | ∅ (added file) | <code>&quot;    def namespace(*args, **kwargs):&quot;</code> |
| tests/test_followup.py:181 | BEYOND | ∅ (added file) | <code>&quot;        assert kwargs[&#x27;bwrap&#x27;] == bwrap&quot;</code> |
| tests/test_followup.py:182 | BEYOND | ∅ (added file) | <code>&quot;        assert kwargs[&#x27;llguidance_stub&#x27;] == enabled&quot;</code> |
| tests/test_followup.py:183 | BEYOND | ∅ (added file) | <code>&quot;        return [bwrap, &#x27;fake-reader&#x27;]&quot;</code> |
| tests/test_followup.py:184 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;ns_command&#x27;, namespace)&quot;</code> |
| tests/test_followup.py:185 | BEYOND | ∅ (added file) | <code>&quot;    record = dict(example_id=&#x27;one&#x27;, token_ids=[1], raw_generation=&#x27;A&#x27;, extracted_answer=&#x27;A&#x27;, score=1.0)&quot;</code> |
| tests/test_followup.py:186 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;sj/pkg/parity/DEV20.json&#x27;, dict(ids=[&#x27;one&#x27;],need=[],arms={arm:[record] for arm in C.ARMS}))&quot;</code> |
| tests/test_followup.py:187 | BEYOND | ∅ (added file) | <code>&quot;    out = tmp_path/&#x27;runs/p12345678&#x27; if command == &#x27;proof&#x27; else tmp_path/&#x27;packet&#x27;&quot;</code> |
| tests/test_followup.py:188 | BEYOND | ∅ (added file) | <code>&quot;    models = out/&#x27;b0/d0/models&#x27; if command == &#x27;proof&#x27; else out/&#x27;direct/main/models&#x27;&quot;</code> |
| tests/test_followup.py:189 | BEYOND | ∅ (added file) | <code>&quot;    def reader(*args):&quot;</code> |
| tests/test_followup.py:190 | BEYOND | ∅ (added file) | <code>&quot;        (models/&#x27;base&#x27;).mkdir(parents=True); (models/&#x27;base/weights&#x27;).write_bytes(b&#x27;123&#x27;)&quot;</code> |
| tests/test_followup.py:191 | BEYOND | ∅ (added file) | <code>&quot;        return 75, dict(matched_file=str(tmp_path/&#x27;yield&#x27;),time=1,utc=&#x27;fixture&#x27;)&quot;</code> |
| tests/test_followup.py:192 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;run_reader&#x27;, reader)&quot;</code> |
| tests/test_followup.py:193 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;host_shm_ours&#x27;, lambda: [])&quot;</code> |
| tests/test_followup.py:194 | BEYOND | ∅ (added file) | <code>&quot;    class Sampler:&quot;</code> |
| tests/test_followup.py:195 | BEYOND | ∅ (added file) | <code>&quot;        def __init__(self, *args):&quot;</code> |
| tests/test_followup.py:196 | BEYOND | ∅ (added file) | <code>&quot;            self.thread = NS(start=lambda: None, join=lambda **kw: None)&quot;</code> |
| tests/test_followup.py:197 | BEYOND | ∅ (added file) | <code>&quot;            self.stop = NS(set=lambda: None); self.errors = []&quot;</code> |
| tests/test_followup.py:198 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;Sampler&#x27;, Sampler)&quot;</code> |
| tests/test_followup.py:199 | BEYOND | ∅ (added file) | <code>&quot;    args = NS(root=str(tmp_path),command=command,token=&#x27;p12345678&#x27;,gpu=&#x27;0&#x27;,shm=None,yield_glob=None,&quot;</code> |
| tests/test_followup.py:200 | BEYOND | ∅ (added file) | <code>&quot;              family=&#x27;main&#x27;,first=1,ids=None,out=str(out),artifact=str(T.LINEAGE/&#x27;m544/artifact.json&#x27;),sha256=&#x27;a&#x27;*64,step=544,bwrap=bwrap,&quot;</code> |
| tests/test_followup.py:201 | BEYOND | ∅ (added file) | <code>&quot;              llguidance_stub=enabled)&quot;</code> |
| tests/test_followup.py:202 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(RuntimeError, match=&#x27;Run or memory sampler failed&#x27;): T.launch(args)&quot;</code> |
| tests/test_followup.py:203 | BEYOND | ∅ (added file) | <code>&quot;    exit_info = T.load(out/&#x27;EXIT.json&#x27;); yielded = T.load(out/&#x27;YIELD.json&#x27;)&quot;</code> |
| tests/test_followup.py:204 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;yielded&#x27;] and exit_info[&#x27;returncode&#x27;] == 75&quot;</code> |
| tests/test_followup.py:205 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;host_dev_shm_ours&#x27;] == exit_info[&#x27;host_dev_shm_ours_before&#x27;] == []&quot;</code> |
| tests/test_followup.py:206 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;bwrap&#x27;] == T.load(out/&#x27;COMMAND.json&#x27;)[&#x27;bwrap&#x27;]&quot;</code> |
| tests/test_followup.py:207 | BEYOND | ∅ (added file) | <code>&quot;    overlay = T.llguidance_evidence(enabled)&quot;</code> |
| tests/test_followup.py:208 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;llguidance_stub&#x27;] == T.load(out/&#x27;COMMAND.json&#x27;)[&#x27;llguidance_stub&#x27;] == overlay&quot;</code> |
| tests/test_followup.py:209 | BEYOND | ∅ (added file) | <code>&quot;    assert T.load(out/&#x27;SPEC.json&#x27;)[&#x27;llguidance_stub&#x27;] == overlay&quot;</code> |
| tests/test_followup.py:210 | BEYOND | ∅ (added file) | <code>&quot;    assert T.load(out/&#x27;CONFIG.json&#x27;)[&#x27;spec&#x27;][&#x27;llguidance_stub&#x27;] == overlay&quot;</code> |
| tests/test_followup.py:211 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;bwrap&#x27;][&#x27;path&#x27;] == bwrap&quot;</code> |
| tests/test_followup.py:212 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;bwrap&#x27;][&#x27;sha256&#x27;] == T.sha(bwrap)&quot;</code> |
| tests/test_followup.py:213 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;bwrap&#x27;][&#x27;version&#x27;] == (&#x27;fixture bwrap 0.4.0\\n&#x27; if custom_bwrap else &#x27;bubblewrap 0.4.0\\n&#x27;)&quot;</code> |
| tests/test_followup.py:214 | BEYOND | ∅ (added file) | <code>&quot;    assert any(row[&#x27;bytes&#x27;] == 3 for row in yielded[&#x27;model_copies&#x27;])&quot;</code> |
| tests/test_followup.py:215 | BEYOND | ∅ (added file) | <code>&quot;    assert (out/&#x27;HOST_SHM_BEFORE.json&#x27;).exists()&quot;</code> |
| tests/test_followup.py:216 | BEYOND | ∅ (added file) | <code>&quot;    if command == &#x27;proof&#x27;:&quot;</code> |
| tests/test_followup.py:217 | BEYOND | ∅ (added file) | <code>&quot;        proof = T.load(out/&#x27;PROOF.json&#x27;)&quot;</code> |
| tests/test_followup.py:218 | BEYOND | ∅ (added file) | <code>&quot;        assert not proof[&#x27;passed&#x27;] and proof[&#x27;host_dev_shm_ours&#x27;] == []&quot;</code> |
| tests/test_followup.py:219 | BEYOND | ∅ (added file) | <code>&quot;        assert proof[&#x27;bwrap&#x27;] == exit_info[&#x27;bwrap&#x27;]&quot;</code> |
| tests/test_followup.py:220 | BEYOND | ∅ (added file) | <code>&quot;        assert proof[&#x27;llguidance_stub&#x27;] == overlay&quot;</code> |
| tests/test_followup.py:221 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:222 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:223 | BEYOND | ∅ (added file) | <code>&quot;def test_real_child_group_handles_term(tmp_path):&quot;</code> |
| tests/test_followup.py:224 | BEYOND | ∅ (added file) | <code>&quot;    script = &#x27;import signal,sys; signal.signal(signal.SIGTERM, lambda *a: sys.exit(0)); print(\&quot;ready\&quot;,flush=True); signal.pause()&#x27;&quot;</code> |
| tests/test_followup.py:225 | BEYOND | ∅ (added file) | <code>&quot;    child = subprocess.Popen([sys.executable, &#x27;-B&#x27;, &#x27;-c&#x27;, script], stdout=subprocess.PIPE,&quot;</code> |
| tests/test_followup.py:226 | BEYOND | ∅ (added file) | <code>&quot;                             universal_newlines=True, start_new_session=True)&quot;</code> |
| tests/test_followup.py:227 | BEYOND | ∅ (added file) | <code>&quot;    assert child.stdout.readline().strip() == &#x27;ready&#x27;&quot;</code> |
| tests/test_followup.py:228 | BEYOND | ∅ (added file) | <code>&quot;    assert os.getpgid(child.pid) == child.pid != os.getpgrp()&quot;</code> |
| tests/test_followup.py:229 | BEYOND | ∅ (added file) | <code>&quot;    assert T.stop_group(child, grace=0.1) == 0&quot;</code> |
| tests/test_followup.py:230 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:231 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:232 | BEYOND | ∅ (added file) | <code>&quot;def test_real_child_group_escalates_ignored_term(tmp_path):&quot;</code> |
| tests/test_followup.py:233 | BEYOND | ∅ (added file) | <code>&quot;    script = &#x27;import signal; signal.signal(signal.SIGTERM, signal.SIG_IGN); print(\&quot;ready\&quot;,flush=True); signal.pause()&#x27;&quot;</code> |
| tests/test_followup.py:234 | BEYOND | ∅ (added file) | <code>&quot;    child = subprocess.Popen([sys.executable, &#x27;-B&#x27;, &#x27;-c&#x27;, script], stdout=subprocess.PIPE,&quot;</code> |
| tests/test_followup.py:235 | BEYOND | ∅ (added file) | <code>&quot;                             universal_newlines=True, start_new_session=True)&quot;</code> |
| tests/test_followup.py:236 | BEYOND | ∅ (added file) | <code>&quot;    assert child.stdout.readline().strip() == &#x27;ready&#x27;&quot;</code> |
| tests/test_followup.py:237 | BEYOND | ∅ (added file) | <code>&quot;    assert T.stop_group(child, grace=0.1) == -signal.SIGKILL&quot;</code> |
| tests/test_followup.py:238 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:239 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_followup.py:240 | BEYOND | ∅ (added file) | <code>&quot;def test_camera_receipt_inventory_from_authenticated_tar(tmp_path):&quot;</code> |
| tests/test_followup.py:241 | BEYOND | ∅ (added file) | <code>&quot;    import hashlib&quot;</code> |
| tests/test_followup.py:242 | BEYOND | ∅ (added file) | <code>&quot;    import io&quot;</code> |
| tests/test_followup.py:243 | BEYOND | ∅ (added file) | <code>&quot;    import tarfile&quot;</code> |
| tests/test_followup.py:244 | BEYOND | ∅ (added file) | <code>&quot;    source = tmp_path/&#x27;camera.tar&#x27;&quot;</code> |
| tests/test_followup.py:245 | BEYOND | ∅ (added file) | <code>&quot;    with tarfile.open(str(source), &#x27;w&#x27;) as archive:&quot;</code> |
| tests/test_followup.py:246 | BEYOND | ∅ (added file) | <code>&quot;        info = tarfile.TarInfo(&#x27;sj/camera.json&#x27;); info.size = 2&quot;</code> |
| tests/test_followup.py:247 | BEYOND | ∅ (added file) | <code>&quot;        archive.addfile(info, io.BytesIO(b&#x27;{}&#x27;))&quot;</code> |
| tests/test_followup.py:248 | BEYOND | ∅ (added file) | <code>&quot;    pin = dict(bytes=source.stat().st_size, sha256=T.sha(source))&quot;</code> |
| tests/test_followup.py:249 | BEYOND | ∅ (added file) | <code>&quot;    rows = T.small_archive_inventory(source, pin)&quot;</code> |
| tests/test_followup.py:250 | BEYOND | ∅ (added file) | <code>&quot;    assert rows == {&#x27;sj/camera.json&#x27;: dict(bytes=2, sha256=hashlib.sha256(b&#x27;{}&#x27;).hexdigest())}&quot;</code> |
| tests/test_followup.py:251 | BEYOND | ∅ (added file) | <code>&quot;    pin[&#x27;sha256&#x27;] = &#x27;0&#x27;*64&quot;</code> |
| tests/test_followup.py:252 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError): T.small_archive_inventory(source, pin)&quot;</code> |
| README.md:1 | BEYOND | ∅ (added file) | <code>&quot;# Trinity dev-S1 direct reader&quot;</code> |
| README.md:2 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:3 | BEYOND | ∅ (added file) | <code>&quot;`trinity_read.py` stages local inputs and runs the accepted direct reader on one card. It accepts only `main`, `away`, and `forward`. The proof invokes the unchanged `proof/phase_b.py` directly; it does not invoke the chain&#x27;s official-item phase A. No command downloads files or uses SSH, Git, or Slurm.&quot;</code> |
| README.md:4 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:5 | BEYOND | ∅ (added file) | <code>&quot;The operator must approve heavy I/O under the Trinity rules before running real staging, frame ingestion, or a read. GPU commands below are operator commands; this build session does not execute them. Coordinate the chosen card before launch. Run from a compute node, never `trinity`.&quot;</code> |
| README.md:6 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:7 | BEYOND | ∅ (added file) | <code>&quot;## Paths and inputs&quot;</code> |
| README.md:8 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:9 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:10 | BEYOND | ∅ (added file) | <code>&quot;cd /scratch/jjyeung/orch_n30/trin_read/build&quot;</code> |
| README.md:11 | BEYOND | ∅ (added file) | <code>&quot;TRIN_ROOT=/scratch/jjyeung/orch_n30/trin_read/root&quot;</code> |
| README.md:12 | BEYOND | ∅ (added file) | <code>&quot;TRIN_DL=/scratch/jjyeung/orch_n30/trin_read/dl&quot;</code> |
| README.md:13 | BEYOND | ∅ (added file) | <code>&quot;TRIN_PY=/usr/bin/python3&quot;</code> |
| README.md:14 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:15 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:16 | BEYOND | ∅ (added file) | <code>&quot;The CLI supports Trinity&#x27;s system Python 3.6.8 and `../kit_src/.venv/bin/python`. Runtime work uses the staged Python interpreters. Tests use the kit venv. All output stays under `build/` or `root/`; production packets must stay under `--root`.&quot;</code> |
| README.md:17 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:18 | BEYOND | ∅ (added file) | <code>&quot;`stage` requires each complete source and its `&lt;filename&gt;.RECEIPT.json`: `runtime_0.tar`, `runtime_1.tar`, `runtime_2.tar`, `camera.tar`, `bwrap`, and `base.tar`. A receipt admits the transfer; runtime part hashes, camera/bwrap pins, and the base manifest authenticate its contents. `.part` files are never consumed. The existing step-544 export stays at `root/fsw/ap/8865619b/runs/469ddece/m544`.&quot;</code> |
| README.md:19 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:20 | BEYOND | ∅ (added file) | <code>&quot;## Stage&quot;</code> |
| README.md:21 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:22 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:23 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py stage --root \&quot;$TRIN_ROOT\&quot; --dl \&quot;$TRIN_DL\&quot;&quot;</code> |
| README.md:24 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:25 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:26 | BEYOND | ∅ (added file) | <code>&quot;The command stages each available piece once and records it in `root/STAGING.json`. Run it again as completed archives arrive. `complete: false` lists missing inputs; it does not mean a partial extraction succeeded. A piece marked `partial`, or an unrecorded existing destination, causes refusal. Preserve the evidence and resolve it manually; the runner never cleans, overwrites a partial extraction, or automatically retries.&quot;</code> |
| README.md:27 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:28 | BEYOND | ∅ (added file) | <code>&quot;The bootstrap is decoded as data from accepted job 169991&#x27;s `BATCH.sh`. Its `CONFIG.json`, launcher pins, `REVIEW.json`, payload SHA256, and every payload member hash are checked. The embedded bootstrap and reader payload retain their exact bytes. Runtime extraction uses the kit&#x27;s `extract_stream`, `links=True`, and unchanged `RUNTIME_ABSOLUTE_LINKS`. The base requires the exact manifest inventory. Export verification hashes the existing full-weight shards; it never moves or fetches them. Staging preserves the kit&#x27;s 200 GiB free-space floor and stages no videos.&quot;</code> |
| README.md:29 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:30 | BEYOND | ∅ (added file) | <code>&quot;## Frames&quot;</code> |
| README.md:31 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:32 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:33 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py frames --root \&quot;$TRIN_ROOT\&quot; --tar \&quot;$TRIN_DL/frames20.tar\&quot;&quot;</code> |
| README.md:34 | BEYOND | ∅ (added file) | <code>&quot;# Additional completed dev-S1 frame archives may be supplied together:&quot;</code> |
| README.md:35 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py frames --root \&quot;$TRIN_ROOT\&quot; --tar \&quot;$TRIN_DL/frames_more.tar\&quot; --tar \&quot;$TRIN_DL/frames_last.tar\&quot;&quot;</code> |
| README.md:36 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:37 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:38 | BEYOND | ∅ (added file) | <code>&quot;Every member must be a PNG named `&lt;sha[:2]&gt;/&lt;sha&gt;.png` whose bytes match its SHA256. The store contains `k6tk/MEMBERS.tsv.gz` and `k6tk/parts/&lt;tag&gt;/&lt;tag&gt;_000.tar`. New gzip index members append rows; existing rows and shards remain unchanged. Duplicate frames are checked and skipped. Shards publish only after full validation. An interrupted index append may leave a corrupt gzip stream; later commands refuse it. Do not ingest frames concurrently with a read. No recovery command removes data.&quot;</code> |
| README.md:39 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:40 | BEYOND | ∅ (added file) | <code>&quot;`proof`, `read`, `need`, `probe`, and `selfcheck` accept `--bwrap PATH` (default `/usr/bin/bwrap`). The host executable must support bubblewrap 0.4.0 flags. The pinned Orchard binary at `root/bwrap` remains authenticated evidence and never executes; selecting it, a link to it, or a byte-identical copy is refused.&quot;</code> |
| README.md:41 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:42 | BEYOND | ∅ (added file) | <code>&quot;The namespace binds this store read-only at `/project/community/jjyeung/cp4tk_fr/k6tk`, so the unchanged `proof/pull.py` and `phase_b.py` consume it directly. The namespace disables networking and gives CPU planning no GPU device nodes. Temporary files, caches, the home directory, and `/dev/shm` map into `root/` by default.&quot;</code> |
| README.md:43 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:44 | BEYOND | ∅ (added file) | <code>&quot;## llguidance overlay and CPU import probe&quot;</code> |
| README.md:45 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:46 | BEYOND | ∅ (added file) | <code>&quot;Trinity uses glibc 2.28. The staged vLLM 0.32.0 imports `llguidance` through structured-output dataclass annotations, but its native `_lib.abi3.so` requires GLIBC_2.30. `proof`, `read`, `need`, and `probe` default to `--llguidance-stub`; `--no-llguidance-stub` disables the overlay.&quot;</code> |
| README.md:47 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:48 | BEYOND | ∅ (added file) | <code>&quot;The runner verifies all three SHA256 pins in `trinity_read.py`, rejects extra files or symlinks, and read-only binds `build/llg_stub/llguidance/` over `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e/lib/python3.12/site-packages/llguidance` after the root binds. The destination must already exist. The v2 stub logs each module import and every attempted call before raising. It supplies `llguidance`, `LLMatcher`, `LLTokenizer`, and `LLInterpreter`; imports of `llguidance.hf` and `llguidance.torch` also log and raise. `work/llg_stub/` remains the v1 record. The stub supplies import-time names and raises on actual guidance use; structured-output requests remain unavailable. The overlay changes package loading while leaving staged bytes unchanged.&quot;</code> |
| README.md:49 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:50 | BEYOND | ∅ (added file) | <code>&quot;`COMMAND.json`, `EXIT.json`, `PROOF.json`, and packet `SPEC.json` carry `llguidance_stub` with `enabled`, source `path`, namespace `target`, the three file `sha256` pins, and `verified`. Run CONFIG and CPU NEED evidence carry the same object, including the satisfied names and stub version. Disabled overlays record the expected pins with `verified: false`. Packet SPEC is written before execution, so failed runs retain this evidence.&quot;</code> |
| README.md:51 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:52 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:53 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py probe --root \&quot;$TRIN_ROOT\&quot;&quot;</code> |
| README.md:54 | BEYOND | ∅ (added file) | <code>&quot;# Select the same private shm and host bwrap as a proof run:&quot;</code> |
| README.md:55 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py probe --root \&quot;$TRIN_ROOT\&quot; --shm \&quot;$TRIN_ROOT/shm\&quot; --bwrap /usr/bin/bwrap&quot;</code> |
| README.md:56 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:57 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:58 | BEYOND | ∅ (added file) | <code>&quot;`probe` requires a completed `runtime_0` receipt and its staged uv Python, plus the staged vLLM environment. It does not require the model/frame stage to be complete or wait for incoming archives. It runs the vLLM interpreter with `-I -B`, matching the isolated wrapper, inside the proof namespace with CPU-only devices, the same root binds, environment variables, stub, and private shm. It imports vLLM, torch, transformers, LLM, qwen3_5, engine core, and gpu_model_runner without loading a model or exposing GPU devices.&quot;</code> |
| README.md:59 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:60 | BEYOND | ∅ (added file) | <code>&quot;The command prints Python/vLLM/torch/transformers versions, glibc, and whether `cryptography` appears in the imported modules. Each invocation writes `root/runs/probe_&lt;utc&gt;/PROBE.json`, including refusals and failures. The report records the command, bwrap identity, overlay pins, environment, stdout/stderr, return code, and import result when execution reaches them. `cryptography_imported: null` means the import script did not report; it does not mean cryptography was absent. A failed probe exits nonzero and never retries.&quot;</code> |
| README.md:61 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:62 | BEYOND | ∅ (added file) | <code>&quot;The probe invokes the staged `GuidanceBackend.compile_grammar(REGEX, \&quot;a\&quot;)` on CPU with a minimal backend object. It bypasses tokenizer construction and model loading; vLLM 0.32.0 reaches `llguidance.grammar_from` while serializing that request. Acceptance requires the stub&#x27;s `RuntimeError` and a logged call. `PROBE.json.structured_output` records the reached stage, exception, exact reason, and call names. An unavailable interpreter or incompatible CPU API records why the check could not run; it never claims a successful failure test. `--no-llguidance-stub` records the check without requiring a stub exception.&quot;</code> |
| README.md:63 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:64 | BEYOND | ∅ (added file) | <code>&quot;Every proof/read/probe writes `SANDBOX.json`. It records the selected bwrap path/hash/version, the exact namespace argv, every bind&#x27;s source/target and ro/rw mode, symlinks and special mounts, stub path/hashes, host `ldd --version` first line, namespace glibc, host NVIDIA driver query, `/usr/lib64/libcuda.so.1` and `libnvidia-ml.so.1` resolved paths/sizes, and the libraries resolved by `ctypes.CDLL` inside the namespace. The CPU probe supplies package versions and its provenance. Unavailable fields remain null or carry errors; `namespace_executed` distinguishes attempted execution from preflight refusal. CPU driver resolution does not establish that a GPU model can run.&quot;</code> |
| README.md:65 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:66 | BEYOND | ∅ (added file) | <code>&quot;Proof/read perform a CPU probe before GPU admission and copy its report into the run. Each generation run sets `LLG_STUB_LOG` to its own `llg_stub_calls.jsonl`, inherited by the reader and engine processes through the shared root bind. The default outside the runner is `$TMPDIR/llg_stub_calls.jsonl` (`/tmp` if unset). The probe&#x27;s deliberate calls use a separate log. `LLGUIDANCE.json`, EXIT, and PROOF record import/call counts. Any generation-time stub call, corrupt log, or enabled stub with no import evidence fails the audit. Phase B packets under `b0/d0/` receive `SANDBOX.json` and `LLGUIDANCE.json`; read packets retain them at their root.&quot;</code> |
| README.md:67 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:68 | BEYOND | ∅ (added file) | <code>&quot;## Plan frames on the CPU&quot;</code> |
| README.md:69 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:70 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:71 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py need --root \&quot;$TRIN_ROOT\&quot; --family main --first 20 --out \&quot;$PWD/NEED20.txt\&quot;&quot;</code> |
| README.md:72 | BEYOND | ∅ (added file) | <code>&quot;cmp \&quot;$PWD/NEED20.txt\&quot; /scratch/jjyeung/orch_n30/trin_read/work/NEED20.txt&quot;</code> |
| README.md:73 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py need --root \&quot;$TRIN_ROOT\&quot; --family away --ids \&quot;$PWD/away.ids\&quot; --out \&quot;$PWD/NEED_AWAY.txt\&quot;&quot;</code> |
| README.md:74 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py need --root \&quot;$TRIN_ROOT\&quot; --all --out \&quot;$PWD/NEED_ALL.txt\&quot;&quot;</code> |
| README.md:75 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:76 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:77 | BEYOND | ∅ (added file) | <code>&quot;An ID file contains one exact `example_id` per line. Empty lines are ignored; duplicates, unknown IDs, nonpositive prefixes, and prefixes larger than the family are refused. ID-file order does not change execution order: the wrapper preserves `(benchmark, example_id)` sorting. `--all` covers every direct item in the three families.&quot;</code> |
| README.md:78 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:79 | BEYOND | ∅ (added file) | <code>&quot;Each CPU family run records `COMMAND.json` and `EXIT.json` under `root/needs/&lt;id&gt;/`, including the executed bwrap path, SHA256, and exact `--version` stdout/stderr. Each command writes the sorted SHA list, `&lt;out&gt;.missing`, and `&lt;out&gt;.json` with IDs, item/capture/frame counts, and estimated bytes. The estimate uses uncompressed RGB dimensions; it is not a measured PNG transfer size. Each family runs in a fresh process inside the namespace. Planning calls `direct.bind(dry=True)`, the kit&#x27;s `select_tasks`, and the family&#x27;s `origin.payload`; it does not decode video or load model weights. The real main-20 list must contain exactly 576 hashes and match `work/NEED20.txt`.&quot;</code> |
| README.md:80 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:81 | BEYOND | ∅ (added file) | <code>&quot;## Proof on one card&quot;</code> |
| README.md:82 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:83 | BEYOND | ∅ (added file) | <code>&quot;After a complete stage and frame ingestion, choose a fresh token and physical card index:&quot;</code> |
| README.md:84 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:85 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:86 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py proof --root \&quot;$TRIN_ROOT\&quot; --gpu 0 --token p2026111501 --repeat 2&quot;</code> |
| README.md:87 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:88 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:89 | BEYOND | ∅ (added file) | <code>&quot;The runner checks frame coverage before touching the GPU. It sets `CUDA_VISIBLE_DEVICES=0` and puts the token in the `SLURM_JOB_ID` environment field expected by the kit. It requires one selected card with at least 40 GiB, less than 100 MiB used, and no compute process. It executes the traced, unchanged phase B with the staged vLLM interpreter through `/data3/shared/scripts/vnice/vnice.sh`. The wrapper&#x27;s documented command-string interface is shell-quoted explicitly.&quot;</code> |
| README.md:90 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:91 | BEYOND | ∅ (added file) | <code>&quot;With the default `--repeat 1`, outputs live in `root/runs/&lt;token&gt;/`: `CONFIG.json`, `ENV.json`, `COMMAND.json`, `CARD.json`, `HOST_SHM_BEFORE.json`, `MEMORY.jsonl`, `run.log`, `EXIT.json`, `b0/d0/`, `PROOF.json`, and `PROOF.md`. `COMMAND.json` is an object with `argv`, `bwrap`, and `llguidance_stub`; `EXIT.json` and `PROOF.json` carry the same identities. The identity includes the resolved executable path, SHA256, and exact `--version` stdout/stderr. Tokens and output directories are single-use. A 1 s sampler records card memory; the report labels its maximum as a sampled peak. Subsecond peaks may be missed.&quot;</code> |
| README.md:92 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:93 | BEYOND | ∅ (added file) | <code>&quot;The proof compares all 20 items against `kit_src/parity/DEV20.json` for ON16k, B2048, and B4096. It reports exact token equality, zero-based divergence, lengths, raw-generation equality, extracted answers, score equality, and unrounded arm means. Missing items cannot pass. Timing comes from worker journals and budget receipts. Reused ON rows do not count as new budget generation; concurrent per-item latency is not wall-clock throughput. Missing measurements remain null. A failed run or sampler cannot produce a passing proof.&quot;</code> |
| README.md:94 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:95 | BEYOND | ∅ (added file) | <code>&quot;`proof --repeat 2` runs phase B sequentially on the same selected card in fresh `root/runs/&lt;token&gt;_r1/` and `&lt;token&gt;_r2/` directories. Each retains its comparison against accepted DEV20. `root/runs/&lt;token&gt;/RUN_TO_RUN.json` compares every item&#x27;s token IDs, first divergence, raw generation, answer, and score across both runs. The parent `PROOF.md` summarizes both accepted comparisons and run 1 versus run 2; its `PROOF.json` passes only if all three comparisons pass. Missing rows never compare equal. A killed, yielded, or failed execution stops the sequence and writes incomplete comparison evidence; the runner never retries it. A completed run with only an accepted-token mismatch can proceed to the second comparison run. Both packets retain model copies, so the usual free-space check runs before each phase B.&quot;</code> |
| README.md:96 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:97 | BEYOND | ∅ (added file) | <code>&quot;To regenerate the report without using a GPU:&quot;</code> |
| README.md:98 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:99 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:100 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B compare_tokens.py --reference ../kit_src/parity/DEV20.json --dest \&quot;$TRIN_ROOT/runs/p2026111501_r1/b0/d0\&quot; --attempt b0 --out \&quot;$TRIN_ROOT/runs/p2026111501_r1\&quot; --memory \&quot;$TRIN_ROOT/runs/p2026111501_r1/MEMORY.jsonl\&quot; --exit \&quot;$TRIN_ROOT/runs/p2026111501_r1/EXIT.json\&quot;&quot;</code> |
| README.md:101 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:102 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:103 | BEYOND | ∅ (added file) | <code>&quot;## Read a named item set&quot;</code> |
| README.md:104 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:105 | BEYOND | ∅ (added file) | <code>&quot;The operator stages exports at `root/fsw/ap/8865619b/runs/469ddece/m&lt;step&gt;/`. `--artifact` accepts the physical staged path or its original logical FSW path. The step, lineage path, artifact digest, shard bytes, tensor inventory, and base compatibility must pass the unchanged export checker before generation.&quot;</code> |
| README.md:106 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:107 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:108 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py read --root \&quot;$TRIN_ROOT\&quot; --family main --first 20 --artifact \&quot;$TRIN_ROOT/fsw/ap/8865619b/runs/469ddece/m544/artifact.json\&quot; --sha256 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef --step 544 --gpu 0 --token r2026111501 --out \&quot;$TRIN_ROOT/packets/r2026111501\&quot;&quot;</code> |
| README.md:109 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py read --root \&quot;$TRIN_ROOT\&quot; --family forward --ids \&quot;$PWD/forward.ids\&quot; --artifact \&quot;$TRIN_ROOT/fsw/ap/8865619b/runs/469ddece/m544/artifact.json\&quot; --sha256 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef --step 544 --gpu 0 --token r2026111502 --out \&quot;$TRIN_ROOT/packets/r2026111502\&quot;&quot;</code> |
| README.md:110 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:111 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:112 | BEYOND | ∅ (added file) | <code>&quot;Packets use the accepted per-family structure: `direct/&lt;family&gt;/request.json`, `PROMPT_PINS.json`, `BIND_STATUS.json`, `frames/0.json`, `results/0`, `results/budget_2048/0`, and `results/budget_4096/0`. Summary files retain the kit&#x27;s naming and admission rules. Packet-level files include `SPEC.json`, `CODE_PINS.json`, `SUMMARIES.json`, `COMPLETE.json`, and execution evidence. A smoke subset retains the kit&#x27;s smoke-number status; the wrapper does not promote it to a full-family result.&quot;</code> |
| README.md:113 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:114 | BEYOND | ∅ (added file) | <code>&quot;`namespace_worker.py` filters the in-memory `data.tasks_for` function and already imported aliases in the worker and mergers. It selects only validated IDs, preserves sort order, records `SELECTION.json` and the wrapper SHA in the request binding, and uses `smoke_items` for subsets. It never edits `direct.py`, `worker.py`, dataset files, or their pins. Frame realization and launch use the accepted public functions. Unknown IDs fail before a GPU check. Missing frames print `NEED` and stop before launch.&quot;</code> |
| README.md:115 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:116 | BEYOND | ∅ (added file) | <code>&quot;## Private shared memory and yielding&quot;</code> |
| README.md:117 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:118 | BEYOND | ∅ (added file) | <code>&quot;Both `proof` and `read` accept `--shm DIR`; the default is `&lt;root&gt;/shm`. The wrapper creates the directory and binds it over `/dev/shm` after the GPU namespace&#x27;s `--dev-bind /dev /dev`. CPU planning uses the same selection with a private device namespace. `DIR` must remain within the authorized `build/` or `root/` trees. Keep it under `root/` for a root-only copy; the default uses disk space rather than the host&#x27;s shared-memory mount.&quot;</code> |
| README.md:119 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:120 | BEYOND | ∅ (added file) | <code>&quot;`TMPDIR`, `HOME`, `XDG_CACHE_HOME`, `HF_HOME`, `TRITON_CACHE_DIR`, `TORCHINDUCTOR_CACHE_DIR`, and `VLLM_CACHE_ROOT` point under `root/`; `ENV.json` records their values. The wrapper lists immediate host `/dev/shm` entries owned by the current UID before and after execution, without following symlinks or descending into directories. `HOST_SHM_BEFORE.json` records the initial listing; `EXIT.json` and `PROOF.json` contain `host_dev_shm_ours_before` and `host_dev_shm_ours`. Empty lists are expected. Entries from other jobs under the same UID may appear; these observations do not attribute or delete them.&quot;</code> |
| README.md:121 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:122 | BEYOND | ∅ (added file) | <code>&quot;Add these options to either launch command:&quot;</code> |
| README.md:123 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:124 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:125 | BEYOND | ∅ (added file) | <code>&quot;--shm \&quot;$TRIN_ROOT/shm\&quot; --yield-glob \&quot;$TRIN_ROOT/control/*.yield\&quot;&quot;</code> |
| README.md:126 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:127 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:128 | BEYOND | ∅ (added file) | <code>&quot;Quote the glob so the wrapper receives it literally. Its parent must be a fixed directory within `build/` or `root/`; recursive globs and wildcard parents are refused. The watcher checks immediately after launching the reader, then every 30 seconds while it runs. A matching regular file triggers SIGTERM to the reader&#x27;s own process group, a 60-second grace period, then SIGKILL to that group only. The wrapper creates the group with `start_new_session=True`; it never signals its caller&#x27;s group or another job. Processes that deliberately leave that group are outside this signal boundary.&quot;</code> |
| README.md:129 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:130 | BEYOND | ∅ (added file) | <code>&quot;A yield makes `EXIT.json.returncode` 75 and the CLI exit nonzero. `YIELD.json` records the matched file, Unix/UTC time, group ID, and paths and byte sizes under the run directory and packet model directories. It inventories metadata after termination and reporting, before writing `YIELD.json` itself; it does not read model contents or follow symlinks. All leftovers remain for inspection. A yielded proof cannot pass, and the wrapper never retries it.&quot;</code> |
| README.md:131 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:132 | BEYOND | ∅ (added file) | <code>&quot;## Copying a root and checking it&quot;</code> |
| README.md:133 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:134 | BEYOND | ∅ (added file) | <code>&quot;The root carries the wrapper modules and their hashes in `root/trinity_runner/`; staging installs and verifies the same bundle. Runtime namespaces bind that directory and use the staged package&#x27;s parity reference, so a copied root does not need `kit_src/` or `evalx27/work/`. The default llguidance overlay additionally requires the three pinned files at `/scratch/jjyeung/orch_n30/trin_read/build/llg_stub/llguidance/` on the destination. Disabling the overlay removes that dependency but leaves the native GLIBC_2.30 requirement. The runner still needs the system directories, a compatible driver/runtime, and `/data3/shared/scripts/vnice/vnice.sh`. Use the **same absolute root path** on the destination node and preserve permissions and symlinks when copying its tar archive under the cluster transfer rules. This session performs no transfer.&quot;</code> |
| README.md:135 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:136 | BEYOND | ∅ (added file) | <code>&quot;After the copy, run on the destination compute node:&quot;</code> |
| README.md:137 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:138 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:139 | BEYOND | ∅ (added file) | <code>&quot;/usr/bin/python3 -B \&quot;$TRIN_ROOT/trinity_runner/trinity_read.py\&quot; selfcheck --root \&quot;$TRIN_ROOT\&quot;&quot;</code> |
| README.md:140 | BEYOND | ∅ (added file) | <code>&quot;# The build copy supports the same check:&quot;</code> |
| README.md:141 | BEYOND | ∅ (added file) | <code>&quot;\&quot;$TRIN_PY\&quot; -B trinity_read.py selfcheck --root \&quot;$TRIN_ROOT\&quot; --bwrap /usr/bin/bwrap&quot;</code> |
| README.md:142 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:143 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:144 | BEYOND | ∅ (added file) | <code>&quot;`selfcheck` writes JSON to stdout and exits nonzero for incomplete, unverifiable, or failed checks. It does not change the root. It checks recorded file sizes, SHA256 for files up to 1 MiB, the bootstrap payload and bwrap hashes, and wrapper hashes. It does not rehash large model shards or runtime archives. New runtime/camera/payload receipts retain member inventories; base/export checks use pinned manifests. A later authorized `stage` can enrich the existing camera receipt from its completed, authenticated small archive without extracting it again. Until that happens, its extracted files are explicitly unverifiable.&quot;</code> |
| README.md:145 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:146 | BEYOND | ∅ (added file) | <code>&quot;The selfcheck CPU probe starts `/bin/true` using the selected bwrap with networking disabled and private devices/shared memory. Its `--dev-bind` probe binds only `/dev/null`; it exposes no GPU devices. It exercises all flags emitted by the runner, including `--bind`, `--dir`, `--chdir`, and `--die-with-parent`. The JSON records the executed bwrap identity and probe command/result. It tests host compatibility, not the complete reader or CUDA runtime.&quot;</code> |
| README.md:147 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:148 | BEYOND | ∅ (added file) | <code>&quot;CONFIG auditing classifies unchanged literals from the authenticated accepted bootstrap as `pinned_evidence` when they are not active paths. These include Orchard host names, accepted job/transport paths, and hashes. They remain visible and do not fail selfcheck. Active model, artifact, interpreter, package, manifest, and run paths are checked against root, `/data3/shared/scripts/vnice`, and system directories. Logical namespace aliases map into root; path traversal and symlink escapes fail. The accepted bootstrap CONFIG SHA256 anchors the evidence classification. The exact llguidance stub source path is classified as `pinned_overlay` and authenticated against its three pins when enabled. The audit checks CONFIG strings and symlink targets without scanning source text, archives, or model contents.&quot;</code> |
| README.md:149 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:150 | BEYOND | ∅ (added file) | <code>&quot;`SELF_CHECK_BWRAP.json` records the real partial-root check with `/usr/bin/bwrap` 0.4.0. Its CONFIG audit passes, but selfcheck remains nonzero because runtime/base/payload pieces are missing, the camera receipt lacks a member inventory, and this agent sandbox rejects the probe&#x27;s `NETLINK_ROUTE` socket. The flag set passes option parsing and appears in 0.4.0&#x27;s help; namespace execution remains unverified in this session. `BWRAP_FLAGS.json` records coverage. No flag replacement is needed. The operator&#x27;s successful namespace test is separate evidence; no GPU result is claimed here.&quot;</code> |
| README.md:151 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:152 | BEYOND | ∅ (added file) | <code>&quot;## Settings, tests, and failure meanings&quot;</code> |
| README.md:153 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:154 | BEYOND | ∅ (added file) | <code>&quot;The reader retains `max_model_len=49152`, greedy decoding, thinking cap 16384, memory utilization 0.90, max sequences 32, batched-token cap 8192, inflight 16, seed 17, tensor parallel size 1, and disabled prefix caching. An OOM or unsupported runtime fails the run; no setting is reduced automatically. See `DIFF.md` for the complete added-code ledger and open validation risks.&quot;</code> |
| README.md:155 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:156 | BEYOND | ∅ (added file) | <code>&quot;The unchanged reader retains two model copies per packet: `direct/&lt;family&gt;/models/base` and `direct/&lt;family&gt;/models/cp1m200` (`b0/d0/models/` for proof). `--keep-models` and `--no-keep-models` are documentation concepts only: neither flag is implemented, and the wrapper never removes these copies.&quot;</code> |
| README.md:157 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:158 | BEYOND | ∅ (added file) | <code>&quot;Budget roughly **36 GiB per read for model copies**, even for a one-item read. The step-544 export&#x27;s five shards total 18,819,721,016 bytes (17.527 GiB); the base archive is 18.002 GiB including tar overhead. The base&#x27;s exact copied size comes from its pinned manifest when staged; copied model metadata adds a small amount. Each fresh packet needs its own copies.&quot;</code> |
| README.md:159 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:160 | BEYOND | ∅ (added file) | <code>&quot;Before launch, `SPACE.json` records `base manifest bytes + export shard bytes + 2 \u00d7 estimated frame bytes + 2 GiB`, while preserving the 200 GiB free-space floor. Frames occupy both a tar and extracted PNGs. Caches, private shared-memory files, and concurrent disk users also consume space; the reserve neither allocates nor caps them.&quot;</code> |
| README.md:161 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:162 | BEYOND | ∅ (added file) | <code>&quot;```bash&quot;</code> |
| README.md:163 | BEYOND | ∅ (added file) | <code>&quot;# Use a fresh basetemp path for every invocation; retain existing test evidence.&quot;</code> |
| README.md:164 | BEYOND | ∅ (added file) | <code>&quot;PYTHONDONTWRITEBYTECODE=1 ../kit_src/.venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=\&quot;$PWD/tests/operator_run_01\&quot; tests&quot;</code> |
| README.md:165 | BEYOND | ∅ (added file) | <code>&quot;```&quot;</code> |
| README.md:166 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:167 | BEYOND | ∅ (added file) | <code>&quot;The tests use kit fakes, miniature frame archives, mocked GPU boundaries, and real CPU child process groups for TERM/KILL handling. Public dry-bind tests read the accepted runtime copy in `evalx27/work/pull/x27c/r2`, including its away/forward payloads. They do not establish that the real namespace or vLLM engine runs on Ada.&quot;</code> |
| README.md:168 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| README.md:169 | BEYOND | ∅ (added file) | <code>&quot;`REFUSED` means an input, pin, path, card, stage, or membership check failed. A nonzero GPU command requires inspection of `run.log`, `EXIT.json`, and any proof report. If a process is killed or a connection drops, stop and coordinate under the Trinity rules; do not relaunch automatically. `PROOF.json` with `passed: false` reports a mismatch or incomplete evidence, not acceptance. No real GPU result is claimed by the CPU tests.&quot;</code> |
| REPORT.md:1 | BEYOND | ∅ (added file) | <code>&quot;The Trinity runner provides stage, frames, need, proof, and read subcommands with operator commands in README.md.&quot;</code> |
| REPORT.md:2 | BEYOND | ∅ (added file) | <code>&quot;The implementation leaves kit_src and the existing step-544 export unchanged.&quot;</code> |
| REPORT.md:3 | BEYOND | ∅ (added file) | <code>&quot;Tests: 33 passed; see TESTS.log. No GPU, network, SSH, or Git command ran.&quot;</code> |
| REPORT.md:4 | BEYOND | ∅ (added file) | <code>&quot;System Python 3.6.8 passed CLI/bootstrap checks and the frame-store test; pytest used the kit Python 3.12.13 environment.&quot;</code> |
| REPORT.md:5 | BEYOND | ∅ (added file) | <code>&quot;CPU dry-bind checks used the accepted runtime source and kit dependency fakes for all three families.&quot;</code> |
| REPORT.md:6 | BEYOND | ∅ (added file) | <code>&quot;Main-first-20 produced exactly 576 hashes, byte-identical to work/NEED20.txt; see NEED20.fixture.txt.&quot;</code> |
| REPORT.md:7 | BEYOND | ∅ (added file) | <code>&quot;Full-set planning covered 1,525 main, 150 away, and 150 forward items; see PLANNING_CHECK.json.&quot;</code> |
| REPORT.md:8 | BEYOND | ∅ (added file) | <code>&quot;The retained Orchard packet compared identically for all 20 items in each arm; actual/accepted means were 0.65/0.65.&quot;</code> |
| REPORT.md:9 | BEYOND | ∅ (added file) | <code>&quot;That comparison checks the reporter against retained evidence; it is not a new Trinity token proof.&quot;</code> |
| REPORT.md:10 | BEYOND | ∅ (added file) | <code>&quot;Real stage and real namespace need did not run: runtime_0.tar, runtime_1.tar, runtime_2.tar, base.tar, and frames20.tar were absent.&quot;</code> |
| REPORT.md:11 | BEYOND | ∅ (added file) | <code>&quot;Those five inputs had zero-byte .part files; camera.tar and bwrap were present without completion receipts. See LOCAL_INPUTS.json.&quot;</code> |
| REPORT.md:12 | BEYOND | ∅ (added file) | <code>&quot;DIFF BEYOND: piece completion/refusal and existing-export verification; append-only frame store; direct-only CPU planning and ID filter.&quot;</code> |
| REPORT.md:13 | BEYOND | ∅ (added file) | <code>&quot;DIFF BEYOND: phase-B-only entry, single-card admission, token job identity, vnice wrapper, memory sampler, exact comparison, and disk reserve.&quot;</code> |
| REPORT.md:14 | BEYOND | ∅ (added file) | <code>&quot;DIFF BEYOND: network/device isolation, packet/run admission, tests, and documentation; the source ledger lists every added line.&quot;</code> |
| REPORT.md:15 | BEYOND | ∅ (added file) | <code>&quot;Reader settings and source bytes remain unchanged; no reduced-memory fallback exists.&quot;</code> |
| REPORT.md:16 | BEYOND | ∅ (added file) | <code>&quot;OPEN: Ada capacity/token parity, staged runtime and host compatibility, bwrap namespace support, and real performance/peak memory need operator validation.&quot;</code> |
| REPORT.md:17 | BEYOND | ∅ (added file) | <code>&quot;OPEN: staging and frame ingestion require the Trinity heavy-I/O approval; interrupted pieces or store indexes require manual review without automatic retries.&quot;</code> |
| REPORT_ADDENDUM.md:1 | BEYOND | ∅ (added file) | <code>&quot;Proof/read support private --shm, root-local temp/home/caches, and before/after UID-owned host /dev/shm evidence.&quot;</code> |
| REPORT_ADDENDUM.md:2 | BEYOND | ∅ (added file) | <code>&quot;--yield-glob polls every 30 seconds, sends TERM then KILL after 60 seconds only to its reader group, and records YIELD.json leftovers.&quot;</code> |
| REPORT_ADDENDUM.md:3 | BEYOND | ∅ (added file) | <code>&quot;The unchanged reader retains both packet model copies; README budgets roughly 36 GiB per read plus frames, caches, and logs.&quot;</code> |
| REPORT_ADDENDUM.md:4 | BEYOND | ∅ (added file) | <code>&quot;root/trinity_runner carries the three wrapper modules for a root-only copy at the same absolute path.&quot;</code> |
| REPORT_ADDENDUM.md:5 | BEYOND | ∅ (added file) | <code>&quot;selfcheck verifies recorded sizes, small-file SHA256, bootstrap/bwrap pins, wrapper hashes, CONFIG literals, symlinks, and a CPU bwrap probe.&quot;</code> |
| REPORT_ADDENDUM.md:6 | BEYOND | ∅ (added file) | <code>&quot;Tests: 56 passed (33 existing, 23 added); TESTS_ADDENDUM_FINAL.log includes real CPU TERM/KILL tests and mocked proof/read yields.&quot;</code> |
| REPORT_ADDENDUM.md:7 | BEYOND | ∅ (added file) | <code>&quot;The existing STAGING.json, bootstrap, bwrap, and export metadata remain unchanged; see ROOT_PRESERVED.json.&quot;</code> |
| REPORT_ADDENDUM.md:8 | BEYOND | ∅ (added file) | <code>&quot;Final metadata checks passed for 19 staged files and 3 wrapper files; five large shards received size checks only.&quot;</code> |
| REPORT_ADDENDUM.md:9 | BEYOND | ∅ (added file) | <code>&quot;OPEN: the real CPU probe failed because staged bwrap requires unavailable GLIBC 2.33/2.34/2.38; no retry or binary replacement ran.&quot;</code> |
| REPORT_ADDENDUM.md:10 | BEYOND | ∅ (added file) | <code>&quot;OPEN: 34 CONFIG findings include a pinned Orchard host name and outside paths; literal portability cannot pass without changing pinned evidence.&quot;</code> |
| REPORT_ADDENDUM.md:11 | BEYOND | ∅ (added file) | <code>&quot;OPEN: runtime/base/payload stages remain incomplete, and the existing a0 receipt lacks member hashes; selfcheck refuses acceptance.&quot;</code> |
| REPORT_ADDENDUM.md:12 | BEYOND | ∅ (added file) | <code>&quot;No GPU, network, SSH, Git, deletion, model-content scan, or input-tar wait ran. README and DIFF.md document the boundaries.&quot;</code> |
| tests/test_bwrap.py:1 | BEYOND | ∅ (added file) | <code>&quot;import copy&quot;</code> |
| tests/test_bwrap.py:2 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/test_bwrap.py:3 | BEYOND | ∅ (added file) | <code>&quot;import subprocess&quot;</code> |
| tests/test_bwrap.py:4 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/test_bwrap.py:5 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace as NS&quot;</code> |
| tests/test_bwrap.py:6 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:7 | BEYOND | ∅ (added file) | <code>&quot;import pytest&quot;</code> |
| tests/test_bwrap.py:8 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| tests/test_bwrap.py:9 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:10 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:11 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;command&#x27;, [&#x27;proof&#x27;, &#x27;read&#x27;, &#x27;need&#x27;, &#x27;selfcheck&#x27;])&quot;</code> |
| tests/test_bwrap.py:12 | BEYOND | ∅ (added file) | <code>&quot;def test_bwrap_option_help(command):&quot;</code> |
| tests/test_bwrap.py:13 | BEYOND | ∅ (added file) | <code>&quot;    result = subprocess.run([sys.executable, &#x27;-B&#x27;, str(T.BUILD/&#x27;trinity_read.py&#x27;), command, &#x27;--help&#x27;],&quot;</code> |
| tests/test_bwrap.py:14 | BEYOND | ∅ (added file) | <code>&quot;                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)&quot;</code> |
| tests/test_bwrap.py:15 | BEYOND | ∅ (added file) | <code>&quot;    assert result.returncode == 0 and &#x27;--bwrap&#x27; in result.stdout and &#x27;/usr/bin/bwrap&#x27; in result.stdout&quot;</code> |
| tests/test_bwrap.py:16 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:17 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:18 | BEYOND | ∅ (added file) | <code>&quot;def host_fixture(tmp_path):&quot;</code> |
| tests/test_bwrap.py:19 | BEYOND | ∅ (added file) | <code>&quot;    path = tmp_path/&#x27;host-bwrap&#x27;&quot;</code> |
| tests/test_bwrap.py:20 | BEYOND | ∅ (added file) | <code>&quot;    path.write_text(&#x27;#!/bin/sh\\nprintf \&quot;fixture bwrap 0.4.0\\\\n\&quot;\\n&#x27;)&quot;</code> |
| tests/test_bwrap.py:21 | BEYOND | ∅ (added file) | <code>&quot;    path.chmod(0o700)&quot;</code> |
| tests/test_bwrap.py:22 | BEYOND | ∅ (added file) | <code>&quot;    return path&quot;</code> |
| tests/test_bwrap.py:23 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:24 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:25 | BEYOND | ∅ (added file) | <code>&quot;def test_custom_executable_identity_and_namespace(tmp_path):&quot;</code> |
| tests/test_bwrap.py:26 | BEYOND | ∅ (added file) | <code>&quot;    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)&quot;</code> |
| tests/test_bwrap.py:27 | BEYOND | ∅ (added file) | <code>&quot;    path = host_fixture(tmp_path)&quot;</code> |
| tests/test_bwrap.py:28 | BEYOND | ∅ (added file) | <code>&quot;    evidence = T.bwrap_evidence(tmp_path, str(path))&quot;</code> |
| tests/test_bwrap.py:29 | BEYOND | ∅ (added file) | <code>&quot;    assert evidence == dict(path=str(path), sha256=T.sha(path), version=&#x27;fixture bwrap 0.4.0\\n&#x27;, version_stderr=&#x27;&#x27;)&quot;</code> |
| tests/test_bwrap.py:30 | BEYOND | ∅ (added file) | <code>&quot;    assert T.namespace(tmp_path, bwrap=str(path))[0] == str(path)&quot;</code> |
| tests/test_bwrap.py:31 | BEYOND | ∅ (added file) | <code>&quot;    assert T.namespace(tmp_path)[0] == &#x27;/usr/bin/bwrap&#x27;&quot;</code> |
| tests/test_bwrap.py:32 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:33 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:34 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;alias&#x27;, [&#x27;direct&#x27;, &#x27;symlink&#x27;, &#x27;hardlink&#x27;, &#x27;copy&#x27;])&quot;</code> |
| tests/test_bwrap.py:35 | BEYOND | ∅ (added file) | <code>&quot;def test_never_execute_pinned_bwrap(tmp_path, monkeypatch, alias):&quot;</code> |
| tests/test_bwrap.py:36 | BEYOND | ∅ (added file) | <code>&quot;    staged = tmp_path/&#x27;bwrap&#x27;; staged.write_bytes(b&#x27;pinned bytes&#x27;)&quot;</code> |
| tests/test_bwrap.py:37 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;PINNED_BWRAP_SHA256&#x27;, T.sha(staged))&quot;</code> |
| tests/test_bwrap.py:38 | BEYOND | ∅ (added file) | <code>&quot;    path = staged&quot;</code> |
| tests/test_bwrap.py:39 | BEYOND | ∅ (added file) | <code>&quot;    if alias != &#x27;direct&#x27;:&quot;</code> |
| tests/test_bwrap.py:40 | BEYOND | ∅ (added file) | <code>&quot;        path = tmp_path/alias&quot;</code> |
| tests/test_bwrap.py:41 | BEYOND | ∅ (added file) | <code>&quot;        if alias == &#x27;symlink&#x27;: path.symlink_to(staged)&quot;</code> |
| tests/test_bwrap.py:42 | BEYOND | ∅ (added file) | <code>&quot;        elif alias == &#x27;hardlink&#x27;: T.os.link(str(staged), str(path))&quot;</code> |
| tests/test_bwrap.py:43 | BEYOND | ∅ (added file) | <code>&quot;        else: path.write_bytes(staged.read_bytes())&quot;</code> |
| tests/test_bwrap.py:44 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;run&#x27;, lambda *a, **k: pytest.fail(&#x27;Pinned binary executed&#x27;))&quot;</code> |
| tests/test_bwrap.py:45 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;bwrap&#x27;): T.bwrap_evidence(tmp_path, path)&quot;</code> |
| tests/test_bwrap.py:46 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:47 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:48 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;code&#x27;, [0, 7])&quot;</code> |
| tests/test_bwrap.py:49 | BEYOND | ∅ (added file) | <code>&quot;def test_need_records_selected_bwrap_even_on_failure(tmp_path, monkeypatch, code):&quot;</code> |
| tests/test_bwrap.py:50 | BEYOND | ∅ (added file) | <code>&quot;    path = host_fixture(tmp_path); real_run = subprocess.run&quot;</code> |
| tests/test_bwrap.py:51 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;require_stage&#x27;, lambda root: {})&quot;</code> |
| tests/test_bwrap.py:52 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;install_runner&#x27;, lambda root: None)&quot;</code> |
| tests/test_bwrap.py:53 | BEYOND | ∅ (added file) | <code>&quot;    def command(root, config, script, args, **kwargs):&quot;</code> |
| tests/test_bwrap.py:54 | BEYOND | ∅ (added file) | <code>&quot;        assert kwargs[&#x27;bwrap&#x27;] == str(path)&quot;</code> |
| tests/test_bwrap.py:55 | BEYOND | ∅ (added file) | <code>&quot;        work = Path(args[1]).parent&quot;</code> |
| tests/test_bwrap.py:56 | BEYOND | ∅ (added file) | <code>&quot;        T.dump(work/&#x27;NEED.json&#x27;, dict(need=[], ids=[]))&quot;</code> |
| tests/test_bwrap.py:57 | BEYOND | ∅ (added file) | <code>&quot;        return [str(path), &#x27;--fixture&#x27;]&quot;</code> |
| tests/test_bwrap.py:58 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;ns_command&#x27;, command)&quot;</code> |
| tests/test_bwrap.py:59 | BEYOND | ∅ (added file) | <code>&quot;    def run(cmd, **kwargs):&quot;</code> |
| tests/test_bwrap.py:60 | BEYOND | ∅ (added file) | <code>&quot;        if cmd[-1] == &#x27;--version&#x27;: return real_run(cmd, **kwargs)&quot;</code> |
| tests/test_bwrap.py:61 | BEYOND | ∅ (added file) | <code>&quot;        return subprocess.CompletedProcess(cmd, code)&quot;</code> |
| tests/test_bwrap.py:62 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;run&#x27;, run)&quot;</code> |
| tests/test_bwrap.py:63 | BEYOND | ∅ (added file) | <code>&quot;    if code:&quot;</code> |
| tests/test_bwrap.py:64 | BEYOND | ∅ (added file) | <code>&quot;        with pytest.raises(subprocess.CalledProcessError): T.cpu_need(tmp_path, &#x27;main&#x27;, bwrap=str(path))&quot;</code> |
| tests/test_bwrap.py:65 | BEYOND | ∅ (added file) | <code>&quot;    else:&quot;</code> |
| tests/test_bwrap.py:66 | BEYOND | ∅ (added file) | <code>&quot;        assert T.cpu_need(tmp_path, &#x27;main&#x27;, bwrap=str(path))[&#x27;bwrap&#x27;][&#x27;path&#x27;] == str(path)&quot;</code> |
| tests/test_bwrap.py:67 | BEYOND | ∅ (added file) | <code>&quot;    work = next((tmp_path/&#x27;needs&#x27;).iterdir())&quot;</code> |
| tests/test_bwrap.py:68 | BEYOND | ∅ (added file) | <code>&quot;    command = T.load(work/&#x27;COMMAND.json&#x27;); exit_info = T.load(work/&#x27;EXIT.json&#x27;)&quot;</code> |
| tests/test_bwrap.py:69 | BEYOND | ∅ (added file) | <code>&quot;    assert exit_info[&#x27;returncode&#x27;] == code&quot;</code> |
| tests/test_bwrap.py:70 | BEYOND | ∅ (added file) | <code>&quot;    assert command[&#x27;bwrap&#x27;] == exit_info[&#x27;bwrap&#x27;]&quot;</code> |
| tests/test_bwrap.py:71 | BEYOND | ∅ (added file) | <code>&quot;    assert command[&#x27;bwrap&#x27;][&#x27;sha256&#x27;] == T.sha(path)&quot;</code> |
| tests/test_bwrap.py:72 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:73 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:74 | BEYOND | ∅ (added file) | <code>&quot;def accepted_fixture(tmp_path):&quot;</code> |
| tests/test_bwrap.py:75 | BEYOND | ∅ (added file) | <code>&quot;    raw = (T.DEFAULT_ROOT/&#x27;bootstrap/CONFIG.json&#x27;).read_bytes()&quot;</code> |
| tests/test_bwrap.py:76 | BEYOND | ∅ (added file) | <code>&quot;    assert T.sha(T.DEFAULT_ROOT/&#x27;bootstrap/CONFIG.json&#x27;) == T.ACCEPTED_CONFIG_SHA256&quot;</code> |
| tests/test_bwrap.py:77 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;bootstrap&#x27;).mkdir()&quot;</code> |
| tests/test_bwrap.py:78 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;bootstrap/CONFIG.json&#x27;).write_bytes(raw)&quot;</code> |
| tests/test_bwrap.py:79 | BEYOND | ∅ (added file) | <code>&quot;    return T.load(tmp_path/&#x27;bootstrap/CONFIG.json&#x27;)&quot;</code> |
| tests/test_bwrap.py:80 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:81 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:82 | BEYOND | ∅ (added file) | <code>&quot;def test_accepted_config_evidence_is_informational(tmp_path):&quot;</code> |
| tests/test_bwrap.py:83 | BEYOND | ∅ (added file) | <code>&quot;    accepted_fixture(tmp_path)&quot;</code> |
| tests/test_bwrap.py:84 | BEYOND | ∅ (added file) | <code>&quot;    result = T.config_audit(tmp_path)&quot;</code> |
| tests/test_bwrap.py:85 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;passed&#x27;] and result[&#x27;pinned_template_authenticated&#x27;]&quot;</code> |
| tests/test_bwrap.py:86 | BEYOND | ∅ (added file) | <code>&quot;    evidence = [r for r in result[&#x27;findings&#x27;] if r[&#x27;kind&#x27;] == &#x27;pinned_evidence&#x27;]&quot;</code> |
| tests/test_bwrap.py:87 | BEYOND | ∅ (added file) | <code>&quot;    assert any(r[&#x27;value&#x27;] == &#x27;orchard-login-001&#x27; for r in evidence)&quot;</code> |
| tests/test_bwrap.py:88 | BEYOND | ∅ (added file) | <code>&quot;    assert any(r[&#x27;value&#x27;].startswith(&#x27;/project/&#x27;) for r in evidence)&quot;</code> |
| tests/test_bwrap.py:89 | BEYOND | ∅ (added file) | <code>&quot;    assert any(len(r[&#x27;value&#x27;]) == 64 for r in evidence)&quot;</code> |
| tests/test_bwrap.py:90 | BEYOND | ∅ (added file) | <code>&quot;    assert all(not r[&#x27;fails&#x27;] for r in evidence)&quot;</code> |
| tests/test_bwrap.py:91 | BEYOND | ∅ (added file) | <code>&quot;    active = next(r for r in result[&#x27;findings&#x27;] if r[&#x27;field&#x27;] == &#x27;$.spec.artifact.path&#x27;)&quot;</code> |
| tests/test_bwrap.py:92 | BEYOND | ∅ (added file) | <code>&quot;    assert active[&#x27;kind&#x27;] == &#x27;namespace_alias&#x27; and active[&#x27;mapped_path&#x27;].startswith(str(tmp_path))&quot;</code> |
| tests/test_bwrap.py:93 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:94 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:95 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;field,value&#x27;, [(&#x27;package&#x27;, &#x27;/data3/escape/package&#x27;),&quot;</code> |
| tests/test_bwrap.py:96 | BEYOND | ∅ (added file) | <code>&quot;                                        (&#x27;run&#x27;, &#x27;/home/escape/job&#x27;),&quot;</code> |
| tests/test_bwrap.py:97 | BEYOND | ∅ (added file) | <code>&quot;                                        (&#x27;package&#x27;, str(T.SJ/&#x27;../../data3/escape&#x27;))])&quot;</code> |
| tests/test_bwrap.py:98 | BEYOND | ∅ (added file) | <code>&quot;def test_active_paths_in_run_config_fail(tmp_path, field, value):&quot;</code> |
| tests/test_bwrap.py:99 | BEYOND | ∅ (added file) | <code>&quot;    config = accepted_fixture(tmp_path)&quot;</code> |
| tests/test_bwrap.py:100 | BEYOND | ∅ (added file) | <code>&quot;    config[&#x27;spec&#x27;][field] = value&quot;</code> |
| tests/test_bwrap.py:101 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;runs/token/CONFIG.json&#x27;, config)&quot;</code> |
| tests/test_bwrap.py:102 | BEYOND | ∅ (added file) | <code>&quot;    result = T.config_audit(tmp_path)&quot;</code> |
| tests/test_bwrap.py:103 | BEYOND | ∅ (added file) | <code>&quot;    assert not result[&#x27;passed&#x27;]&quot;</code> |
| tests/test_bwrap.py:104 | BEYOND | ∅ (added file) | <code>&quot;    assert any(r.get(&#x27;field&#x27;) == &#x27;$.spec.&#x27;+field and r[&#x27;fails&#x27;] for r in result[&#x27;findings&#x27;])&quot;</code> |
| tests/test_bwrap.py:105 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:106 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:107 | BEYOND | ∅ (added file) | <code>&quot;def test_namespace_alias_cannot_hide_symlink_escape(tmp_path):&quot;</code> |
| tests/test_bwrap.py:108 | BEYOND | ∅ (added file) | <code>&quot;    accepted_fixture(tmp_path)&quot;</code> |
| tests/test_bwrap.py:109 | BEYOND | ∅ (added file) | <code>&quot;    (tmp_path/&#x27;sj&#x27;).symlink_to(&#x27;/data3/escape&#x27;)&quot;</code> |
| tests/test_bwrap.py:110 | BEYOND | ∅ (added file) | <code>&quot;    result = T.config_audit(tmp_path)&quot;</code> |
| tests/test_bwrap.py:111 | BEYOND | ∅ (added file) | <code>&quot;    assert not result[&#x27;passed&#x27;]&quot;</code> |
| tests/test_bwrap.py:112 | BEYOND | ∅ (added file) | <code>&quot;    assert any(r.get(&#x27;field&#x27;) == &#x27;$.spec.package&#x27; and r[&#x27;fails&#x27;] for r in result[&#x27;findings&#x27;])&quot;</code> |
| tests/test_bwrap.py:113 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:114 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:115 | BEYOND | ∅ (added file) | <code>&quot;def test_modified_bootstrap_is_not_accepted_evidence(tmp_path):&quot;</code> |
| tests/test_bwrap.py:116 | BEYOND | ∅ (added file) | <code>&quot;    config = accepted_fixture(tmp_path)&quot;</code> |
| tests/test_bwrap.py:117 | BEYOND | ∅ (added file) | <code>&quot;    config[&#x27;assets&#x27;][&#x27;observed_host&#x27;] = &#x27;orchard-login-999&#x27;&quot;</code> |
| tests/test_bwrap.py:118 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;bootstrap/CONFIG.json&#x27;, config)&quot;</code> |
| tests/test_bwrap.py:119 | BEYOND | ∅ (added file) | <code>&quot;    result = T.config_audit(tmp_path)&quot;</code> |
| tests/test_bwrap.py:120 | BEYOND | ∅ (added file) | <code>&quot;    assert not result[&#x27;pinned_template_authenticated&#x27;]&quot;</code> |
| tests/test_bwrap.py:121 | BEYOND | ∅ (added file) | <code>&quot;    assert not any(r[&#x27;kind&#x27;] == &#x27;pinned_evidence&#x27; for r in result[&#x27;findings&#x27;])&quot;</code> |
| tests/test_bwrap.py:122 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:123 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_bwrap.py:124 | BEYOND | ∅ (added file) | <code>&quot;def test_need_cli_passes_bwrap_to_every_family(tmp_path, monkeypatch):&quot;</code> |
| tests/test_bwrap.py:125 | BEYOND | ∅ (added file) | <code>&quot;    calls = []&quot;</code> |
| tests/test_bwrap.py:126 | BEYOND | ∅ (added file) | <code>&quot;    def need(*args):&quot;</code> |
| tests/test_bwrap.py:127 | BEYOND | ∅ (added file) | <code>&quot;        calls.append(args)&quot;</code> |
| tests/test_bwrap.py:128 | BEYOND | ∅ (added file) | <code>&quot;        return dict(need=[], items=0, estimated_frame_bytes={})&quot;</code> |
| tests/test_bwrap.py:129 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;cpu_need&#x27;, need)&quot;</code> |
| tests/test_bwrap.py:130 | BEYOND | ∅ (added file) | <code>&quot;    T.need_command(NS(root=str(tmp_path), all=True, family=None, ids=None, first=None,&quot;</code> |
| tests/test_bwrap.py:131 | BEYOND | ∅ (added file) | <code>&quot;                      out=str(tmp_path/&#x27;need.txt&#x27;), bwrap=&#x27;/usr/bin/custom-bwrap&#x27;))&quot;</code> |
| tests/test_bwrap.py:132 | BEYOND | ∅ (added file) | <code>&quot;    assert len(calls) == 3 and all(c[-2:] == (&#x27;/usr/bin/custom-bwrap&#x27;, True) for c in calls)&quot;</code> |
| REPORT_BWRAP.md:1 | BEYOND | ∅ (added file) | <code>&quot;proof, read, need, and selfcheck accept --bwrap PATH, default /usr/bin/bwrap; the pinned Orchard binary never executes.&quot;</code> |
| REPORT_BWRAP.md:2 | BEYOND | ∅ (added file) | <code>&quot;COMMAND.json/EXIT.json/PROOF.json and CPU/selfcheck evidence record the executed path, SHA256, and exact --version output.&quot;</code> |
| REPORT_BWRAP.md:3 | BEYOND | ∅ (added file) | <code>&quot;Executed host: /usr/bin/bwrap, bubblewrap 0.4.0; SHA256 e60f175f82b2d6779a543ba52152f636f6260d092e44b195713f7650fb7bed76.&quot;</code> |
| REPORT_BWRAP.md:4 | BEYOND | ∅ (added file) | <code>&quot;Every emitted flag is listed by 0.4.0 and included in the CPU true probe; no substitutions were needed (BWRAP_FLAGS.json).&quot;</code> |
| REPORT_BWRAP.md:5 | BEYOND | ∅ (added file) | <code>&quot;Tests: 76 passed in 9.24 s; see TESTS_BWRAP_FINAL.log. DIFF.md marks selection PATH/ENV and evidence/classification BEYOND.&quot;</code> |
| REPORT_BWRAP.md:6 | BEYOND | ∅ (added file) | <code>&quot;Real-root selfcheck exited 2: CONFIG passed with 153 pinned_evidence findings and eight root-backed aliases; integrity checks passed.&quot;</code> |
| REPORT_BWRAP.md:7 | BEYOND | ∅ (added file) | <code>&quot;Missing: base, reader_payload, runtime_0, runtime_1, runtime_2; a0 lacks its member inventory (SELF_CHECK_BWRAP.json).&quot;</code> |
| REPORT_BWRAP.md:8 | BEYOND | ∅ (added file) | <code>&quot;The probe exited 1: bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted. This sandbox blocks namespace execution.&quot;</code> |
| REPORT_BWRAP.md:9 | BEYOND | ∅ (added file) | <code>&quot;STAGING/pinned files are unchanged; root/trinity_runner is updated. No tar wait, staging, kit edit, SSH, network access, Git, or GPU work ran.&quot;</code> |
| tests/test_llguidance.py:1 | BEYOND | ∅ (added file) | <code>&quot;import json&quot;</code> |
| tests/test_llguidance.py:2 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/test_llguidance.py:3 | BEYOND | ∅ (added file) | <code>&quot;import subprocess&quot;</code> |
| tests/test_llguidance.py:4 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/test_llguidance.py:5 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace as NS&quot;</code> |
| tests/test_llguidance.py:6 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:7 | BEYOND | ∅ (added file) | <code>&quot;import pytest&quot;</code> |
| tests/test_llguidance.py:8 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| tests/test_llguidance.py:9 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:10 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:11 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;gpu&#x27;, [False, True])&quot;</code> |
| tests/test_llguidance.py:12 | BEYOND | ∅ (added file) | <code>&quot;def test_overlay_is_pinned_and_bound_after_root(tmp_path, gpu):&quot;</code> |
| tests/test_llguidance.py:13 | BEYOND | ∅ (added file) | <code>&quot;    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)&quot;</code> |
| tests/test_llguidance.py:14 | BEYOND | ∅ (added file) | <code>&quot;    evidence = T.llguidance_evidence()&quot;</code> |
| tests/test_llguidance.py:15 | BEYOND | ∅ (added file) | <code>&quot;    assert evidence[&#x27;verified&#x27;] and evidence[&#x27;sha256&#x27;] == T.LLG_PINS&quot;</code> |
| tests/test_llguidance.py:16 | BEYOND | ∅ (added file) | <code>&quot;    argv = T.namespace(tmp_path, gpu=gpu)&quot;</code> |
| tests/test_llguidance.py:17 | BEYOND | ∅ (added file) | <code>&quot;    at = argv.index(str(T.LLG_STUB))&quot;</code> |
| tests/test_llguidance.py:18 | BEYOND | ∅ (added file) | <code>&quot;    assert argv[at-1:at+2] == [&#x27;--ro-bind&#x27;, str(T.LLG_STUB), str(T.LLG_TARGET)]&quot;</code> |
| tests/test_llguidance.py:19 | BEYOND | ∅ (added file) | <code>&quot;    assert at &gt; argv.index(str(tmp_path/&#x27;m/ap&#x27;))&quot;</code> |
| tests/test_llguidance.py:20 | BEYOND | ∅ (added file) | <code>&quot;    assert at &gt; argv.index(str(tmp_path), argv.index(str(tmp_path/&#x27;m/ap&#x27;)))&quot;</code> |
| tests/test_llguidance.py:21 | BEYOND | ∅ (added file) | <code>&quot;    disabled = T.namespace(tmp_path, gpu=gpu, llguidance_stub=False)&quot;</code> |
| tests/test_llguidance.py:22 | BEYOND | ∅ (added file) | <code>&quot;    assert str(T.LLG_STUB) not in disabled and str(T.LLG_TARGET) not in disabled&quot;</code> |
| tests/test_llguidance.py:23 | BEYOND | ∅ (added file) | <code>&quot;    if not gpu:&quot;</code> |
| tests/test_llguidance.py:24 | BEYOND | ∅ (added file) | <code>&quot;        assert &#x27;--dev-bind&#x27; not in argv and &#x27;--dev&#x27; in argv&quot;</code> |
| tests/test_llguidance.py:25 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:26 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:27 | BEYOND | ∅ (added file) | <code>&quot;def test_missing_overlay_target_refuses_without_creating_it(tmp_path):&quot;</code> |
| tests/test_llguidance.py:28 | BEYOND | ∅ (added file) | <code>&quot;    target = T.physical(tmp_path, T.LLG_TARGET)&quot;</code> |
| tests/test_llguidance.py:29 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;requires an existing staged directory&#x27;):&quot;</code> |
| tests/test_llguidance.py:30 | BEYOND | ∅ (added file) | <code>&quot;        T.namespace(tmp_path)&quot;</code> |
| tests/test_llguidance.py:31 | BEYOND | ∅ (added file) | <code>&quot;    assert not target.exists()&quot;</code> |
| tests/test_llguidance.py:32 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:33 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:34 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;name&#x27;, sorted(T.LLG_PINS))&quot;</code> |
| tests/test_llguidance.py:35 | BEYOND | ∅ (added file) | <code>&quot;def test_pin_mismatch_refuses_before_binding(tmp_path, monkeypatch, name):&quot;</code> |
| tests/test_llguidance.py:36 | BEYOND | ∅ (added file) | <code>&quot;    stub = tmp_path/&#x27;llguidance&#x27;; stub.mkdir()&quot;</code> |
| tests/test_llguidance.py:37 | BEYOND | ∅ (added file) | <code>&quot;    for filename in T.LLG_PINS:&quot;</code> |
| tests/test_llguidance.py:38 | BEYOND | ∅ (added file) | <code>&quot;        (stub/filename).write_bytes((T.LLG_STUB/filename).read_bytes())&quot;</code> |
| tests/test_llguidance.py:39 | BEYOND | ∅ (added file) | <code>&quot;    (stub/name).write_text(&#x27;# mismatched stub\\n&#x27;)&quot;</code> |
| tests/test_llguidance.py:40 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;LLG_STUB&#x27;, stub)&quot;</code> |
| tests/test_llguidance.py:41 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;bwrap_path&#x27;, lambda *a: pytest.fail(&#x27;Reached bwrap with bad stub&#x27;))&quot;</code> |
| tests/test_llguidance.py:42 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;llguidance stub pin mismatch&#x27;):&quot;</code> |
| tests/test_llguidance.py:43 | BEYOND | ∅ (added file) | <code>&quot;        T.namespace(tmp_path)&quot;</code> |
| tests/test_llguidance.py:44 | BEYOND | ∅ (added file) | <code>&quot;    assert T.llguidance_evidence(False)[&#x27;verified&#x27;] is False&quot;</code> |
| tests/test_llguidance.py:45 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:46 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:47 | BEYOND | ∅ (added file) | <code>&quot;def test_extra_stub_file_refuses(tmp_path, monkeypatch):&quot;</code> |
| tests/test_llguidance.py:48 | BEYOND | ∅ (added file) | <code>&quot;    stub = tmp_path/&#x27;llguidance&#x27;; stub.mkdir()&quot;</code> |
| tests/test_llguidance.py:49 | BEYOND | ∅ (added file) | <code>&quot;    for name in T.LLG_PINS:&quot;</code> |
| tests/test_llguidance.py:50 | BEYOND | ∅ (added file) | <code>&quot;        (stub/name).write_bytes((T.LLG_STUB/name).read_bytes())&quot;</code> |
| tests/test_llguidance.py:51 | BEYOND | ∅ (added file) | <code>&quot;    (stub/&#x27;extra.py&#x27;).write_text(&#x27;&#x27;)&quot;</code> |
| tests/test_llguidance.py:52 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;LLG_STUB&#x27;, stub)&quot;</code> |
| tests/test_llguidance.py:53 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;inventory differs&#x27;): T.namespace(tmp_path)&quot;</code> |
| tests/test_llguidance.py:54 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:55 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:56 | BEYOND | ∅ (added file) | <code>&quot;def test_config_audit_authenticates_host_overlay(tmp_path, monkeypatch):&quot;</code> |
| tests/test_llguidance.py:57 | BEYOND | ∅ (added file) | <code>&quot;    overlay = T.llguidance_evidence()&quot;</code> |
| tests/test_llguidance.py:58 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;runs/fixture/CONFIG.json&#x27;, dict(spec=dict(llguidance_stub=overlay)))&quot;</code> |
| tests/test_llguidance.py:59 | BEYOND | ∅ (added file) | <code>&quot;    audit = T.config_audit(tmp_path)&quot;</code> |
| tests/test_llguidance.py:60 | BEYOND | ∅ (added file) | <code>&quot;    assert audit[&#x27;passed&#x27;]&quot;</code> |
| tests/test_llguidance.py:61 | BEYOND | ∅ (added file) | <code>&quot;    assert any(r[&#x27;kind&#x27;] == &#x27;pinned_overlay&#x27; for r in audit[&#x27;findings&#x27;])&quot;</code> |
| tests/test_llguidance.py:62 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;LLG_PINS&#x27;, dict(T.LLG_PINS, **{&#x27;hf.py&#x27;: &#x27;0&#x27;*64}))&quot;</code> |
| tests/test_llguidance.py:63 | BEYOND | ∅ (added file) | <code>&quot;    assert not T.config_audit(tmp_path)[&#x27;passed&#x27;]&quot;</code> |
| tests/test_llguidance.py:64 | BEYOND | ∅ (added file) | <code>&quot;    overlay[&#x27;enabled&#x27;] = False&quot;</code> |
| tests/test_llguidance.py:65 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;runs/fixture/CONFIG.json&#x27;, dict(spec=dict(llguidance_stub=overlay)))&quot;</code> |
| tests/test_llguidance.py:66 | BEYOND | ∅ (added file) | <code>&quot;    assert T.config_audit(tmp_path)[&#x27;passed&#x27;]&quot;</code> |
| tests/test_llguidance.py:67 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:68 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:69 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;command&#x27;, [&#x27;proof&#x27;, &#x27;read&#x27;, &#x27;need&#x27;, &#x27;probe&#x27;])&quot;</code> |
| tests/test_llguidance.py:70 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;enabled&#x27;, [True, False])&quot;</code> |
| tests/test_llguidance.py:71 | BEYOND | ∅ (added file) | <code>&quot;def test_cli_overlay_selection(tmp_path, monkeypatch, command, enabled):&quot;</code> |
| tests/test_llguidance.py:72 | BEYOND | ∅ (added file) | <code>&quot;    argv = [&#x27;trinity_read.py&#x27;, command, &#x27;--root&#x27;, str(tmp_path)]&quot;</code> |
| tests/test_llguidance.py:73 | BEYOND | ∅ (added file) | <code>&quot;    if not enabled: argv.append(&#x27;--no-llguidance-stub&#x27;)&quot;</code> |
| tests/test_llguidance.py:74 | BEYOND | ∅ (added file) | <code>&quot;    if command in (&#x27;proof&#x27;, &#x27;read&#x27;): argv += [&#x27;--gpu&#x27;, &#x27;0&#x27;, &#x27;--token&#x27;, &#x27;p12345678&#x27;]&quot;</code> |
| tests/test_llguidance.py:75 | BEYOND | ∅ (added file) | <code>&quot;    if command in (&#x27;need&#x27;, &#x27;read&#x27;): argv += [&#x27;--family&#x27;, &#x27;main&#x27;, &#x27;--first&#x27;, &#x27;1&#x27;, &#x27;--out&#x27;, str(tmp_path/&#x27;packet&#x27;)]&quot;</code> |
| tests/test_llguidance.py:76 | BEYOND | ∅ (added file) | <code>&quot;    if command == &#x27;read&#x27;: argv += [&#x27;--artifact&#x27;, &#x27;fixture&#x27;, &#x27;--sha256&#x27;, &#x27;a&#x27;*64, &#x27;--step&#x27;, &#x27;544&#x27;]&quot;</code> |
| tests/test_llguidance.py:77 | BEYOND | ∅ (added file) | <code>&quot;    seen = []&quot;</code> |
| tests/test_llguidance.py:78 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(sys, &#x27;argv&#x27;, argv)&quot;</code> |
| tests/test_llguidance.py:79 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;launch&#x27;, lambda args: seen.append(args.llguidance_stub))&quot;</code> |
| tests/test_llguidance.py:80 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;need_command&#x27;, lambda args: seen.append(args.llguidance_stub))&quot;</code> |
| tests/test_llguidance.py:81 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;probe&#x27;, lambda *args: seen.append(args[-1]))&quot;</code> |
| tests/test_llguidance.py:82 | BEYOND | ∅ (added file) | <code>&quot;    T.main()&quot;</code> |
| tests/test_llguidance.py:83 | BEYOND | ∅ (added file) | <code>&quot;    assert seen == [enabled]&quot;</code> |
| tests/test_llguidance.py:84 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:85 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:86 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;enabled&#x27;, [True, False])&quot;</code> |
| tests/test_llguidance.py:87 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;code&#x27;, [0, 7])&quot;</code> |
| tests/test_llguidance.py:88 | BEYOND | ∅ (added file) | <code>&quot;def test_need_evidence_on_success_or_failure(tmp_path, monkeypatch, enabled, code):&quot;</code> |
| tests/test_llguidance.py:89 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;require_stage&#x27;, lambda root: {})&quot;</code> |
| tests/test_llguidance.py:90 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;install_runner&#x27;, lambda root: None)&quot;</code> |
| tests/test_llguidance.py:91 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;bwrap_evidence&#x27;, lambda *a: dict(path=&#x27;/usr/bin/bwrap&#x27;))&quot;</code> |
| tests/test_llguidance.py:92 | BEYOND | ∅ (added file) | <code>&quot;    def command(root, config, script, args, **kwargs):&quot;</code> |
| tests/test_llguidance.py:93 | BEYOND | ∅ (added file) | <code>&quot;        assert kwargs[&#x27;llguidance_stub&#x27;] == enabled&quot;</code> |
| tests/test_llguidance.py:94 | BEYOND | ∅ (added file) | <code>&quot;        work = Path(args[1]).parent&quot;</code> |
| tests/test_llguidance.py:95 | BEYOND | ∅ (added file) | <code>&quot;        T.dump(work/&#x27;NEED.json&#x27;, dict(need=[], ids=[]))&quot;</code> |
| tests/test_llguidance.py:96 | BEYOND | ∅ (added file) | <code>&quot;        return [&#x27;fixture&#x27;]&quot;</code> |
| tests/test_llguidance.py:97 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;ns_command&#x27;, command)&quot;</code> |
| tests/test_llguidance.py:98 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;run&#x27;, lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, code))&quot;</code> |
| tests/test_llguidance.py:99 | BEYOND | ∅ (added file) | <code>&quot;    if code:&quot;</code> |
| tests/test_llguidance.py:100 | BEYOND | ∅ (added file) | <code>&quot;        with pytest.raises(subprocess.CalledProcessError): T.cpu_need(tmp_path, &#x27;main&#x27;, llguidance_stub=enabled)&quot;</code> |
| tests/test_llguidance.py:101 | BEYOND | ∅ (added file) | <code>&quot;    else:&quot;</code> |
| tests/test_llguidance.py:102 | BEYOND | ∅ (added file) | <code>&quot;        assert T.cpu_need(tmp_path, &#x27;main&#x27;, llguidance_stub=enabled)[&#x27;llguidance_stub&#x27;] == T.llguidance_evidence(enabled)&quot;</code> |
| tests/test_llguidance.py:103 | BEYOND | ∅ (added file) | <code>&quot;    work = next((tmp_path/&#x27;needs&#x27;).iterdir())&quot;</code> |
| tests/test_llguidance.py:104 | BEYOND | ∅ (added file) | <code>&quot;    for name in (&#x27;COMMAND.json&#x27;, &#x27;EXIT.json&#x27;):&quot;</code> |
| tests/test_llguidance.py:105 | BEYOND | ∅ (added file) | <code>&quot;        assert T.load(work/name)[&#x27;llguidance_stub&#x27;] == T.llguidance_evidence(enabled)&quot;</code> |
| tests/test_llguidance.py:106 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:107 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:108 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;state&#x27;, [{}, {&#x27;status&#x27;: &#x27;partial&#x27;}, {&#x27;status&#x27;: &#x27;complete&#x27;}])&quot;</code> |
| tests/test_llguidance.py:109 | BEYOND | ∅ (added file) | <code>&quot;def test_probe_refuses_missing_uv_python_and_retains_report(tmp_path, monkeypatch, state):&quot;</code> |
| tests/test_llguidance.py:110 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;STAGING.json&#x27;, dict(pieces={&#x27;runtime_0&#x27;: state}))&quot;</code> |
| tests/test_llguidance.py:111 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;capture_command&#x27;, lambda argv: dict(argv=argv, stdout=&#x27;&#x27;, returncode=None))&quot;</code> |
| tests/test_llguidance.py:112 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;run&#x27;, lambda *a, **k: pytest.fail(&#x27;Ran without runtime_0&#x27;))&quot;</code> |
| tests/test_llguidance.py:113 | BEYOND | ∅ (added file) | <code>&quot;    with pytest.raises(ValueError, match=&#x27;requires runtime_0 staged&#x27;):&quot;</code> |
| tests/test_llguidance.py:114 | BEYOND | ∅ (added file) | <code>&quot;        T.probe(tmp_path)&quot;</code> |
| tests/test_llguidance.py:115 | BEYOND | ∅ (added file) | <code>&quot;    report = T.load(next((tmp_path/&#x27;runs&#x27;).glob(&#x27;probe_*/PROBE.json&#x27;)))&quot;</code> |
| tests/test_llguidance.py:116 | BEYOND | ∅ (added file) | <code>&quot;    assert not report[&#x27;passed&#x27;] and report[&#x27;returncode&#x27;] is None&quot;</code> |
| tests/test_llguidance.py:117 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;cryptography_imported&#x27;] is None&quot;</code> |
| tests/test_llguidance.py:118 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:119 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:120 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;enabled&#x27;, [True, False])&quot;</code> |
| tests/test_llguidance.py:121 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;outcome&#x27;, [&#x27;success&#x27;, &#x27;imports_failed&#x27;, &#x27;namespace_failed&#x27;, &#x27;timeout&#x27;])&quot;</code> |
| tests/test_llguidance.py:122 | BEYOND | ∅ (added file) | <code>&quot;def test_probe_namespace_and_evidence(tmp_path, monkeypatch, enabled, outcome):&quot;</code> |
| tests/test_llguidance.py:123 | BEYOND | ∅ (added file) | <code>&quot;    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)&quot;</code> |
| tests/test_llguidance.py:124 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;STAGING.json&#x27;, dict(complete=False, pieces={&#x27;runtime_0&#x27;: dict(status=&#x27;complete&#x27;)}))&quot;</code> |
| tests/test_llguidance.py:125 | BEYOND | ∅ (added file) | <code>&quot;    uv = tmp_path/&#x27;sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12&#x27;&quot;</code> |
| tests/test_llguidance.py:126 | BEYOND | ∅ (added file) | <code>&quot;    uv.parent.mkdir(parents=True); uv.write_bytes(b&#x27;fixture&#x27;)&quot;</code> |
| tests/test_llguidance.py:127 | BEYOND | ∅ (added file) | <code>&quot;    python = T.physical(tmp_path, T.VLLM_ENV/&#x27;bin/python&#x27;)&quot;</code> |
| tests/test_llguidance.py:128 | BEYOND | ∅ (added file) | <code>&quot;    python.parent.mkdir(parents=True); python.symlink_to(T.UV+&#x27;/bin/python3.12&#x27;)&quot;</code> |
| tests/test_llguidance.py:129 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;bwrap_evidence&#x27;, lambda *a: dict(path=&#x27;/usr/bin/bwrap&#x27;))&quot;</code> |
| tests/test_llguidance.py:130 | BEYOND | ∅ (added file) | <code>&quot;    custom_shm = tmp_path/&#x27;private-shm&#x27;&quot;</code> |
| tests/test_llguidance.py:131 | BEYOND | ∅ (added file) | <code>&quot;    imports = dict(versions=dict(vllm=&#x27;0.32.0&#x27;, torch=&#x27;fixture&#x27;, transformers=&#x27;fixture&#x27;),&quot;</code> |
| tests/test_llguidance.py:132 | BEYOND | ∅ (added file) | <code>&quot;                   glibc=&#x27;glibc 2.28&#x27;, imports_passed=outcome == &#x27;success&#x27;, cryptography_imported=False,&quot;</code> |
| tests/test_llguidance.py:133 | BEYOND | ∅ (added file) | <code>&quot;                   structured_output=dict(stub_runtime_error=True))&quot;</code> |
| tests/test_llguidance.py:134 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;capture_command&#x27;, lambda argv: dict(argv=argv, stdout=&#x27;&#x27;, returncode=None))&quot;</code> |
| tests/test_llguidance.py:135 | BEYOND | ∅ (added file) | <code>&quot;    def run(command, **kwargs):&quot;</code> |
| tests/test_llguidance.py:136 | BEYOND | ∅ (added file) | <code>&quot;        assert &#x27;--dev-bind&#x27; not in command and &#x27;--dev&#x27; in command&quot;</code> |
| tests/test_llguidance.py:137 | BEYOND | ∅ (added file) | <code>&quot;        assert command == T.namespace(tmp_path, shm=custom_shm, llguidance_stub=enabled) + [str(T.VLLM_ENV/&#x27;bin/python&#x27;), &#x27;-I&#x27;, &#x27;-B&#x27;, &#x27;-c&#x27;, T.PROBE_CODE]&quot;</code> |
| tests/test_llguidance.py:138 | BEYOND | ∅ (added file) | <code>&quot;        env = T.environment(tmp_path, shm=custom_shm)&quot;</code> |
| tests/test_llguidance.py:139 | BEYOND | ∅ (added file) | <code>&quot;        env[&#x27;LLG_STUB_LOG&#x27;] = kwargs[&#x27;env&#x27;][&#x27;LLG_STUB_LOG&#x27;]&quot;</code> |
| tests/test_llguidance.py:140 | BEYOND | ∅ (added file) | <code>&quot;        assert kwargs[&#x27;env&#x27;] == env&quot;</code> |
| tests/test_llguidance.py:141 | BEYOND | ∅ (added file) | <code>&quot;        Path(env[&#x27;LLG_STUB_LOG&#x27;]).write_text(json.dumps(dict(event=&#x27;import&#x27;, module=&#x27;llguidance&#x27;, pid=1))+&#x27;\\n&#x27;+json.dumps(dict(event=&#x27;call&#x27;, name=&#x27;llguidance.grammar_from&#x27;))+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_llguidance.py:142 | BEYOND | ∅ (added file) | <code>&quot;        assert kwargs[&#x27;env&#x27;][&#x27;CUDA_VISIBLE_DEVICES&#x27;] == &#x27;&#x27;&quot;</code> |
| tests/test_llguidance.py:143 | BEYOND | ∅ (added file) | <code>&quot;        if outcome == &#x27;timeout&#x27;: raise subprocess.TimeoutExpired(command, 120)&quot;</code> |
| tests/test_llguidance.py:144 | BEYOND | ∅ (added file) | <code>&quot;        stdout = &#x27;&#x27; if outcome == &#x27;namespace_failed&#x27; else T.PROBE_MARKER+json.dumps(imports)+&#x27;\\n&#x27;&quot;</code> |
| tests/test_llguidance.py:145 | BEYOND | ∅ (added file) | <code>&quot;        return subprocess.CompletedProcess(command, 0 if outcome == &#x27;success&#x27; else 1, stdout, &#x27;fixture stderr&#x27;)&quot;</code> |
| tests/test_llguidance.py:146 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T.subprocess, &#x27;run&#x27;, run)&quot;</code> |
| tests/test_llguidance.py:147 | BEYOND | ∅ (added file) | <code>&quot;    if outcome == &#x27;success&#x27;:&quot;</code> |
| tests/test_llguidance.py:148 | BEYOND | ∅ (added file) | <code>&quot;        result = T.probe(tmp_path, shm=custom_shm, llguidance_stub=enabled)&quot;</code> |
| tests/test_llguidance.py:149 | BEYOND | ∅ (added file) | <code>&quot;        assert result[&#x27;passed&#x27;] and result[&#x27;glibc&#x27;] == &#x27;glibc 2.28&#x27;&quot;</code> |
| tests/test_llguidance.py:150 | BEYOND | ∅ (added file) | <code>&quot;    else:&quot;</code> |
| tests/test_llguidance.py:151 | BEYOND | ∅ (added file) | <code>&quot;        with pytest.raises((RuntimeError, subprocess.TimeoutExpired)):&quot;</code> |
| tests/test_llguidance.py:152 | BEYOND | ∅ (added file) | <code>&quot;            T.probe(tmp_path, shm=custom_shm, llguidance_stub=enabled)&quot;</code> |
| tests/test_llguidance.py:153 | BEYOND | ∅ (added file) | <code>&quot;    result = T.load(next((tmp_path/&#x27;runs&#x27;).glob(&#x27;probe_*/PROBE.json&#x27;)))&quot;</code> |
| tests/test_llguidance.py:154 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;llguidance_stub&#x27;] == T.llguidance_evidence(enabled)&quot;</code> |
| tests/test_llguidance.py:155 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;passed&#x27;] == (outcome == &#x27;success&#x27;)&quot;</code> |
| tests/test_llguidance.py:156 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;cryptography_imported&#x27;] is (None if outcome in (&#x27;namespace_failed&#x27;, &#x27;timeout&#x27;) else False)&quot;</code> |
| tests/test_llguidance.py:157 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:158 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llguidance.py:159 | BEYOND | ∅ (added file) | <code>&quot;def test_probe_code_reports_actual_loaded_modules(tmp_path):&quot;</code> |
| tests/test_llguidance.py:160 | BEYOND | ∅ (added file) | <code>&quot;    # Exercise the import script without importing any real GPU libraries.&quot;</code> |
| tests/test_llguidance.py:161 | BEYOND | ∅ (added file) | <code>&quot;    code = &#x27;&#x27;&#x27;&quot;</code> |
| tests/test_llguidance.py:162 | BEYOND | ∅ (added file) | <code>&quot;import sys, types&quot;</code> |
| tests/test_llguidance.py:163 | BEYOND | ∅ (added file) | <code>&quot;for name in (&#x27;vllm&#x27;, &#x27;torch&#x27;, &#x27;transformers&#x27;, &#x27;vllm.model_executor&#x27;, &#x27;vllm.model_executor.models&#x27;,&quot;</code> |
| tests/test_llguidance.py:164 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;vllm.v1&#x27;, &#x27;vllm.v1.engine&#x27;, &#x27;vllm.v1.engine.core&#x27;, &#x27;vllm.v1.worker&#x27;, &#x27;vllm.v1.worker.gpu_model_runner&#x27;):&quot;</code> |
| tests/test_llguidance.py:165 | BEYOND | ∅ (added file) | <code>&quot;    module = types.ModuleType(name); module.__version__ = &#x27;fixture&#x27;; module.__path__ = []&quot;</code> |
| tests/test_llguidance.py:166 | BEYOND | ∅ (added file) | <code>&quot;    sys.modules[name] = module&quot;</code> |
| tests/test_llguidance.py:167 | BEYOND | ∅ (added file) | <code>&quot;sys.modules[&#x27;vllm&#x27;].LLM = object&quot;</code> |
| tests/test_llguidance.py:168 | BEYOND | ∅ (added file) | <code>&quot;sys.modules[&#x27;vllm.model_executor.models&#x27;].qwen3_5 = object&quot;</code> |
| tests/test_llguidance.py:169 | BEYOND | ∅ (added file) | <code>&quot;sys.modules[&#x27;cryptography&#x27;] = types.ModuleType(&#x27;cryptography&#x27;)&quot;</code> |
| tests/test_llguidance.py:170 | BEYOND | ∅ (added file) | <code>&quot;&#x27;&#x27;&#x27;&quot;</code> |
| tests/test_llguidance.py:171 | BEYOND | ∅ (added file) | <code>&quot;    result = subprocess.run([sys.executable, &#x27;-I&#x27;, &#x27;-B&#x27;, &#x27;-c&#x27;, code+T.PROBE_CODE],&quot;</code> |
| tests/test_llguidance.py:172 | BEYOND | ∅ (added file) | <code>&quot;                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)&quot;</code> |
| tests/test_llguidance.py:173 | BEYOND | ∅ (added file) | <code>&quot;    assert result.returncode == 0, result.stderr&quot;</code> |
| tests/test_llguidance.py:174 | BEYOND | ∅ (added file) | <code>&quot;    record = json.loads(result.stdout.split(T.PROBE_MARKER)[1])&quot;</code> |
| tests/test_llguidance.py:175 | BEYOND | ∅ (added file) | <code>&quot;    assert record[&#x27;imports_passed&#x27;] and record[&#x27;cryptography_imported&#x27;]&quot;</code> |
| tests/test_llguidance.py:176 | BEYOND | ∅ (added file) | <code>&quot;    assert record[&#x27;versions&#x27;][&#x27;vllm&#x27;] == &#x27;fixture&#x27; and record[&#x27;glibc&#x27;].startswith(&#x27;glibc &#x27;)&quot;</code> |
| llg_stub/llguidance/__init__.py:1 | BEYOND | ∅ (added file) | <code>&quot;\&quot;\&quot;\&quot;Import-only llguidance overlay; every attempted guidance operation fails.\&quot;\&quot;\&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:2 | BEYOND | ∅ (added file) | <code>&quot;import json as _json&quot;</code> |
| llg_stub/llguidance/__init__.py:3 | BEYOND | ∅ (added file) | <code>&quot;import os as _os&quot;</code> |
| llg_stub/llguidance/__init__.py:4 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:5 | BEYOND | ∅ (added file) | <code>&quot;_MSG = &#x27;llguidance stub: guidance structured outputs are unavailable on this host (glibc 2.28)&#x27;&quot;</code> |
| llg_stub/llguidance/__init__.py:6 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:7 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:8 | BEYOND | ∅ (added file) | <code>&quot;def _record(event, **fields):&quot;</code> |
| llg_stub/llguidance/__init__.py:9 | BEYOND | ∅ (added file) | <code>&quot;    path = _os.environ.get(&#x27;LLG_STUB_LOG&#x27;) or _os.path.join(_os.environ.get(&#x27;TMPDIR&#x27;, &#x27;/tmp&#x27;), &#x27;llg_stub_calls.jsonl&#x27;)&quot;</code> |
| llg_stub/llguidance/__init__.py:10 | BEYOND | ∅ (added file) | <code>&quot;    data = (_json.dumps(dict(event=event, **fields), sort_keys=True) + &#x27;\\n&#x27;).encode()&quot;</code> |
| llg_stub/llguidance/__init__.py:11 | BEYOND | ∅ (added file) | <code>&quot;    fd = _os.open(path, _os.O_WRONLY | _os.O_CREAT | _os.O_APPEND, 0o600)&quot;</code> |
| llg_stub/llguidance/__init__.py:12 | BEYOND | ∅ (added file) | <code>&quot;    try:&quot;</code> |
| llg_stub/llguidance/__init__.py:13 | BEYOND | ∅ (added file) | <code>&quot;        if _os.write(fd, data) != len(data):&quot;</code> |
| llg_stub/llguidance/__init__.py:14 | BEYOND | ∅ (added file) | <code>&quot;            raise RuntimeError(&#x27;llguidance stub: incomplete audit write&#x27;)&quot;</code> |
| llg_stub/llguidance/__init__.py:15 | BEYOND | ∅ (added file) | <code>&quot;    finally:&quot;</code> |
| llg_stub/llguidance/__init__.py:16 | BEYOND | ∅ (added file) | <code>&quot;        _os.close(fd)&quot;</code> |
| llg_stub/llguidance/__init__.py:17 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:18 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:19 | BEYOND | ∅ (added file) | <code>&quot;def _fail(name):&quot;</code> |
| llg_stub/llguidance/__init__.py:20 | BEYOND | ∅ (added file) | <code>&quot;    _record(&#x27;call&#x27;, name=name)&quot;</code> |
| llg_stub/llguidance/__init__.py:21 | BEYOND | ∅ (added file) | <code>&quot;    raise RuntimeError(_MSG + &#x27; (&#x27; + name + &#x27;)&#x27;)&quot;</code> |
| llg_stub/llguidance/__init__.py:22 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:23 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:24 | BEYOND | ∅ (added file) | <code>&quot;_record(&#x27;import&#x27;, module=__name__, pid=_os.getpid())&quot;</code> |
| llg_stub/llguidance/__init__.py:25 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:26 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:27 | BEYOND | ∅ (added file) | <code>&quot;class _UnavailableMeta(type):&quot;</code> |
| llg_stub/llguidance/__init__.py:28 | BEYOND | ∅ (added file) | <code>&quot;    def __getattr__(cls, name):&quot;</code> |
| llg_stub/llguidance/__init__.py:29 | BEYOND | ∅ (added file) | <code>&quot;        _fail(cls.__name__ + &#x27;.&#x27; + name)&quot;</code> |
| llg_stub/llguidance/__init__.py:30 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:31 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:32 | BEYOND | ∅ (added file) | <code>&quot;class _Unavailable(metaclass=_UnavailableMeta):&quot;</code> |
| llg_stub/llguidance/__init__.py:33 | BEYOND | ∅ (added file) | <code>&quot;    def __init__(self, *args, **kwargs):&quot;</code> |
| llg_stub/llguidance/__init__.py:34 | BEYOND | ∅ (added file) | <code>&quot;        _fail(type(self).__name__)&quot;</code> |
| llg_stub/llguidance/__init__.py:35 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:36 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:37 | BEYOND | ∅ (added file) | <code>&quot;class LLMatcher(_Unavailable):&quot;</code> |
| llg_stub/llguidance/__init__.py:38 | BEYOND | ∅ (added file) | <code>&quot;    pass&quot;</code> |
| llg_stub/llguidance/__init__.py:39 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:40 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:41 | BEYOND | ∅ (added file) | <code>&quot;class LLTokenizer(_Unavailable):&quot;</code> |
| llg_stub/llguidance/__init__.py:42 | BEYOND | ∅ (added file) | <code>&quot;    pass&quot;</code> |
| llg_stub/llguidance/__init__.py:43 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:44 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:45 | BEYOND | ∅ (added file) | <code>&quot;class LLInterpreter(_Unavailable):&quot;</code> |
| llg_stub/llguidance/__init__.py:46 | BEYOND | ∅ (added file) | <code>&quot;    pass&quot;</code> |
| llg_stub/llguidance/__init__.py:47 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:48 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/__init__.py:49 | BEYOND | ∅ (added file) | <code>&quot;def __getattr__(name):&quot;</code> |
| llg_stub/llguidance/__init__.py:50 | BEYOND | ∅ (added file) | <code>&quot;    _fail(&#x27;llguidance.&#x27; + name)&quot;</code> |
| llg_stub/llguidance/hf.py:1 | BEYOND | ∅ (added file) | <code>&quot;from . import _record, _fail, _os&quot;</code> |
| llg_stub/llguidance/hf.py:2 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/hf.py:3 | BEYOND | ∅ (added file) | <code>&quot;_record(&#x27;import&#x27;, module=__name__, pid=_os.getpid())&quot;</code> |
| llg_stub/llguidance/hf.py:4 | BEYOND | ∅ (added file) | <code>&quot;_fail(__name__)&quot;</code> |
| llg_stub/llguidance/torch.py:1 | BEYOND | ∅ (added file) | <code>&quot;from . import _record, _fail, _os&quot;</code> |
| llg_stub/llguidance/torch.py:2 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| llg_stub/llguidance/torch.py:3 | BEYOND | ∅ (added file) | <code>&quot;_record(&#x27;import&#x27;, module=__name__, pid=_os.getpid())&quot;</code> |
| llg_stub/llguidance/torch.py:4 | BEYOND | ∅ (added file) | <code>&quot;_fail(__name__)&quot;</code> |
| REPORT_LLG.md:1 | BEYOND | ∅ (added file) | <code>&quot;proof/read/need/probe default to a pinned llguidance overlay; --no-llguidance-stub disables it.&quot;</code> |
| REPORT_LLG.md:2 | BEYOND | ∅ (added file) | <code>&quot;The three build stub files match the operator&#x27;s bytes; hashes and exact inventory are checked before the read-only bind.&quot;</code> |
| REPORT_LLG.md:3 | BEYOND | ∅ (added file) | <code>&quot;COMMAND/EXIT/PROOF, packet SPEC/CONFIG, and NEED evidence record the source path, target, hashes, and enablement.&quot;</code> |
| REPORT_LLG.md:4 | BEYOND | ∅ (added file) | <code>&quot;probe uses the staged vLLM Python with CPU-only devices and writes versions, glibc, and cryptography import presence to PROBE.json.&quot;</code> |
| REPORT_LLG.md:5 | BEYOND | ∅ (added file) | <code>&quot;Tests: 112 passed; see TESTS_LLG_FINAL.log. The suite covers argv, pin refusal, disablement, evidence, and probe failures.&quot;</code> |
| REPORT_LLG.md:6 | BEYOND | ∅ (added file) | <code>&quot;Real probe refused absent runtime_0; see ../root/runs/probe_20261116T043218.988773Z/PROBE.json. No runtime import success is claimed.&quot;</code> |
| REPORT_LLG.md:7 | BEYOND | ∅ (added file) | <code>&quot;Root wrapper modules match build; STAGING/bootstrap hashes are unchanged (LLG_PRESERVED.json); staged package bytes were not edited.&quot;</code> |
| REPORT_LLG.md:8 | BEYOND | ∅ (added file) | <code>&quot;DIFF marks the load-time overlay BEYOND for glibc 2.28; README documents its limits. No tar wait, staging, SSH, network, Git, or GPU ran.&quot;</code> |
| tests/test_llg2.py:1 | BEYOND | ∅ (added file) | <code>&quot;import ast&quot;</code> |
| tests/test_llg2.py:2 | BEYOND | ∅ (added file) | <code>&quot;import copy&quot;</code> |
| tests/test_llg2.py:3 | BEYOND | ∅ (added file) | <code>&quot;import json&quot;</code> |
| tests/test_llg2.py:4 | BEYOND | ∅ (added file) | <code>&quot;import os&quot;</code> |
| tests/test_llg2.py:5 | BEYOND | ∅ (added file) | <code>&quot;from pathlib import Path&quot;</code> |
| tests/test_llg2.py:6 | BEYOND | ∅ (added file) | <code>&quot;import subprocess&quot;</code> |
| tests/test_llg2.py:7 | BEYOND | ∅ (added file) | <code>&quot;import sys&quot;</code> |
| tests/test_llg2.py:8 | BEYOND | ∅ (added file) | <code>&quot;from types import SimpleNamespace as NS&quot;</code> |
| tests/test_llg2.py:9 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:10 | BEYOND | ∅ (added file) | <code>&quot;import pytest&quot;</code> |
| tests/test_llg2.py:11 | BEYOND | ∅ (added file) | <code>&quot;import trinity_read as T&quot;</code> |
| tests/test_llg2.py:12 | BEYOND | ∅ (added file) | <code>&quot;import compare_tokens as C&quot;</code> |
| tests/test_llg2.py:13 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:14 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:15 | BEYOND | ∅ (added file) | <code>&quot;def run_stub(tmp_path, code, default=False):&quot;</code> |
| tests/test_llg2.py:16 | BEYOND | ∅ (added file) | <code>&quot;    log = tmp_path/&#x27;llg_stub_calls.jsonl&#x27;&quot;</code> |
| tests/test_llg2.py:17 | BEYOND | ∅ (added file) | <code>&quot;    env = dict(os.environ, TMPDIR=str(tmp_path), PYTHONDONTWRITEBYTECODE=&#x27;1&#x27;)&quot;</code> |
| tests/test_llg2.py:18 | BEYOND | ∅ (added file) | <code>&quot;    env.pop(&#x27;LLG_STUB_LOG&#x27;, None)&quot;</code> |
| tests/test_llg2.py:19 | BEYOND | ∅ (added file) | <code>&quot;    if not default: env[&#x27;LLG_STUB_LOG&#x27;] = str(log)&quot;</code> |
| tests/test_llg2.py:20 | BEYOND | ∅ (added file) | <code>&quot;    prefix = &#x27;import sys; sys.path.insert(0, &#x27;+repr(str(T.LLG_STUB.parent))+&#x27;); import llguidance\\n&#x27;&quot;</code> |
| tests/test_llg2.py:21 | BEYOND | ∅ (added file) | <code>&quot;    p = subprocess.run([sys.executable, &#x27;-I&#x27;, &#x27;-B&#x27;, &#x27;-c&#x27;, prefix+code], env=env,&quot;</code> |
| tests/test_llg2.py:22 | BEYOND | ∅ (added file) | <code>&quot;                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)&quot;</code> |
| tests/test_llg2.py:23 | BEYOND | ∅ (added file) | <code>&quot;    return p, [json.loads(line) for line in log.read_text().splitlines()]&quot;</code> |
| tests/test_llg2.py:24 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:25 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:26 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;name&#x27;, [&#x27;LLMatcher&#x27;, &#x27;LLTokenizer&#x27;, &#x27;LLInterpreter&#x27;])&quot;</code> |
| tests/test_llg2.py:27 | BEYOND | ∅ (added file) | <code>&quot;def test_class_always_logs_before_raising(tmp_path, name):&quot;</code> |
| tests/test_llg2.py:28 | BEYOND | ∅ (added file) | <code>&quot;    p, rows = run_stub(tmp_path, &#x27;llguidance.&#x27;+name+&#x27;(None)&#x27;)&quot;</code> |
| tests/test_llg2.py:29 | BEYOND | ∅ (added file) | <code>&quot;    assert p.returncode != 0 and &#x27;RuntimeError: llguidance stub:&#x27; in p.stderr&quot;</code> |
| tests/test_llg2.py:30 | BEYOND | ∅ (added file) | <code>&quot;    assert rows[0][&#x27;event&#x27;] == &#x27;import&#x27; and rows[0][&#x27;module&#x27;] == &#x27;llguidance&#x27; and rows[0][&#x27;pid&#x27;] &gt; 0&quot;</code> |
| tests/test_llg2.py:31 | BEYOND | ∅ (added file) | <code>&quot;    assert rows[1] == dict(event=&#x27;call&#x27;, name=name)&quot;</code> |
| tests/test_llg2.py:32 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:33 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:34 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;code,name&#x27;, [(&#x27;llguidance.unknown&#x27;, &#x27;llguidance.unknown&#x27;),&quot;</code> |
| tests/test_llg2.py:35 | BEYOND | ∅ (added file) | <code>&quot;    (&#x27;llguidance.LLMatcher.grammar_from_json_schema({})&#x27;, &#x27;LLMatcher.grammar_from_json_schema&#x27;),&quot;</code> |
| tests/test_llg2.py:36 | BEYOND | ∅ (added file) | <code>&quot;    (&#x27;import llguidance.hf&#x27;, &#x27;llguidance.hf&#x27;), (&#x27;import llguidance.torch&#x27;, &#x27;llguidance.torch&#x27;)])&quot;</code> |
| tests/test_llg2.py:37 | BEYOND | ∅ (added file) | <code>&quot;def test_other_guidance_use_raises_and_logs(tmp_path, code, name):&quot;</code> |
| tests/test_llg2.py:38 | BEYOND | ∅ (added file) | <code>&quot;    p, rows = run_stub(tmp_path, code, default=True)&quot;</code> |
| tests/test_llg2.py:39 | BEYOND | ∅ (added file) | <code>&quot;    assert p.returncode and &#x27;RuntimeError: llguidance stub:&#x27; in p.stderr&quot;</code> |
| tests/test_llg2.py:40 | BEYOND | ∅ (added file) | <code>&quot;    assert rows[-1] == dict(event=&#x27;call&#x27;, name=name)&quot;</code> |
| tests/test_llg2.py:41 | BEYOND | ∅ (added file) | <code>&quot;    if name in (&#x27;llguidance.hf&#x27;, &#x27;llguidance.torch&#x27;):&quot;</code> |
| tests/test_llg2.py:42 | BEYOND | ∅ (added file) | <code>&quot;        assert rows[-2][&#x27;event&#x27;] == &#x27;import&#x27; and rows[-2][&#x27;module&#x27;] == name&quot;</code> |
| tests/test_llg2.py:43 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:44 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:45 | BEYOND | ∅ (added file) | <code>&quot;def test_import_only_and_concurrent_log(tmp_path):&quot;</code> |
| tests/test_llg2.py:46 | BEYOND | ∅ (added file) | <code>&quot;    log = tmp_path/&#x27;shared.jsonl&#x27;&quot;</code> |
| tests/test_llg2.py:47 | BEYOND | ∅ (added file) | <code>&quot;    code = &#x27;import sys; sys.path.insert(0, &#x27;+repr(str(T.LLG_STUB.parent))+&#x27;); import llguidance&#x27;&quot;</code> |
| tests/test_llg2.py:48 | BEYOND | ∅ (added file) | <code>&quot;    children = [subprocess.Popen([sys.executable, &#x27;-I&#x27;, &#x27;-B&#x27;, &#x27;-c&#x27;, code], env=dict(os.environ, LLG_STUB_LOG=str(log))) for _ in range(4)]&quot;</code> |
| tests/test_llg2.py:49 | BEYOND | ∅ (added file) | <code>&quot;    assert [p.wait(timeout=20) for p in children] == [0]*4&quot;</code> |
| tests/test_llg2.py:50 | BEYOND | ∅ (added file) | <code>&quot;    usage = T.stub_usage(log)&quot;</code> |
| tests/test_llg2.py:51 | BEYOND | ∅ (added file) | <code>&quot;    assert usage[&#x27;passed&#x27;] and usage[&#x27;import_events_count&#x27;] == 4 and usage[&#x27;call_events_count&#x27;] == 0&quot;</code> |
| tests/test_llg2.py:52 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:53 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:54 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;contents&#x27;, [&#x27;&#x27;, &#x27;{bad\\n&#x27;, &#x27;{\&quot;event\&quot;:\&quot;call\&quot;,\&quot;name\&quot;:\&quot;LLMatcher\&quot;}\\n&#x27;])&quot;</code> |
| tests/test_llg2.py:55 | BEYOND | ∅ (added file) | <code>&quot;def test_audit_fails_closed(tmp_path, contents):&quot;</code> |
| tests/test_llg2.py:56 | BEYOND | ∅ (added file) | <code>&quot;    path = tmp_path/&#x27;calls&#x27;; path.write_text(contents)&quot;</code> |
| tests/test_llg2.py:57 | BEYOND | ∅ (added file) | <code>&quot;    assert not T.stub_usage(path)[&#x27;passed&#x27;]&quot;</code> |
| tests/test_llg2.py:58 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:59 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:60 | BEYOND | ∅ (added file) | <code>&quot;def test_sandbox_receipt_captures_all_binds(tmp_path, monkeypatch):&quot;</code> |
| tests/test_llg2.py:61 | BEYOND | ∅ (added file) | <code>&quot;    T.physical(tmp_path, T.LLG_TARGET).mkdir(parents=True)&quot;</code> |
| tests/test_llg2.py:62 | BEYOND | ∅ (added file) | <code>&quot;    command = T.namespace(tmp_path, gpu=True)&quot;</code> |
| tests/test_llg2.py:63 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T, &#x27;capture_command&#x27;, lambda argv: dict(argv=argv, stdout=&#x27;glibc fixture\\n&#x27; if argv[0]==&#x27;ldd&#x27; else &#x27;driver fixture\\n&#x27;, returncode=0))&quot;</code> |
| tests/test_llg2.py:64 | BEYOND | ∅ (added file) | <code>&quot;    p = dict(versions=dict(python=&#x27;3.12&#x27;, vllm=&#x27;0.32&#x27;, torch=&#x27;2&#x27;, transformers=&#x27;5&#x27;), glibc=&#x27;glibc 2.28&#x27;,&quot;</code> |
| tests/test_llg2.py:65 | BEYOND | ∅ (added file) | <code>&quot;             imports=dict(driver_resolution=[dict(name=&#x27;libcuda.so.1&#x27;, paths=[])]), passed=True)&quot;</code> |
| tests/test_llg2.py:66 | BEYOND | ∅ (added file) | <code>&quot;    result = T.sandbox_receipt(command, dict(path=command[0],sha256=&#x27;fixture&#x27;,version=&#x27;0.4&#x27;), T.llguidance_evidence(), p)&quot;</code> |
| tests/test_llg2.py:67 | BEYOND | ∅ (added file) | <code>&quot;    expected = [(command[i+1],command[i+2], &#x27;ro&#x27; if arg==&#x27;--ro-bind&#x27; else &#x27;rw&#x27;) for i,arg in enumerate(command) if arg in (&#x27;--ro-bind&#x27;,&#x27;--bind&#x27;,&#x27;--dev-bind&#x27;)]&quot;</code> |
| tests/test_llg2.py:68 | BEYOND | ∅ (added file) | <code>&quot;    assert [(b[&#x27;source&#x27;],b[&#x27;target&#x27;],b[&#x27;mode&#x27;]) for b in result[&#x27;binds&#x27;]] == expected&quot;</code> |
| tests/test_llg2.py:69 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;host_glibc&#x27;] == &#x27;glibc fixture&#x27; and result[&#x27;namespace_glibc&#x27;] == p[&#x27;glibc&#x27;]&quot;</code> |
| tests/test_llg2.py:70 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;versions&#x27;] == p[&#x27;versions&#x27;] and result[&#x27;llguidance_stub&#x27;][&#x27;sha256&#x27;] == T.LLG_PINS&quot;</code> |
| tests/test_llg2.py:71 | BEYOND | ∅ (added file) | <code>&quot;    assert [p[&#x27;path&#x27;] for p in result[&#x27;host_driver_libraries&#x27;]] == [&#x27;/usr/lib64/libcuda.so.1&#x27;,&#x27;/usr/lib64/libnvidia-ml.so.1&#x27;]&quot;</code> |
| tests/test_llg2.py:72 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:73 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:74 | BEYOND | ∅ (added file) | <code>&quot;def test_probe_executes_installed_compile_method_fixture(tmp_path):&quot;</code> |
| tests/test_llg2.py:75 | BEYOND | ∅ (added file) | <code>&quot;    # Exercise the installed method&#x27;s exact source with import fixtures; this is not a real namespace probe.&quot;</code> |
| tests/test_llg2.py:76 | BEYOND | ∅ (added file) | <code>&quot;    source = T.physical(T.DEFAULT_ROOT, T.VLLM_ENV/&#x27;lib/python3.12/site-packages/vllm/v1/structured_output/backend_guidance.py&#x27;)&quot;</code> |
| tests/test_llg2.py:77 | BEYOND | ∅ (added file) | <code>&quot;    tree = ast.parse(source.read_text())&quot;</code> |
| tests/test_llg2.py:78 | BEYOND | ∅ (added file) | <code>&quot;    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == &#x27;GuidanceBackend&#x27;)&quot;</code> |
| tests/test_llg2.py:79 | BEYOND | ∅ (added file) | <code>&quot;    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == &#x27;compile_grammar&#x27;)&quot;</code> |
| tests/test_llg2.py:80 | BEYOND | ∅ (added file) | <code>&quot;    serialize = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == &#x27;serialize_guidance_grammar&#x27;)&quot;</code> |
| tests/test_llg2.py:81 | BEYOND | ∅ (added file) | <code>&quot;    lines = source.read_text().splitlines()&quot;</code> |
| tests/test_llg2.py:82 | BEYOND | ∅ (added file) | <code>&quot;    import textwrap&quot;</code> |
| tests/test_llg2.py:83 | BEYOND | ∅ (added file) | <code>&quot;    method_source = textwrap.dedent(&#x27;\\n&#x27;.join(lines[method.lineno-1:method.end_lineno]))&quot;</code> |
| tests/test_llg2.py:84 | BEYOND | ∅ (added file) | <code>&quot;    serialize_source = &#x27;\\n&#x27;.join(lines[serialize.lineno-1:serialize.end_lineno])&quot;</code> |
| tests/test_llg2.py:85 | BEYOND | ∅ (added file) | <code>&quot;    fixture = &#x27;&#x27;&#x27;&quot;</code> |
| tests/test_llg2.py:86 | BEYOND | ∅ (added file) | <code>&quot;import sys, types, os&quot;</code> |
| tests/test_llg2.py:87 | BEYOND | ∅ (added file) | <code>&quot;from enum import Enum&quot;</code> |
| tests/test_llg2.py:88 | BEYOND | ∅ (added file) | <code>&quot;for name in (&#x27;vllm&#x27;, &#x27;torch&#x27;, &#x27;transformers&#x27;, &#x27;vllm.model_executor&#x27;, &#x27;vllm.model_executor.models&#x27;,&quot;</code> |
| tests/test_llg2.py:89 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;vllm.v1&#x27;, &#x27;vllm.v1.engine&#x27;, &#x27;vllm.v1.engine.core&#x27;, &#x27;vllm.v1.worker&#x27;, &#x27;vllm.v1.worker.gpu_model_runner&#x27;,&quot;</code> |
| tests/test_llg2.py:90 | BEYOND | ∅ (added file) | <code>&quot;             &#x27;vllm.v1.structured_output&#x27;, &#x27;vllm.v1.structured_output.backend_guidance&#x27;):&quot;</code> |
| tests/test_llg2.py:91 | BEYOND | ∅ (added file) | <code>&quot;    module = types.ModuleType(name); module.__version__ = &#x27;fixture&#x27;; module.__path__ = []&quot;</code> |
| tests/test_llg2.py:92 | BEYOND | ∅ (added file) | <code>&quot;    sys.modules[name] = module&quot;</code> |
| tests/test_llg2.py:93 | BEYOND | ∅ (added file) | <code>&quot;sys.modules[&#x27;vllm&#x27;].LLM = object&quot;</code> |
| tests/test_llg2.py:94 | BEYOND | ∅ (added file) | <code>&quot;sys.modules[&#x27;vllm.model_executor.models&#x27;].qwen3_5 = object&quot;</code> |
| tests/test_llg2.py:95 | BEYOND | ∅ (added file) | <code>&quot;class StructuredOutputOptions(Enum):&quot;</code> |
| tests/test_llg2.py:96 | BEYOND | ∅ (added file) | <code>&quot;    JSON=1; JSON_OBJECT=2; REGEX=3; GRAMMAR=4; CHOICE=5; STRUCTURAL_TAG=6&quot;</code> |
| tests/test_llg2.py:97 | BEYOND | ∅ (added file) | <code>&quot;&#x27;&#x27;&#x27;&quot;</code> |
| tests/test_llg2.py:98 | BEYOND | ∅ (added file) | <code>&quot;    fixture += &#x27;\\nexec(&#x27;+repr(&#x27;from __future__ import annotations\\n&#x27;+serialize_source+&#x27;\\n&#x27;+method_source)+&#x27;)\\n&#x27;&quot;</code> |
| tests/test_llg2.py:99 | BEYOND | ∅ (added file) | <code>&quot;    fixture += \&quot;m=sys.modules[&#x27;vllm.v1.structured_output.backend_guidance&#x27;]; m.GuidanceBackend=type(&#x27;GuidanceBackend&#x27;, (), {&#x27;compile_grammar&#x27;: compile_grammar}); m.StructuredOutputOptions=StructuredOutputOptions\\n\&quot;&quot;</code> |
| tests/test_llg2.py:100 | BEYOND | ∅ (added file) | <code>&quot;    p, rows = run_stub(tmp_path, fixture+T.PROBE_CODE)&quot;</code> |
| tests/test_llg2.py:101 | BEYOND | ∅ (added file) | <code>&quot;    assert p.returncode == 0, p.stderr&quot;</code> |
| tests/test_llg2.py:102 | BEYOND | ∅ (added file) | <code>&quot;    report = json.loads(p.stdout.split(T.PROBE_MARKER)[1])&quot;</code> |
| tests/test_llg2.py:103 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;structured_output&#x27;][&#x27;stub_runtime_error&#x27;]&quot;</code> |
| tests/test_llg2.py:104 | BEYOND | ∅ (added file) | <code>&quot;    assert report[&#x27;structured_output&#x27;][&#x27;stage&#x27;].startswith(&#x27;GuidanceBackend.compile_grammar&#x27;)&quot;</code> |
| tests/test_llg2.py:105 | BEYOND | ∅ (added file) | <code>&quot;    assert rows[-1] == dict(event=&#x27;call&#x27;, name=&#x27;llguidance.grammar_from&#x27;)&quot;</code> |
| tests/test_llg2.py:106 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:107 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:108 | BEYOND | ∅ (added file) | <code>&quot;def make_run(root, token, index, changed=False, calls=0):&quot;</code> |
| tests/test_llg2.py:109 | BEYOND | ∅ (added file) | <code>&quot;    out = root/&#x27;runs&#x27;/(token+&#x27;_r&#x27;+str(index)); out.mkdir(parents=True)&quot;</code> |
| tests/test_llg2.py:110 | BEYOND | ∅ (added file) | <code>&quot;    row = dict(example_id=&#x27;one&#x27;, token_ids=[1,2], raw_generation=&#x27;A&#x27;, extracted_answer=&#x27;A&#x27;, score=1.)&quot;</code> |
| tests/test_llg2.py:111 | BEYOND | ∅ (added file) | <code>&quot;    reference = dict(ids=[&#x27;one&#x27;], arms={arm:[copy.deepcopy(row)] for arm in C.ARMS})&quot;</code> |
| tests/test_llg2.py:112 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(out/&#x27;accepted.json&#x27;, reference)&quot;</code> |
| tests/test_llg2.py:113 | BEYOND | ∅ (added file) | <code>&quot;    if changed: row.update(token_ids=[1,3], extracted_answer=&#x27;B&#x27;, score=0.)&quot;</code> |
| tests/test_llg2.py:114 | BEYOND | ∅ (added file) | <code>&quot;    for rel in C.ARMS.values():&quot;</code> |
| tests/test_llg2.py:115 | BEYOND | ∅ (added file) | <code>&quot;        path = out/&#x27;b0/d0/results&#x27;/rel/&#x27;items_b0.jsonl&#x27;; path.parent.mkdir(parents=True)&quot;</code> |
| tests/test_llg2.py:116 | BEYOND | ∅ (added file) | <code>&quot;        path.write_text(json.dumps(row)+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_llg2.py:117 | BEYOND | ∅ (added file) | <code>&quot;    (out/&#x27;MEMORY.jsonl&#x27;).write_text(&#x27;{\&quot;memory_used_mib\&quot;:1}\\n&#x27;)&quot;</code> |
| tests/test_llg2.py:118 | BEYOND | ∅ (added file) | <code>&quot;    log = out/&#x27;llg_stub_calls.jsonl&#x27;&quot;</code> |
| tests/test_llg2.py:119 | BEYOND | ∅ (added file) | <code>&quot;    log.write_text(&#x27;{\&quot;event\&quot;:\&quot;import\&quot;,\&quot;module\&quot;:\&quot;llguidance\&quot;,\&quot;pid\&quot;:1}\\n&#x27; + &#x27;{\&quot;event\&quot;:\&quot;call\&quot;,\&quot;name\&quot;:\&quot;LLMatcher\&quot;}\\n&#x27;*calls)&quot;</code> |
| tests/test_llg2.py:120 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(out/&#x27;EXIT.json&#x27;, dict(returncode=0, llguidance_stub=T.llguidance_evidence(), stub_usage=T.stub_usage(log)))&quot;</code> |
| tests/test_llg2.py:121 | BEYOND | ∅ (added file) | <code>&quot;    C.write_report(out/&#x27;accepted.json&#x27;, out/&#x27;b0/d0&#x27;, &#x27;b0&#x27;, out, out/&#x27;MEMORY.jsonl&#x27;, out/&#x27;EXIT.json&#x27;)&quot;</code> |
| tests/test_llg2.py:122 | BEYOND | ∅ (added file) | <code>&quot;    return out&quot;</code> |
| tests/test_llg2.py:123 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:124 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:125 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;changed,calls&#x27;, [(False,0),(True,0),(False,1)])&quot;</code> |
| tests/test_llg2.py:126 | BEYOND | ∅ (added file) | <code>&quot;def test_repeated_comparison_and_call_rejection(tmp_path, changed, calls):&quot;</code> |
| tests/test_llg2.py:127 | BEYOND | ∅ (added file) | <code>&quot;    token=&#x27;p12345678&#x27;&quot;</code> |
| tests/test_llg2.py:128 | BEYOND | ∅ (added file) | <code>&quot;    make_run(tmp_path, token, 1)&quot;</code> |
| tests/test_llg2.py:129 | BEYOND | ∅ (added file) | <code>&quot;    second=make_run(tmp_path, token, 2, changed, calls)&quot;</code> |
| tests/test_llg2.py:130 | BEYOND | ∅ (added file) | <code>&quot;    out=tmp_path/&#x27;summary&#x27;; out.mkdir()&quot;</code> |
| tests/test_llg2.py:131 | BEYOND | ∅ (added file) | <code>&quot;    result=C.write_repeated(tmp_path,token,out)&quot;</code> |
| tests/test_llg2.py:132 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;passed&#x27;] == (not changed and not calls)&quot;</code> |
| tests/test_llg2.py:133 | BEYOND | ∅ (added file) | <code>&quot;    check=result[&#x27;run_to_run&#x27;][&#x27;arms&#x27;][&#x27;ON16k&#x27;]&quot;</code> |
| tests/test_llg2.py:134 | BEYOND | ∅ (added file) | <code>&quot;    assert check[&#x27;items&#x27;][0][&#x27;first_divergence_index&#x27;] == (1 if changed else None)&quot;</code> |
| tests/test_llg2.py:135 | BEYOND | ∅ (added file) | <code>&quot;    assert check[&#x27;answers_equal&#x27;] == (not changed) and check[&#x27;scores_equal&#x27;] == (not changed)&quot;</code> |
| tests/test_llg2.py:136 | BEYOND | ∅ (added file) | <code>&quot;    if calls:&quot;</code> |
| tests/test_llg2.py:137 | BEYOND | ∅ (added file) | <code>&quot;        proof=T.load(second/&#x27;PROOF.json&#x27;)&quot;</code> |
| tests/test_llg2.py:138 | BEYOND | ∅ (added file) | <code>&quot;        assert not proof[&#x27;passed&#x27;] and any(&#x27;called 1&#x27; in e for e in proof[&#x27;errors&#x27;])&quot;</code> |
| tests/test_llg2.py:139 | BEYOND | ∅ (added file) | <code>&quot;    assert &#x27;Run 1 vs accepted&#x27; in (out/&#x27;PROOF.md&#x27;).read_text()&quot;</code> |
| tests/test_llg2.py:140 | BEYOND | ∅ (added file) | <code>&quot;    assert &#x27;Run 2 vs accepted&#x27; in (out/&#x27;PROOF.md&#x27;).read_text()&quot;</code> |
| tests/test_llg2.py:141 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:142 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:143 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;fail_first&#x27;, [False, True])&quot;</code> |
| tests/test_llg2.py:144 | BEYOND | ∅ (added file) | <code>&quot;def test_repeat_sequential_same_card_and_no_retry(tmp_path, monkeypatch, fail_first):&quot;</code> |
| tests/test_llg2.py:145 | BEYOND | ∅ (added file) | <code>&quot;    seen=[]&quot;</code> |
| tests/test_llg2.py:146 | BEYOND | ∅ (added file) | <code>&quot;    def run(args):&quot;</code> |
| tests/test_llg2.py:147 | BEYOND | ∅ (added file) | <code>&quot;        seen.append((args.run_name,args.gpu))&quot;</code> |
| tests/test_llg2.py:148 | BEYOND | ∅ (added file) | <code>&quot;        index=len(seen)&quot;</code> |
| tests/test_llg2.py:149 | BEYOND | ∅ (added file) | <code>&quot;        if fail_first: raise RuntimeError(&#x27;Reader killed; do not retry&#x27;)&quot;</code> |
| tests/test_llg2.py:150 | BEYOND | ∅ (added file) | <code>&quot;        make_run(tmp_path,args.token,index)&quot;</code> |
| tests/test_llg2.py:151 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;_launch_one&#x27;,run)&quot;</code> |
| tests/test_llg2.py:152 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;sandbox_receipt&#x27;,lambda **kw: dict())&quot;</code> |
| tests/test_llg2.py:153 | BEYOND | ∅ (added file) | <code>&quot;    args=NS(root=str(tmp_path),command=&#x27;proof&#x27;,token=&#x27;p12345678&#x27;,gpu=&#x27;3&#x27;,repeat=2)&quot;</code> |
| tests/test_llg2.py:154 | BEYOND | ∅ (added file) | <code>&quot;    if fail_first:&quot;</code> |
| tests/test_llg2.py:155 | BEYOND | ∅ (added file) | <code>&quot;        with pytest.raises(RuntimeError,match=&#x27;Reader killed&#x27;): T.launch(args)&quot;</code> |
| tests/test_llg2.py:156 | BEYOND | ∅ (added file) | <code>&quot;    else: T.launch(args)&quot;</code> |
| tests/test_llg2.py:157 | BEYOND | ∅ (added file) | <code>&quot;    assert seen == [(&#x27;p12345678_r1&#x27;,&#x27;3&#x27;)]+([] if fail_first else [(&#x27;p12345678_r2&#x27;,&#x27;3&#x27;)])&quot;</code> |
| tests/test_llg2.py:158 | BEYOND | ∅ (added file) | <code>&quot;    result=T.load(tmp_path/&#x27;runs/p12345678/RUN_TO_RUN.json&#x27;)&quot;</code> |
| tests/test_llg2.py:159 | BEYOND | ∅ (added file) | <code>&quot;    assert result[&#x27;passed&#x27;] != fail_first&quot;</code> |
| tests/test_llg2.py:160 | BEYOND | ∅ (added file) | <code>&quot;    assert (tmp_path/&#x27;runs/p12345678_r1/SANDBOX.json&#x27;).exists()&quot;</code> |
| tests/test_llg2.py:161 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:162 | BEYOND | ∅ (added file) | <code>&quot;&quot;</code> |
| tests/test_llg2.py:163 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;command&#x27;, [&#x27;proof&#x27;,&#x27;read&#x27;])&quot;</code> |
| tests/test_llg2.py:164 | BEYOND | ∅ (added file) | <code>&quot;@pytest.mark.parametrize(&#x27;calls&#x27;, [0,1])&quot;</code> |
| tests/test_llg2.py:165 | BEYOND | ∅ (added file) | <code>&quot;def test_run_audit_receipt_and_packet(tmp_path, monkeypatch, command, calls):&quot;</code> |
| tests/test_llg2.py:166 | BEYOND | ∅ (added file) | <code>&quot;    cfg=dict(spec=dict(package=str(T.SJ/&#x27;pkg&#x27;),models={}))&quot;</code> |
| tests/test_llg2.py:167 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;require_stage&#x27;,lambda root:copy.deepcopy(cfg))&quot;</code> |
| tests/test_llg2.py:168 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;cpu_need&#x27;,lambda *a:dict(ids=[&#x27;one&#x27;],need=[]))&quot;</code> |
| tests/test_llg2.py:169 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;read_space&#x27;,lambda *a:0)&quot;</code> |
| tests/test_llg2.py:170 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;check_card&#x27;,lambda *a:dict(index=&#x27;2&#x27;))&quot;</code> |
| tests/test_llg2.py:171 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;capture_command&#x27;,lambda argv:dict(stdout=&#x27;fixture\\n&#x27;,returncode=0))&quot;</code> |
| tests/test_llg2.py:172 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;probe&#x27;,lambda *a:dict(passed=True,versions=dict(python=&#x27;3.12&#x27;,vllm=&#x27;0.32&#x27;,torch=&#x27;fixture&#x27;,transformers=&#x27;fixture&#x27;),glibc=&#x27;glibc 2.28&#x27;))&quot;</code> |
| tests/test_llg2.py:173 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;ns_command&#x27;,lambda *a,**k:[&#x27;/usr/bin/bwrap&#x27;,&#x27;--bind&#x27;,str(tmp_path),str(tmp_path),&#x27;fake-reader&#x27;])&quot;</code> |
| tests/test_llg2.py:174 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;host_shm_ours&#x27;,lambda:[])&quot;</code> |
| tests/test_llg2.py:175 | BEYOND | ∅ (added file) | <code>&quot;    row=dict(example_id=&#x27;one&#x27;,token_ids=[1],raw_generation=&#x27;A&#x27;,extracted_answer=&#x27;A&#x27;,score=1.)&quot;</code> |
| tests/test_llg2.py:176 | BEYOND | ∅ (added file) | <code>&quot;    T.dump(tmp_path/&#x27;sj/pkg/parity/DEV20.json&#x27;,dict(ids=[&#x27;one&#x27;],need=[],arms={a:[row] for a in C.ARMS}))&quot;</code> |
| tests/test_llg2.py:177 | BEYOND | ∅ (added file) | <code>&quot;    out=tmp_path/&#x27;runs/p12345678&#x27; if command==&#x27;proof&#x27; else tmp_path/&#x27;packet&#x27;&quot;</code> |
| tests/test_llg2.py:178 | BEYOND | ∅ (added file) | <code>&quot;    def reader(argv, env, *a):&quot;</code> |
| tests/test_llg2.py:179 | BEYOND | ∅ (added file) | <code>&quot;        assert env[&#x27;CUDA_VISIBLE_DEVICES&#x27;]==&#x27;2&#x27;&quot;</code> |
| tests/test_llg2.py:180 | BEYOND | ∅ (added file) | <code>&quot;        assert env[&#x27;LLG_STUB_LOG&#x27;]==str(out/&#x27;llg_stub_calls.jsonl&#x27;)&quot;</code> |
| tests/test_llg2.py:181 | BEYOND | ∅ (added file) | <code>&quot;        Path(env[&#x27;LLG_STUB_LOG&#x27;]).write_text(&#x27;{\&quot;event\&quot;:\&quot;import\&quot;,\&quot;module\&quot;:\&quot;llguidance\&quot;,\&quot;pid\&quot;:2}\\n&#x27;+&#x27;{\&quot;event\&quot;:\&quot;call\&quot;,\&quot;name\&quot;:\&quot;LLMatcher\&quot;}\\n&#x27;*calls)&quot;</code> |
| tests/test_llg2.py:182 | BEYOND | ∅ (added file) | <code>&quot;        if command==&#x27;proof&#x27;:&quot;</code> |
| tests/test_llg2.py:183 | BEYOND | ∅ (added file) | <code>&quot;            for rel in C.ARMS.values():&quot;</code> |
| tests/test_llg2.py:184 | BEYOND | ∅ (added file) | <code>&quot;                path=out/&#x27;b0/d0/results&#x27;/rel/&#x27;items_b0.jsonl&#x27;;path.parent.mkdir(parents=True)&quot;</code> |
| tests/test_llg2.py:185 | BEYOND | ∅ (added file) | <code>&quot;                path.write_text(json.dumps(row)+&#x27;\\n&#x27;)&quot;</code> |
| tests/test_llg2.py:186 | BEYOND | ∅ (added file) | <code>&quot;        return 0,None&quot;</code> |
| tests/test_llg2.py:187 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;run_reader&#x27;,reader)&quot;</code> |
| tests/test_llg2.py:188 | BEYOND | ∅ (added file) | <code>&quot;    class Sampler:&quot;</code> |
| tests/test_llg2.py:189 | BEYOND | ∅ (added file) | <code>&quot;        def __init__(self,gpu,path):&quot;</code> |
| tests/test_llg2.py:190 | BEYOND | ∅ (added file) | <code>&quot;            self.thread=NS(start=lambda:path.write_text(&#x27;{\&quot;memory_used_mib\&quot;:1}\\n&#x27;),join=lambda **kw:None)&quot;</code> |
| tests/test_llg2.py:191 | BEYOND | ∅ (added file) | <code>&quot;            self.stop=NS(set=lambda:None);self.errors=[]&quot;</code> |
| tests/test_llg2.py:192 | BEYOND | ∅ (added file) | <code>&quot;    monkeypatch.setattr(T,&#x27;Sampler&#x27;,Sampler)&quot;</code> |
| tests/test_llg2.py:193 | BEYOND | ∅ (added file) | <code>&quot;    args=NS(root=str(tmp_path),command=command,token=&#x27;p12345678&#x27;,gpu=&#x27;2&#x27;,family=&#x27;main&#x27;,first=1,ids=None,&quot;</code> |
| tests/test_llg2.py:194 | BEYOND | ∅ (added file) | <code>&quot;            out=str(out),artifact=str(T.LINEAGE/&#x27;m544/artifact.json&#x27;),sha256=&#x27;a&#x27;*64,step=544)&quot;</code> |
| tests/test_llg2.py:195 | BEYOND | ∅ (added file) | <code>&quot;    if calls:&quot;</code> |
| tests/test_llg2.py:196 | BEYOND | ∅ (added file) | <code>&quot;        with pytest.raises(RuntimeError,match=&#x27;llguidance audit failed&#x27;): T.launch(args)&quot;</code> |
| tests/test_llg2.py:197 | BEYOND | ∅ (added file) | <code>&quot;    else: T.launch(args)&quot;</code> |
| tests/test_llg2.py:198 | BEYOND | ∅ (added file) | <code>&quot;    receipt=T.load(out/&#x27;SANDBOX.json&#x27;)&quot;</code> |
| tests/test_llg2.py:199 | BEYOND | ∅ (added file) | <code>&quot;    assert receipt[&#x27;namespace_executed&#x27;] and receipt[&#x27;versions&#x27;][&#x27;python&#x27;]==&#x27;3.12&#x27;&quot;</code> |
| tests/test_llg2.py:200 | BEYOND | ∅ (added file) | <code>&quot;    packet=out/&#x27;b0/d0&#x27; if command==&#x27;proof&#x27; else out&quot;</code> |
| tests/test_llg2.py:201 | BEYOND | ∅ (added file) | <code>&quot;    assert T.load(packet/&#x27;SANDBOX.json&#x27;)==receipt&quot;</code> |
| tests/test_llg2.py:202 | BEYOND | ∅ (added file) | <code>&quot;    usage=T.load(packet/&#x27;LLGUIDANCE.json&#x27;)[&#x27;usage&#x27;]&quot;</code> |
| tests/test_llg2.py:203 | BEYOND | ∅ (added file) | <code>&quot;    assert usage[&#x27;import_events_count&#x27;]==1 and usage[&#x27;call_events_count&#x27;]==calls&quot;</code> |
| tests/test_llg2.py:204 | BEYOND | ∅ (added file) | <code>&quot;    if command==&#x27;proof&#x27;: assert T.load(out/&#x27;PROOF.json&#x27;)[&#x27;passed&#x27;]==(calls==0)&quot;</code> |
| REPORT_LLG2.md:1 | BEYOND | ∅ (added file) | <code>&quot;Stub v2 logs imports and every attempted guidance call, raises on use, and has pinned hashes; work/llg_stub remains v1.&quot;</code> |
| REPORT_LLG2.md:2 | BEYOND | ∅ (added file) | <code>&quot;Proof/read inherit a per-run LLG_STUB_LOG; EXIT/PROOF and packet LLGUIDANCE.json carry names, hashes, counts, and failure reasons.&quot;</code> |
| REPORT_LLG2.md:3 | BEYOND | ∅ (added file) | <code>&quot;Any generation-time stub call, malformed log, or missing enabled-stub import evidence fails the audit.&quot;</code> |
| REPORT_LLG2.md:4 | BEYOND | ∅ (added file) | <code>&quot;Every proof/read/probe writes SANDBOX.json with bwrap/binds, stub, glibc, driver libraries/query, and probe versions; phase-B packets receive a copy.&quot;</code> |
| REPORT_LLG2.md:5 | BEYOND | ∅ (added file) | <code>&quot;The CPU probe invokes the installed GuidanceBackend.compile_grammar(REGEX, \&quot;a\&quot;) and requires the stub RuntimeError plus a logged call.&quot;</code> |
| REPORT_LLG2.md:6 | BEYOND | ∅ (added file) | <code>&quot;Real probe: ../root/runs/probe_20261116T044423.425718Z/PROBE.json records missing runtime_0/uv Python; no namespace guidance success is claimed.&quot;</code> |
| REPORT_LLG2.md:7 | BEYOND | ∅ (added file) | <code>&quot;The receipt records host glibc 2.28 and driver-library paths/sizes; nvidia-smi could not communicate with the driver in this sandbox.&quot;</code> |
| REPORT_LLG2.md:8 | BEYOND | ∅ (added file) | <code>&quot;proof --repeat 2 creates sequential _r1/_r2 runs on one card, RUN_TO_RUN.json, and a combined PROOF.md; failed execution/audit stops the sequence.&quot;</code> |
| REPORT_LLG2.md:9 | BEYOND | ∅ (added file) | <code>&quot;Tests: 134 passed (TESTS_LLG2_FINAL.log), including actual installed guidance-method source with dependency fixtures, packet receipts, and repeat comparisons.&quot;</code> |
| REPORT_LLG2.md:10 | BEYOND | ∅ (added file) | <code>&quot;README/DIFF and root wrapper manifest are current; LLG2_PRESERVED.json verifies v1/staged evidence. No staging, GPU inference, transfer, Git, or deletion ran.&quot;</code> |
