ReVSI × harness: NOT READY; ReVSI × e2e: NOT READY; VSI-Bench × harness: NOT READY; VSI-Bench × e2e: NOT READY.

Run CPU checks from this directory. Choose fresh opaque RAM directories; never reuse a pytest basetemp. Keep RAM scratch output below `/dev/shm/b07_n7` and below 4 GB. Production-root rehearsals use fresh `/tmp/a_900000_<12 hex>` roots, each below 20 MB.

```bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
RUN_ID=$("$PY" -B -c 'import secrets; print(secrets.token_hex(6))')
export ROFF2_ROOT=/tmp/a_900000_$RUN_ID
"$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=/dev/shm/b07_n7/a${RUN_ID}_101 -q
"$PY" -B -m offnative.census /dev/shm/b07_n7/a${RUN_ID}_102 harness /dev/shm/b07_n7/a${RUN_ID}_102.json revsi999t32
"$PY" -B -m offnative.census /dev/shm/b07_n7/a${RUN_ID}_103 e2e /dev/shm/b07_n7/a${RUN_ID}_103.json revsi999t32
"$PY" -B -m offnative.census /dev/shm/b07_n7/a${RUN_ID}_104 harness /dev/shm/b07_n7/a${RUN_ID}_104.json vsibench5130
"$PY" -B -m offnative.census /dev/shm/b07_n7/a${RUN_ID}_105 e2e /dev/shm/b07_n7/a${RUN_ID}_105.json vsibench5130
```

ReVSI model prompts use the 32-frame clip's indices 0..31, FPS, timestamps and total frame count. `GEOMETRY_FRAMES.json` alone supplies dense-clip slots to V1. Selected geometry is relabelled into model coordinates after conversion. The e2e payload separates model metadata from geometry indices; its loaded-entry prompt audit runs before generation. `clip32` remains diagnostic-only.

Both unserved arms use the primary's `ThinkingBudget` and registered 2048 thinking + 64 answer policy, including its callback accounting, call limit and outer token cap.

Reduced harness proof requires the pinned job-170056 mask-loss declaration. Camera items require token, call, served-response and answer equality, with independent response replay. The five distance items are reported only. Their token, call and answer comparisons are recorded where decoding reaches them; missing masks are never loaded. Distance served-response equality, served-query digests, independent re-serving and distance identity are not required or established. E2E distance items are reported in both full and reduced modes. CPU fixtures do not establish model-logit equality.

Production preparation requires the inputs in `OPEN_INPUTS.md`. For a harness read, provide the signed freeze and its hash; for e2e, provide the artifact and EAT-1 report. The following prepares files only:

```bash
"$PY" -B native_read.py prepare --benchmark vsibench5130 --export step544   --reader "harness:$FREEZE_SHA256" --freeze-file "$FREEZE_FILE"   --frames 32 --frame-layout duplicate --g3t-source original   --ledger /dev/shm/b07_n7/a${RUN_ID}_106.jsonl --mode production   --inputs "$INPUT_MANIFEST" --destination /dev/shm/b07_n7/a${RUN_ID}_107
```

VSI-Bench harness preparation creates 17 whole-scene child jobs with the recorded planning allowances. `SHARDS.json` binds the full cohort and each child's IDs, CONFIG, token, packet and return. Each child requests six hours and retains a 600-second return reserve. Complete a genuine transport-only `REHEARSAL.json` for each child's exact CONFIG and packet before `submit-command` will print its argv. Record each submission under the same parent and ledger; a shard group spends one registered read. The builder submits nothing.

Fetch each child into its prepared directory. `merge-shards --destination PARENT --returns CHILD...` authenticates the returns and requires the exact, duplicate-free full ID union for every arm. A cutoff writes `PARTIAL.json`, all completed decode records, all completed primary scores and each arm's missing IDs. A completed primary remains available when its secondary decode cannot start. Incomplete unions are refused; they are not official results.

