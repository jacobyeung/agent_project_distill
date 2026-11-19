# CPU and release check inventory

The wrapper runs the implemented per-delivery gates below before it prints an executable release plan. The source harness and production-data gaps are listed explicitly; this delivery is not a complete production release certification. A missing local input fails this gate; it never moves that check to after placement. Local mirrors authenticate the same archive bytes and preserve the remote names through a path adapter. Fixture results establish the checker, not the availability of a production export.

| Native source and check | Trinity, same bytes and inputs | Orchard dependency |
|---|---|---|
| `o_cpu_A3/A4/B4/B5.sh`, `o_cpu_D.sh`: fill status, no previous CPU receipt, `3.py check` | Run exact `3.py` under real `/usr/bin/python3` 3.6.8 with authenticated path mirrors; verify filled inputs | Actual package permissions, absence of prior job, part sizes and token directory must be rechecked on Orchard |
| `3.py`, payload `8.py`, common/job: public/payload/plan/member hashes, registered dependency pins, export binding, input schema/types, time/GPU contract and opaque sbatch arguments | Yes; exact helpers plus independent archive checks | Actual `sbatch` submission |
| `a/5.py` before staging: payload and member hashes, sequence bytes | Yes | Slurm job ID, node-local `/tmp` space and storage proof |
| `job.stage`: authenticated archive parts, safe tar members, destination resolution, payload pins, all input file pins/sizes, env receipt, vnice/terminator pins and policy receipt | Yes when all bytes are mirrored locally; missing mirrors block release | Real staging/extraction into the allocated namespace, filesystem capacity and namespace support |
| `a/5.py check_bundle_guard`: 3 bundle members, descriptor equality, operator equality, guarded 4 MiB pool write, operator unchanged | Yes; actual helper and process guard on local storage | Real return-pool access, quota and persistence |
| `a/5.py dispatch_operator`: guard installed before write test before bootstrap/operator dispatch; guard target bytes, argv rewrite and operator hash | Yes, actual helper with a recording terminal dispatcher | Actual namespaced operator process in the staged job environment |
| `a/6.py`: descriptors, item/type counts, settings, native preparation, worker arguments and selector rehearsal | Yes, exact payload and native CPU stub rehearsal; tensor threads capped at 8 | Real export restore, actual RGB files and installed job packages |
| `a/6.py memory_bound`: fixed shapes, capture counts, allocation fit and too-small allocation rejection | Yes | Real resident memory during full staged reader |
| `a/5.py validate_full_reader`: CPU read count, set/item/type, 32 frames, completion/EOS and score agreement | Exact validator and malformed synthetic receipt fixtures run locally; actual full-reader execution was not run | Producing the real FULL_READER receipt needs the export/RGBs/job venv, unavailable here; this could run on Trinity if identical inputs and environment were staged |
| `o_sub_A4/B5/D.sh`: CPU receipt hashes, bundle/entry event order, 4 MiB evidence hash, memory equality, FULL_READER equality and per-package identities | Pure receipt predicates and script sealing run locally; generated receipt tests exercise conditions | Successful actual CPU allocation/receipt, sacct terminal state, general queue empty, actual return pool <=75 MB, duplicate submit marker |
| `dry2.py`, `dry2b.py`: payload/member/bundle checks, export pins, prep members/hashes, binding, archive0, policy and environment resolution, settings/operator/types/items/memory, submit job name | Yes; covered by structure, fill, archive resolver, logic and guard gates | None beyond availability of authenticated mirrors |
| `dryres.py`, `dryres2.py`, `dryres_d.py`: ordered parts, tar headers, unique regular member resolution, sizes, policy authorization, preserved base slots and appended prep tar | Yes; resolver checks stronger full file hashes as well | No extra dependency |
| `check_release_d.py`: embedded assets equal source, 200/544 deliveries/pins, metadata, compile, walltime rejection, dry header fixture, wrong reused part rejection | Source/embedded equality is a required per-delivery gate. The complete unchanged checker runs separately with W redirected locally; raw input fails, coherent fixture passes | None |
| `run_release_gates.py`: release package, bundle guard, operator sequence, memory, return/stop, CPU helper and room pair/labels | Package helper assertions run separately. Referenced test_sequence, test_operator_memory, test_fixes, test_cpu_helper, test_room_pair and test_room_pair_labels harness files were not supplied at the referenced release paths; their complete assertions are unverified | Full staged reader subset as above |
| `BATCH.sh` EXIT capture and USR1 forwarding, `runner.run` stop marker/partial summary | Yes; execute exact wrapper with bounded failing child and exact native runner with a cooperative tiny child | Slurm delivering `--signal=B:USR1@1800`, scheduler teardown and real trainer-rank cooperation |
| `o_cpu_B5.sh` extra trap-test submission | Shell block inventoried; reject its digit-leading job token and extra submission rather than silently use it | Separate five-minute Slurm job; not part of wrapper CPU submit |

