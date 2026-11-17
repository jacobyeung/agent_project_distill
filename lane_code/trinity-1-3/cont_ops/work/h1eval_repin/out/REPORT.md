# Build stopped: the requested pin-only scope is insufficient

No replacement package was built. No production source was edited. The request says: “If something cannot be done without changing scoring or admission semantics beyond the pin source, stop and explain in REPORT.md.” The production pipeline binds more than the three export files to H1-0. Completing this as a correctly identified m100 evaluator requires resolving the constraints below.

## Constraints that prevent completion

1. **The evaluator unconditionally labels every export SFT, step 544.** `out/production/h1eval/h10/launch.py:186` constructs the shard binding with `lineage='SFT',step=544`. The camera operator’s `submerge.py` copies these fields into the scored curve. A pin-only replacement would label m100 as step 544 and a later RL export as SFT. Correcting the binding changes the evaluator source and its token-independent `evaluator_code_sha256`. Silently patching the binding at runtime would change behavior despite preserving source bytes; this audit does not use that workaround.

2. **The new token conflicts with the unchanged policy receipt under the original builder’s layout.** The builder sets `logical='/scratch/jjyeung/'+token`. `job.py:40` also requires archive destinations to use that token. `job.py:132` checks that the pinned policy receipt authorizes the exact input script paths. The admitted H1-0 receipt therefore authorizes paths under `b01ec87a6f29b`. Adapting the input paths to a new token passes metadata admission but fails that policy check. Regenerating the receipt changes a non-export file and its enclosing archive pins. Keeping the original logical namespace could preserve those bytes, but requires decoupling the package token from archive-destination admission and the original build layout. That additional admission change was not made.

3. **The restore admits only the frozen preparation identity.** `orchard_h10/prepare.py:26` passes the packaged `REQUEST`; `b/parity_kit/stage_restore.py:82` checks its fixed artifact hash. Supplying that request’s artifact hash from the proposed pin file can solve this first check. It does not solve the subsequent equality between the export’s `config_sha256` and the frozen preparation receipt, at lines 90–96. The required value is `84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb`. A different value refuses even when the three export file pins are correct. The m100 artifact is not supplied, so this audit does **not** claim that m100 fails this check. General support for registered exports with different preparation identities would require an explicit compatibility contract beyond the requested three pins. The existing base, architecture, frame-layout, data-receipt, and weight checks must not simply be bypassed.

The first two constraints are demonstrated from the supplied production sources. The third is a demonstrated refusal condition, with m100 compatibility still unknown. A useful next scope would permit accurate export identity in the launcher and a fixed logical namespace independent of the package token, while explicitly retaining the existing preparation-identity restriction unless a separate compatibility rule is approved.

## What the offline audit proved

The authoritative archive is SHA256 `446a432306b8e68ebfa32228071259a61ffd2ec0dada3ec43a664ba342ca540e`. All 924 regular members were extracted into `out/production/` and `out/src/`; every extracted byte matches. `PRODUCTION_SOURCE_SHA256.json` contains the complete per-file inventory. These are unchanged audit copies, not a replacement package.

The builder snapshot differs from production in `job.py`, `operator.py`, and `runner.py`. `DIFF.md` includes every changed Python line, with a complete supplied-tree inventory in `KIT_COMPARISON.json`. The production archive already supports these camera types in this order:

```json
["camera_displacement", "camera_rotation", "camera_movement_direction"]
```

The production export stager and `in/h1read_export_stage.py` are different files. Their `stage_export` and `parse_done` function text is identical. Their run registries and fetch/binding integration differ; `DIFF.md` includes the complete comparison. The supplied stager also requires an external `binding` module. Neither whole module can be treated as a generic drop-in stager without adapting its surrounding contracts.

