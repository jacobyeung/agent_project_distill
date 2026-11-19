# Read-package check inventory

The CPU submission runs `3.py check` on the login node, then `a/5.py` inside a Slurm allocation. A4 checks all five routed types. B5 adds a two-set full-reader rehearsal for room questions. D selects distance questions and changes those two sets. `check_release_d.py` is a local release checker, not a command in `o_cpu_D.sh`.

Paths below are relative to the supplied `cont_ops16/work/c15/r1route/out3/A4/src` unless prefixed otherwise. The companion `CHECK_PREDICATES.json` preserves source lines and conditional predicates. Developer regression suites are listed separately; an unexecuted suite is not CPU-job evidence.

| Check and source | Trinity: same bytes and inputs? | Orchard dependency or local action |
|---|---|---|
| Fill exit status; package path/walltime syntax; no prior CPU marker/results (`o_cpu_*.sh`) | Partly | Syntax is local. Actual placement, fill status, collision markers and allocation remain remote. |
| Payload SHA; canonical plan SHA; helper pins (`8.py:load_helpers`, `common.py:read_config`, `job.py:verify_config`) | Yes | Execute exact bundled helpers on built archive. |
| Every package file SHA; sequence equals `a/6.py`; config/public/plan token consistency (`8.py:check`, `a/5.py:main`) | Yes | Hash shipped bytes, not builder workspace. |
| Token grammar, opaque argv/env/cwd, time/card/GPU-hour bounds (`common.py:valid_token`, `opaque`, `submit_argv`, `install_process_guard`) | Yes for values | Dynamic Slurm environment must be checked remotely too. Scan delivery names and operational argv/env/cwd; private archive contents are excluded. |
| Registered placement path, private mode, actual archive-part sizes (`8.py:check`) | Metadata yes; actual location no | Local mirrors establish bytes; login check repeats at exact destination. |
| Export schema, step/lineage, canonical paths, positive sizes/full hashes, distinct preparation paths (`export_pins.py:validate/load`) | Yes | Use exact filled inputs and export receipt. |
| Reviewed run/step/member/object/lineage/config/preparation/whole-archive identity; heads/full-weight pins (`export_pins.py:admit`) | Yes | Execute native helper after real fill. |
| Inputs schema, ordered types, archive pins/destination/part namespace, dependencies, registered hashes/prefixes, logical paths, python/policy/env receipts, optional index/root/hash (`job.py:check_inputs`) | Yes | Execute exact function with package path supplied. |
| Export part/whole hashes, safe regular unique tar members, weight shards/index/artifact pins, reviewed receipt/preparation identity and flags (`a/4.py`) | Yes if parts supplied | Run actual fill under `-I -s -B`; never relax sealed constants for a release. Mirror omits the large export. |
| Preserve base archives after slot zero; append prep; env/policy archive survives (`a/4.py`, `dryres2.py`, `dryres_d.py`) | Yes | Compare lists and resolve local archive headers/pins. Missing mirrors fail prerequisites. |
| Template/bwrap pins, extraction limits/link policy, code/file hashes/sizes, policy script hashes and authorization (`job.py:stage`, vendor stage helper) | Algorithm yes; full inputs absent | Exact staging exceeds this dispatch's input set and workspace cap. CPU job must repeat it. |
| Numeric allocated job ID, node disk proof, bwrap namespace/template (`a/5.py:main`, vendor job helper) | No | Needs Slurm, node disk, mount layout and namespace permissions. |
| Bundle exactly three regular members; public descriptor equality; operator byte equality (`a/5.py:check_bundle_guard`) | Yes | Decode before staging; compare bytes as well as JSON. |
| Real process guard, 4 MiB write-test size/hash, `6.py` vendor target, unchanged operator (`a/5.py:check_bundle_guard`) | Yes with local pool | Exact helper with temporary pool; real return-pool permission/capacity remains remote. |
| Dispatch after guard/write proof; evidence hashes; entry replaced once with `7.py`; unchanged operator SHA (`a/5.py:dispatch_operator`, embedded `0.py`) | Yes | Exact callable with local proof and recording launcher; no model execution claim. |
| Python/library versions equal receipt; transformers >=5.12 (`prepare.py:run`) | No for actual venv | Local CPU venv cannot attest Orchard CUDA venv. |
| Prep fallback pins, restore architecture/config/frame layout, shard/index pins, code/source manifest, optional RGB hashes, READY/settings/binding/RESTORE hashes (`prepare.py`, `b/parity_kit/stage_restore.py`) | In principle; same inputs absent | Run exact restore in Orchard CPU job; toy weights cannot establish restore. |
| Prepared rule, memo modules/verify IDs and selected types (`a/5.py:main`, operator) | Plan yes; actual settings no | Actual prepared settings belong to remote CPU receipt. |
| Identity/settings hashes, no optional input, known rule, worker args/arms/modes/types/stop-file, socket selector rule (`a/6.py:prepare/rehearsal`) | Yes with small local fixture | Exact callable; stubs establish rehearsal only. |
| Memory bound fits; fixed shape basis/captures/memo; no SAM measurement required (`a/6.py:memory_bound`) | Yes | Exact function; bound is not measured GPU memory. |
| B5/D full reader: CPU, RESTORE, manifest sets/items, 32 frame hashes/PNG decode, mapping/load/decode counts, complete/EOS/token/type/arm/mode records, official score, env binding (`a/6.py:full_reader_rehearsal`, `a/5.py:validate_full_reader`) | Conditional | Logic is local; same staged RGBs/restore/venv are absent. Remote CPU runs supplied rehearsal, including its model stubs. |
| CPU receipt binds plan/payload/inputs/operator/storage/READY/memory/guard/dispatch/full-reader (`a/5.py:main`) | Predicate yes; authentic receipt no | Validate remote receipt before GPU submit. Local receipts cannot satisfy this gate. |
| D embedded assets SHA/source equality; 200/544 delivery SHA; metadata/item/twin/unit/frame/room/set validation; compile; trap/exclusion; wrong-walltime rejection (`dbuild/check_release_d.py`) | Yes subject to fixture inputs | Script hardcodes `/dev/shm/c18d`; do not execute it with writes outside L. Reuse its underlying validators. |
| D dry header fixture, reused-part size/SHA rejection (`check_release_d.py`, `place_fill_d.py:check_part`) | Yes | Small local archive; real parts remain separate prerequisites. |
| EXIT trap preserves failure/node/exception tail; USR1 reaches CPU child and produces stop/end evidence (`build_r9/r10.py:wrap_batch`) | Yes for wrapper | Retain exact trap/tail; redirect local destinations. Tiny child does not certify training-rank stop/export. |
| Training duplicate-layout fps/total_num_frames/indices/timestamps; signal end export (recorded incidents) | Layout yes; trainer proof requires trainer inputs | Invoke exact `layout_inputs` on rows. A generic child cannot certify four training ranks or export. |

`run_release_gates.py` names package, bundle/process-guard, sequence, memory, return/stop, CPU helper, room-pair and room-label suites. It expects missing `release/b1,b2` fixture trees. `check_release_d.py` expects missing `/dev/shm/c18d` trees. `test_fix7.py` needs direct/facing/VSTI roots and `offline_guard`, which are not supplied. These are developer tests, not extra commands in `o_cpu_*.sh`.

Missing same-input checks prevent release. A4 and B5 pass the operational-name rule. The login probe executes generated placement under real Python 3.6.8; the fill probe uses that same interpreter. Authenticated full export/dependency mirrors and the Trinity token ledger remain required.
