# H1-1 read kit

The local kit supports H1-1 run `17c4ffa4` and D0 run `359fcc3c` at m100/m200, plus H1-1's three claimed stop generations. It adds all 2,169 R0-dev items as Orchard family `a7`. All four families total 3,994 items. `readk/` supplies the unchanged D0 reference; the candidate lives in `kit/`.

**The literal naming requirement remains unsatisfied for the inherited families. Do not submit this kit as a fully anonymous job.** The accepted D0 journals contain virtual `video_path` values with dataset names. These fields are part of the accepted task/frame identity. `evidence/NAME_AUDIT.json` gives concrete examples for main, away and forward. The supplied kit also lacks the complete runtime-archive member inventory, so this build cannot certify every inherited private path. The new asset paths, tar members, item IDs, room IDs and family label are opaque. No exception to the user's naming rule is assumed.

No network, SSH, Orchard/GCS operation, GPU, Git or deletion was used. No production token or production build was prepared. Fixed `a000000001` preparations under `evidence/test_*` are test fixtures. Every write is inside this workspace. The operator alone uploads and submits.

## Export binding

The public prepare interface and the embedded bootstrap validate the exact namespace `8865619b`. Normal reads allow only m100 and m200 for the two registered runs. All other runs, normal steps, namespaces and unregistered stop generations are refused before cloud staging. The base model and the selected artifact retain the accepted native export checker. Four ordered parts must match the whole-tar byte count and SHA256 before extraction. The unchanged admission function and full export checker then verify the archive and tensor inventory.

| Identity | Source lines in the read-only H1 packet |
|---|---|
| Run `17c4ffa4` | `../h1/ids.json:1`, `tokens.run` |
| Namespace `8865619b` | `../h1/build/fx/b/c.sh:9`; `../h1/runtime/jb.sh:25` |
| Deployment `/project/community/jjyeung/okh7/x_4b3114cf` | `../h1/payload/z.sh:5`; `../h1/runtime/jb.sh:8` |
| m100 object `q8/8865619b/17c4ffa4_m100.tar` and parts 00–03 | `../h1/EXPORT_OBJECTS.txt:9–12` |
| m200 object `q8/8865619b/17c4ffa4_m200.tar` and parts 00–03 | `../h1/EXPORT_OBJECTS.txt:13–16` |
| mstop, mstopB, mstopC objects and their four parts | `../h1/EXPORT_OBJECTS.txt:33–44`; `../h1/runtime/jb.sh:24–25` |
| `.done` file naming and receipt format | `../h1/build/fx/b/c.sh:411–412,430` |
| Stop claim → actual optimizer step | `../h1/build/fx/b/c.sh:418–423` |
| Part suffix format | `../h1/build/fx/b/gcsput.py:17–18` |

`evidence/EXPORT_SOURCES.json` retains numbered excerpts and complete source hashes. `orch_h1.sh` and `fin_h1.sh` carry encoded bundles; the readable `payload/z.sh` and installed `build/fx/b/c.sh` establish the actual path rules.

H1 receipts are `/project/community/jjyeung/okh7/x_4b3114cf/o/gcs_17c4ffa4_m100.done` and `..._m200.done`. A stop at optimizer step 137 still writes `..._m137.done`; its object can be `17c4ffa4_mstop.tar`. The kit requires `gcs_17c4ffa4_mstop.claim` to contain exactly `m137\n`, then checks the archive's m137 directory and artifact step 137. Stop generations allow actual steps 1–200 only. A registered generation is not evidence that its upload exists. D0 retains `/project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m<s>.done`.

D0's `worker.bind`, `worker.validate`, `export_stage.stage_export` and `export_stage.parse_done` function source is byte-identical to the reference. Direct reader, adapters and export checker files are byte-identical. The reference's wider legacy helper API remains in `readk/`; the candidate's public request validator restricts reads to this task's scope.

## R0-dev protocol and assets

The item file preserves all source rows, questions, options, answers, units and ordered f32 indices. The source contains 2,167 distinct qids across 2,169 rows: two appearance questions repeat a qid with different options. An opaque item ID hashes the original qid together with its one-based source-line number. No row is deduplicated. `evidence/ID_MAP.json` stays on Trinity and is never packaged for Orchard.

The tar holds exactly 3,136 used PNGs from 98 physical rooms, with sorted opaque names, UID/GID 0, empty owner names, mtime 0 and mode 0644. Both appearances of a room use the same opaque physical-room ID. Every item uses its own 32 `frame_indices` in order, with source FPS and total frame count. This is the evaluator's `spread` layout, without frame duplication.

The job hashes both uploaded files before use, checks sizes, validates item/type/room counts and frame references, verifies every extracted PNG's bytes/SHA256, and checks RGB mode, dimensions and pixel hashes when loading frames. Model staging retains the 200 GiB free-space floor. `UPLOAD_PLAN.md` gives the exact upload targets and pins.