Every job name is `a15_cot_ap` followed by `secrets.token_hex(8)`, validated against `^a15_cot_ap[0-9a-f]{16}$`. The environment uses `A0_ROOTS`, `A0_DEADLINE` and `A0_PACKET_SHA256`; submission uses `--export=A0_PACKET_SHA256=<sha>`, `--account=mt01` and `--no-requeue`. Each forbidden logical path component receives an independent `x` plus 12 random hex digits. The pinned `out/NAME_MAP.json` stays on Trinity. Packets contain a salted digest-to-token table in `x0.json`; the adapter learns virtual spellings from unchanged source bytes in memory. Source loading preserves reader, scorer and item bytes. Named text diagnostics receive random tokens. Scans reject plain, hex and base64 forbidden spellings in packet bytes, decoded member paths, environment settings and submission argv.

The shipped `code.tar` is gzip-compressed despite its `.tar` suffix. An extracted bundle contains `xnames.py`; `native_read.py` installs it before resolving source roots. Offkit must be staged unchanged by its owner. `vendor/ACTIVE.json`, the recorded refresh diffs, `CODE_PINS.json`, `DEPENDENCY_PINS.json` and `SHIP_SHA256SUMS` bind this release.

VSI-Bench has 288 media byte sizes matched by relative path and SHA256 to the supplied size inventory. Files must still pass SHA256 verification in the job. `A2_RESULT.json` was absent: the 604 ReVSI clip hashes, real pixel correspondence and remote archive receipt remain pending. The registered 302-video dense mapping retains its pending hashes.

All four native combinations need complete runtime/export inputs and a production-CONFIG transport-only rehearsal. Harness inputs include the signed freeze, selector, proposal and geometry assets. E2E inputs include the artifact, EAT-1 PASS and a pinned loaded entry with `generate`, `replay` and `prompt_inputs`; the latter must expose the actual processor user-text bytes and frame metadata. Original-export proof assets and authenticated transfer receipts remain required. Offkit stays read-only and owner-supplied. GPU restoration, native-library path resolution and the live namespace have not been validated by CPU fixtures.

The full N7 suite includes the byte-equal reviewer file. Its R4 case necessarily fails because the test itself appends the retired `OFFNATIVE_PACKET_SHA256` export after calling the helper. `kit/tests/test_n5.py::test_R4_current_submit_argv_is_opaque` checks the same forbidden-word assertion against the current API, including the actual export and required job prefix. No reviewer assertion is edited, skipped or marked xfail.

CPU release checks use `validate_n7.py` with a fresh label. `n_prod` and `r_prod` each run a full CPU rehearsal under a fresh production-style root. Large fixture assets and synthetic decode traces stay in RAM. The namespace builder and mapped shell-interpreter target run; transport, mounts and models remain CPU stand-ins.

Both adapters scan every child argument after mapping and before process creation. Media readers resolve private logical names to SHA-keyed job-local files; namespace bind arguments contain only those opaque file paths. `Log.fileno()` reuses one filtered pipe per log, drains it into the job log and closes its descriptors at context exit. The proposal fixture injects its permitted root in test code; the shipped proposal runner contains no RAM-path bypass.

Each packet carries a 32-byte public salt. The builder computes HMAC-SHA256 with the Trinity-only secret over SHA256 of canonical JSON member pins: sorted physical member paths mapped to SHA256 content hashes, excluding `x0.json`, with compact JSON separators. The secret file contains 64 hex characters, which the builder decodes before HMAC. Tokens and aliases use SHA256(salt bytes + UTF-8 logical name). Build-side maps keep their unsalted keys; the runtime reads the salt before learning or resolving names and rejects a table without it. Packaging refuses a missing secret. Tests inject a synthetic secret through `A0_BUILD_SECRET_FILE`; production uses the protected Trinity secret. The secret never enters a packet or report.

The unsalted dictionary gate must find zero keys for every WORDS entry and NAME_MAP name. A public salt still permits dictionary guesses that include that salt; this format does not promise dictionary resistance. In-job file contents are exempt from the naming rule. File paths, child arguments, environment and job names retain their naming checks.

The production-root gate runs from build R: `"$PY" -B -m pytest -p no:cacheprovider tests/test_review_offnative2.py tests/test_prodroot.py --basetemp=/dev/shm/b07_n7/gate_$RUN_ID -q`. Keep the `ROFF2_ROOT` export above. F1/F2 and all three mapping-aware production-root cases must pass; F3 runs in N.