Nine audit tests passed with the requested interpreter, with no fallback or installation:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B out/tests/test_constraints.py
```

`out/tests/results.txt` contains the results. The tests check production identity and admission, all payload pins, all extracted member bytes, camera selection, fixed export hashes, the current byte-check behavior, the exact restore configuration guard, the new-token policy conflict, and the constant launch identity. The two guard tests execute the original AST statements with controlled metadata; they do not claim a full staging or model run.

One admission detail differs from the task’s description: production `check_inputs` fixes the three export hashes but only requires positive file sizes. Changing an export file’s declared byte count still passes metadata admission. Actual size equality is checked later in `stage()`. A replacement would need to add comparison against the operator pin file before staging, as requested.

## Identities and limits

| Identity | Offline result |
|---|---|
| Production plan | Reproduced: `c6135410e087916095256a8b4c27eaa290f854734f8f4ea37150d34208ce709f` |
| Raw H1-0 `a/1.json` | Reproduced: `1abaf6ca0ebcf7a710292b5d337a59534a5a7ed178c48965a5530da5f9fd041f` |
| Canonical inputs excluding `resume` | Reproduced: `c8da89a80166e5320ed6a3ac76e6398e0eab1bdb10cffc1e13e58fdec5a2e900`; this differs from the raw-file hash by design |
| Item-set identity | Reproduced: `7162af725a9ee3e25e6054ee7d0cffc210c99d10ad8b097c6d3fb5b3319f7910`; matches camera run 170631 |
| Reader identity | Reproduced: `2c2dc559f9ba529ec470be058528f7c12cf4c838f21df829a9c8ba5369d4b3af`; matches camera run 170631 |
| Parity code identity | Reproduced: `64474315cfaf1bd3bdaf2171b20fd7c1d82ff065ca5db107bfccf5862f289bc3`; matches camera run 170631 |
| Production evaluator identity | Computed: `9fb4329d459aff71f0b42e615604437c09580adfb251550eef5dc70bfb33207d` |
| Camera-run evaluator identity | Recorded as `ad9aeb9532074c0471089f622b01591b2a84800828cb958f41a952643e99f690`; does **not** match the supplied production archive |
| Camera export identity | Recorded as `46029ca28948a0c9bf395c4b5796ec0d323d166c87d19901ed11cc6c02cc6915`; not recomputed |

The camera run also used plan `1de19b86d81f2bf9a5b254270e61496e45d454893fe893cbbd325739f74764c8` and raw inputs `7757209963ac9f084fc48d3dc7133159e6c5785c8db3ae970e199c1ab817a3f5`, according to the supplied ledger. It is a different package revision and input selection from the supplied production `2.json`. This distinction is required to interpret the identity tests; the values must not be conflated.

`46029ca2…` hashes the restored export tree, including localized metadata and restored assets. It is neither the source artifact hash nor the whole-tar hash. The export weights, base assets, and live staged environment are absent here. Reading the recorded value from a return is not recomputing it. `binding.json` has a separate hash, recorded in camera journals as `0c41352a772b95f2ddc98fe5d411624717d19226fe797ffacae22328455e13b0`.

The production metadata command is:

```bash
cd /project/community/jjyeung/b01ec87a6f29b
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 03:00:00
```

This writes `2.json` with `passed:true` and `scope:0` for the actual inputs and package on Orchard. It does not execute the real node environment, restore, archive hashing, or empty-root staging. Those checks occur in the allocated job before decoding. There is no existing full empty-root CPU-check command exposed by this production helper; presenting `3.py check` as that proof would be incorrect. No replacement full-check command was implemented after the stop condition.

## Deliverable status

Available: this report, complete source/stager diffs, per-file extraction hashes, machine-readable `AUDIT.json`, nine passing audit tests, and the unchanged extracted sources. `OPERATIONS_DELTA.md` records the operational constraints and measured time basis.

`out/TOKEN` contains an unused token generated with `'b'+secrets.token_hex(6)`. It does not identify a built or admissible package. There is no `out/0.tgz`, replacement package descriptor, implemented export schema, `export_544.json`, `export_TEMPLATE.json`, new-package admission test, four-part staging test, or submission-ready operator runbook. No new-package CPU pass or submit receipt has been fabricated.

No network, SSH, Slurm, GPU, Git, or deletion operation ran. All new files are under `out/`. The next implementation needs the scope decisions above and evidence of m100’s preparation compatibility.