The new family uses the accepted prompt builder and ON16k → B2048/B4096 continuation policy, with B2048 primary, greedy decoding, the same 64-token continuation answer cap, vLLM 0.32.0, max-model length 49152, max sequences 32 and inflight 16. Five layout literals in three authenticated evaluator modules are changed in memory for this family's fresh process. Their original and effective hashes appear in the family completion record. The other families never install these changes.

The official-style scorer uses MRA for the four numeric types and parsed option exact match for multiple choice. Explicit refusal text, an unparsed or absent answer, and an output-token/answer-cap hit score zero. Every source item remains in the item denominator. Forced closure of the thinking prefix at B2048 is the accepted continuation policy; it does not itself discard the subsequent answer. A failed byte, binding, parity or completeness check fails the family and stops the chain.

| Type | Items | No-information score (%) | Chance (%) |
|---|---:|---:|---:|
| object_counting | 385 | 62.2 | — |
| object_abs_distance | 290 | 29.5 | — |
| object_size_estimation | 293 | 18.3 | — |
| room_size_estimation | 98 | 33.1 | — |
| object_rel_direction_easy | 192 | 51.6 | 50 |
| object_rel_direction_medium | 194 | 35.6 | 33.33 |
| object_rel_direction_hard | 192 | 30.7 | 25 |
| obj_appearance_order | 246 | 25.0 | 25 |
| object_rel_distance | 279 | 25.0 | 25 |

`SUMMARY.json` places `no_information_pct` beside each new-family type score. The registered room denominator remains **100**, including the two deferred rooms, and the summary reports 98 rooms with items and two deferred opaque room IDs. The source gives those deferred rooms no questions. Their unknown per-type item counts are not invented: item accuracy uses exactly the 2,169 supplied items, while room coverage uses 98/100.

## Operator commands

These are the exact prepare/submit/fetch/pair commands for the candidate, **not authorization to bypass the naming blocker above**. They were not executed. Run them only after the kit satisfies the required naming policy and the operator has uploaded the two pinned assets. No official benchmark family is available.

```bash
cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python
L=$PWD/kit/launcher/orchard_launcher.py
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh

prepare_read() {
  local label=$1 run=$2 step=$3
  shift 3
  local token=a$("$PY" -B -c 'import secrets; print(secrets.token_hex(5))')
  local dest=$PWD/kit/build/$token
  "$PY" -B "$L" prepare --run "$run" --namespace 8865619b --step "$step" \
    --families "$@" --token "$token" --destination "$dest" || return
  printf -v "$label" '%s' "$dest"
}

prepare_read D0_200 359fcc3c 200 r0dev
prepare_read D0_100 359fcc3c 100 main away forward r0dev
prepare_read H1_100 17c4ffa4 100 main away forward r0dev
prepare_read H1_200 17c4ffa4 200 main away forward r0dev

submit_read() {
  local dest=$1 cmd
  cmd=$("$PY" -B "$L" submit-command --destination "$dest") || return
  timeout 300 bash "$OSSH" "$cmd" < "$dest/BATCH.sh" \
    > "$dest/SUBMIT.out" 2> "$dest/SUBMIT.err" || return
  "$PY" -B "$L" record-submission --destination "$dest"
}
```

Submit each only when its exact `.done` receipt exists and the allocation is authorized. Execute these calls separately as reads become eligible; they are not a request for concurrent jobs:

```bash
submit_read "$D0_200"
submit_read "$D0_100"
submit_read "$H1_100"
submit_read "$H1_200"
```

Each call performs test-only admission and submits one H100 on `general`, 16 CPUs, 200G, six hours, no requeue. Family execution is sequential in fresh processes. Runtime, base, export and GPU admission remain inherited.

After each corresponding job finishes:

```bash
"$PY" -B "$L" fetch --destination "$D0_200"
"$PY" -B "$L" fetch --destination "$D0_100"
"$PY" -B "$L" fetch --destination "$H1_100"
"$PY" -B "$L" fetch --destination "$H1_200"
```

For a return ≥20 MB, `fetch` retains the verified exit receipt and prints the exact transfer command for the operator to register with the IO governor. Execute that governed command; do not loop or bypass the governor. Then authenticate and extract each downloaded archive:

```bash
"$PY" -B tools/unpack_return.py --destination "$D0_200"
"$PY" -B tools/unpack_return.py --destination "$D0_100"
"$PY" -B tools/unpack_return.py --destination "$H1_100"
"$PY" -B tools/unpack_return.py --destination "$H1_200"

"$PY" -B h1pair.py --step 100 \
  --d0 "$D0_100/fetched/x/ITEMS.jsonl" \
  --h1 "$H1_100/fetched/x/ITEMS.jsonl" --output evidence/PAIR_100.json
"$PY" -B h1pair.py --step 200 \
  --d0 readk/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl "$D0_200/fetched/x/ITEMS.jsonl" \
  --h1 "$H1_200/fetched/x/ITEMS.jsonl" --output evidence/PAIR_200.json
```