Inputs: `cont_ops17/work/o_cpu_*.sh`, `dry*.py`, `build_r5..r10.py`, `bundle0_*.py`; `cont_ops18/dbuild/check_release_d.py`, `o_cpu_D.sh`, `o_sub_D.sh`, `place_fill_d.py`; routed package `a/5.py`, `a/6.py`, payload `8.py` and `orchard_h10/{common,job,runner}.py`. The six event files were read by their supplied names. The B4 three-second root cause is unknown: the regression verifies readable failure capture, not a speculative repair. The trainer USR1 event is outside the read runner; the local signal test does not establish trainer-rank behavior.

## Scope of the wrapper and source-regression evidence

`pack.py check` invokes `logic`, `guard`, `trap`, `stop`, `login`, `fill` and `receipt` on the built package, then validates every generated phase script. The source release harnesses `check_release_d.py` and `run_release_gates.py` are not launched by that per-delivery command. The probes cover the listed package hash, bundle, sequence, memory, input-selection, return/stop and CPU-receipt predicates. The missing routed harness tests are not claimed equivalent to those probes. D embedded/source equality is additionally required before local checks and before consuming a check receipt. The standalone `test_native.py` executes the exact D checker with its workspace redirected under this task directory.

The raw supplied D source tree fails `check_release_d.py` because `score_d.py` differs from the copy embedded in `o_build_D.sh`. The additive token adapter preserves that same failure. A separately labelled coherent snapshot of the authenticated embedded assets passes the unchanged checker before and after adding the adapter. Thus raw-source release consistency remains a production prerequisite, and the wrapper rejects this supplied source before remote release. The tests do not claim that a synthetic export is the same input as a production export; production preflight requires authenticated mirrors of all actual bytes and fails when they are unavailable.

## Predicate detail and limits

All rows below are CPU predicates and can run on Trinity with the identical inputs. They do not intrinsically need Orchard. The native sources name them in `cont_ops17/work/dry2.py:16–96` and `dry2b.py:16–98`.

| Predicate | Implemented gate or remaining limit |
|---|---|
| Payload SHA, every package file SHA, sequence equals a/6, plan SHA, every payload pin | `structure` |
| Native export pin load and export binding run/step/member_directory/lineage/object | Native `a/4.py` and `3.py check` during isolated fill |
| No optional inputs; selected type membership | `logic`; exact full-five and single-type order is required |
| Preparation member set, every preparation hash/size, binding preparation hashes | Native fill plus `resolver` |
| Archive0 equals authenticated export and REVIEWED_ARCHIVE_SHA256 | Native fill and entry check |
| Exactly one a3 slot with vnice/terminator SHA, authorized policy and policy paths | Resolver requires exactly one full-SHA match to authenticated base policy slot 4, and policy/environment/scripts must resolve to that slot; full SHA equality strengthens the legacy prefix test |
| Environment receipt presence and version report | Resolver proves presence and pins; installed job-version compatibility is deferred for missing environment |
| Bundle inventory, descriptor, operator and temporary token | `structure` and exact native `check_bundle_guard` |
| Selection rule, memo enabled/modules/verify IDs, rule in operator RULES | Exact applicable dry settings, empty verify IDs, rule membership and native rehearsal |
| Descriptor count 636 for full-five or 134 for room package; item counts 150/36/150/150/150; selected type order | Exact native full-five (636), room (134) and D distance (580) constants, per-type counts, descriptor count and selected order; native rehearsal and manifest contract also run |
| Fixed shape memory fits, basis and no SAM measurement | Native memory bound, too-small rejection and sealed submit receipt predicates |
| Exact token in 2.json job argv | `privacy` after native entry check |

The D submit receipt predicates (`cont_ops18/dbuild/o_sub_D.sh:16–50`) check: overall/bundle/entry pass flags; payload/plan/operator/input hashes; guard path/target/action; operator and batch hashes; entry events and unchanged operator; pool and token; integer 4 MiB size and 64 hexadecimal SHA; guard-target SHA; equality of guard and entry evidence; requested/dispatched argv; MEMORY file equality, fit, basis, module list and measurement flag; FULL_READER pass, native validator, exact item pairs/types, native memory equality, and FULL_READER file equality. `receipt` executes the selected native submit Python body on synthetic positive and corrupt receipts. That proves predicate wiring, not a real CPU run.

The unavailable routed harnesses prevent a claim that *every* original source-harness assertion has been reproduced. All listed dry predicates applicable to the supported full-five, room and D distance families now run on the built bytes. Real full-reader/export/RGB checks also remain unrun because their production inputs are absent.