`h1pair.py` accepts multiple files per side so D0's existing three-family m200 return can accompany the new r0dev-only return. It normalizes `a7` to `r0dev` locally, pairs shared `(family,id)` keys, reports unmatched counts, and refuses duplicate keys, mismatched task/room metadata, invalid scores, wrong budgets or wrong steps. It computes H1-1 minus D0 for each family/type using the reference bootstrap: item-weighted means, complete physical-room resampling with replacement, 10,000 draws, seed 20261115, linearly interpolated percentile 95% intervals. An interval whose upper endpoint is strictly below zero flags harm only for one of D0's seven registered F1 types. Absolute distance, room size and appearance are reported without becoming F1 stopping types.

For an unscheduled H1 stop, prepare with `--run 17c4ffa4 --step <actual optimizer step> --generation mstop` (or `mstopB`/`mstopC`) and the same family arguments. The `.claim` binds that generation to the actual step. `h1pair.py` intentionally compares registered m100/m200 pairs only.

## Validation

`evidence/D0_TESTS.log` records all **53 existing tests passing**. `evidence/NEW_TESTS.log` records **24 additional tests passing**: closed identities, stop claims, ordered four-part digest admission, embedded-bootstrap validation, family subsets, deterministic asset reconstruction, full local asset staging, exact prompt/answer/index preservation, scorer zero cases, complete denominators, opaque new names, return retention/extraction, and synthetic/real pairing.

`evidence/RUNTIME_FIXTURE.json` records a separate four-item integration through the actual evaluator worker, B2048/B4096 derivation, token audit and mergers, with actual RGB frames. The engine, model staging and GPU parity probe are mocks. It uses a local event loop without sockets. This proves interface integration, not GPU prompt/pixel parity or vLLM execution.

`evidence/BIND_100_main.log` and `BIND_200_main.log` prove exact main-family prompt bytes against the real D0 m200 return and the accepted evaluator digest `d27804f7…`. The local reference lacks away/forward payload directories, so fresh binds for those two families are not claimed; the unchanged functions and existing suite cover their preserved code. `evidence/D0_SELF_PAIR.json` pairs all 1,825 real D0 m200 items with themselves: every type has delta 0 and interval [0,0].

```bash
(cd readk && PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest discover -s tests -p 'test_*.py' -v)
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest discover -s tests -p 'test_h1read.py' -v
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -B tests/runtime_fixture.py
```

Tests install the offline process/socket guard before kit imports. Fixtures remain on disk; `REMOVAL_CANDIDATES.md` lists their paths. No cleanup command ran.

## Estimated time and local space

These are **estimates**, not measured H1 reads. `readk/REPORT.md` reports 52m51s for 1,825 items, including 47m11s generation, and 497.6s staging. Scaling by 2,169/1,825 estimates about 62m49s for the additional family's bind/generate/merge work. Scaling all 3,994 items gives about 115m40s plus staging. Allow **125–145 minutes for all four families** and **75–90 minutes for r0dev only**; full hashes, f32 visual-token differences, answer lengths and model staging remain uncertainties.

Budget approximately **275 GB additional `/tmp` space** for all four families: the reference's 220 GB estimate plus a fourth base/export model copy, the 0.80 GB extracted asset and working margin. Start with at least **500 GB free**, retaining the 200 GiB floor. For r0dev-only, allow approximately **150 GB additional**, starting with **375 GB free**. The actual per-family admission checks remain authoritative. The inherited 512 MiB expanded/sub-90 MB compressed return limits remain enforced; oversize returns fail rather than silently omit journals.

## Choices

- Preserve the accepted D0 duplicate layout for main/away/forward. Apply f32 `spread` only to the new population, as required for its 32-frame input. Changing the existing families would invalidate the requested byte-identical D0 binding.
- Retain all source rows despite repeated qids. Use opaque source-line-qualified IDs and keep the reversible map on Trinity.
- Preserve the registered 100-room coverage denominator, while retaining the source's exact 2,169-item scoring denominator; do not fabricate questions for deferred rooms.
- Use the reference's ON16k/B2048/B4096 answer policy, with explicit zero scoring for new-family refusals, nonanswers and answer-cap hits. Use chance for appearance and relative distance.
- Preserve D0's binder and raw journal content. Report the resulting literal anonymity conflict instead of asserting an unsupported exception. The packet is not fully submit-ready under that requirement.
- Keep the reference kit, input copies, test fixtures and failed fixture directories. No files were deleted. Only generated evidence and ledgers changed under `readk/`; its pinned source files retain their hashes.
- Use the supplied measured D0 timings for planning, without claiming that a live export, upload, credential, runtime archive or GPU read has been verified.
