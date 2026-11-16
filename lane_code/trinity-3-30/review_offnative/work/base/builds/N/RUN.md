The worker is NOT READY for production on either benchmark or reader. CPU fixtures validate native control flow and dense-frame preparation. They do not establish production-CONFIG equivalence. No submission or upload was made.

Run commands from this build directory. Use a fresh output directory for every test or rehearsal.

```bash
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
"$PY" -B -m pytest -p no:cacheprovider kit/tests --basetemp=work/pytest_operator_fresh -q
"$PY" -B -m offnative.census work/operator_revsi_harness harness out/operator_revsi_harness.json revsi999t32
"$PY" -B -m offnative.census work/operator_revsi_e2e e2e out/operator_revsi_e2e.json revsi999t32
"$PY" -B -m offnative.census work/operator_vsi_harness harness out/operator_vsi_harness.json vsibench5130
"$PY" -B -m offnative.census work/operator_vsi_e2e e2e out/operator_vsi_e2e.json vsibench5130
```

`original` is the default G3T source for both readers. For ReVSI, the worker reconstructs the official 64-frame clip and selects geometry at `i64.index(i)` for each registered 32-frame source index. It decodes positions 0–63 of the 64-frame clip; it does not interpret source-video indices as clip positions. The registration can repeat source indices for short original videos. Both index lists and the selection positions remain in `out/REVSI_DENSE_MAPPING.json`.

The mapping binds both clip hashes and its own SHA256. The local `A.tar` is a zero-byte placeholder at the recorded check. Hashes therefore remain pending, and production binding refuses it. Once the complete local archive is available, this command extracts only the expected 604 regular files, enforces the 4 GB build cap and scratch reserve, hashes both sets, and records RGB correspondence for every video. It reads no clips from `/data2`.

```bash
df -h /scratch
"$PY" -B -m offnative.media \
  --archive /scratch/jjyeung/orch_n30/b07_offread/work/stage_rv/A.tar \
  --destination work/revsi_clips_operator_fresh
```

This command uses the saved registration in `out/REGISTERED_FRAME_INDICES.json`; it does not reread the shared metadata. `out/REVSI_PIXEL_CORRESPONDENCE.json` records all 32 matched RGB mean absolute differences and all 32 neighbouring-frame comparisons per video. A synthetic compressed-video test exercises the check. The real 302-video check has not run.

`out/REVSI_MEDIA_MANIFEST.json` assigns the accepted 261 anchor clips to `/project/community/jjyeung/okh7/313db5a47f11ff0c/`. It assigns the 41 additional anchor clips and all 302 dense clips to `/project/community/jjyeung/okh7/d46dd56e669a050f/7b5d2192.tar`, using `a/<name>.mp4` and `b/<name>.mp4`. The stager verifies the remote archive pin and every staged file. An archive can also contain the accepted anchor clips; those are read from the accepted pool. Remote upload completion and the remote archive's own hash/size/transfer receipt remain owner inputs. The local 604-member archive and remote archive need not have the same whole-file hash.

For VSI-Bench, `out/VSI_COHORT.json` contains all 5,130 question-only rows. `out/VSI_MEDIA_MANIFEST.json` preserves the direct kit's 288 full-video names, aliases, and hashes; its source manifest lacks byte sizes. `out/VSI_NAME_INVENTORY.json` contains 845 distance-name/video pairs with no unresolved templates. Dense sampling keeps the exact 32 floor-uniform model anchors, then adds the farthest unused candidates from the floor-uniform 64-frame grid until it has 64 frames. Ties select the earlier frame. Both readers receive this frame set and its anchor positions; the e2e reader invokes its towers inside `generate`.

`clip32` is a labelled fixture diagnostic only. Binding, admission, worker execution, and reporting refuse it for claimed reads. Model anchors remain 32 with duplicate layout. Offkit admits frame overrides, but the native runtime separately refuses unsupported 64-model-anchor reads.

An operator can prepare production only after resolving `out/OPEN_INPUTS.md`:

```bash
"$PY" -B native_read.py prepare --benchmark revsi999t32 --export step544 \
  --reader "harness:$FREEZE_SHA256" --freeze-file "$FREEZE_FILE" \
  --frames 32 --frame-layout duplicate --g3t-source original \
  --original-mapping out/REVSI_DENSE_MAPPING.json \
  --ledger work/OFFICIAL_READ_LEDGER.jsonl --mode production \
  --inputs "$INPUT_MANIFEST" --destination work/read_operator_fresh
```

For e2e, use `--reader e2e:<manifest-sha256> --e2e-manifest <file> --eat1-report <file>` with the same dense mapping. Offkit requires EAT-1 PASS. For VSI-Bench, select `--benchmark vsibench5130`; it uses the full videos and needs no ReVSI mapping. A D0 export uses `--export done:<file> --init-selection <file>`. The selection must include `selected_sha256`, the registered `init_rule_sha256`, a valid `selected_step`, and `d0_ended.reason` plus `d0_ended.event`. Offkit owns the training layout; callers cannot supply an `export_layout`.

Every production input role needs a safe relative logical path, SHA256, byte count, and uploaded source. Inputs above 20 MB need a governed transfer receipt. ReVSI also needs `revsi_media_manifest`, `original_mapping`, and a pinned `revsi_archive` role. Bootstrap stages its clips under `work/runtime/revsi_media`; R retains the export/runtime gates and hash-checked media copies. Additional runtime assets, labels, original proof inputs, and the loaded e2e entry must resolve within the staged namespace.

`vendor/ACTIVE.json` selects immutable snapshots for b04, R, C8r, V1c, and the trainer tree. Each snapshot has a `PIN.json`. The following command deliberately creates a new content-addressed snapshot, updates the active selection, and writes added/removed/changed names and unified text diffs to `out/VENDOR_REFRESH.json`. For `OFFKIT`, the command refreshes external module pins without copying the owner package; its recorded diff includes old and new hashes. It runs before normal startup pin verification. It does not edit the lane or delete any snapshot. Rebuild and retest before shipping a refreshed selection.

```bash
"$PY" -B -m offnative.vendor --refresh R OFFKIT
```

Offkit is imported unchanged and is not copied into the new bundle. `out/OFFKIT_EXTERNAL_PINS.json` pins every owner module and startup verifies those bytes. An extracted bundle uses `OFFNATIVE_ROOTS=r.json`; its environment must provide the pinned offkit package, normally at `d/00/offkit`, before bootstrap. Portable CPU tests explicitly supply that external dependency through `PYTHONPATH`. Weights, runtime environments, media, tokenizer assets, and proof inputs are separate pinned assets.

The required production-CONFIG rehearsal has not run. `out/N3_PRODUCTION_REHEARSAL.json` records the blockers. The fixture substitutes model prefill, token sampling, and tower arrays; those changes exceed transport. The launcher requires a genuine `REHEARSAL.json` with PASS, `only_transport_changed: true`, and the exact CONFIG and packet hashes before it prints a submission command. Fixture evidence must never be relabelled as that receipt.

The seven worker phases are stage, frames, towers, proof, canary, read, and score. The original-export proof precedes official decoding. Reports use the verified full offkit BINDING and preserve model answer bytes. Primary refusals score zero; harness fallback and room-unserved arms remain secondary. An emitted operand outside the question-derived cache remains a recorded native refusal.

`submit-command` only prints an argv; `record-submission` reads a saved, unambiguous `SUBMIT.out` and locks the one-export ledger. The job name is `a15_cot_ap` plus 16 hex characters. The proposed resources remain one GPU, 16 CPUs, 200 GB, and `/dev/null` output. The watchdog reserves 600 seconds for returns. The opaque packet receives a byte-name scan; BINDING and token meanings stay local. Fetch authenticates job, token, binding, CONFIG, packet, and archive identities before R's verifier runs.

```bash
"$PY" -B native_read.py fetch --destination work/read_operator_fresh --channel pool
"$PY" -B native_read.py fetch --destination work/read_operator_fresh \
  --return-archive "$RETURN_ARCHIVE" --return-receipt "$EXIT_RECEIPT"
"$PY" -B native_read.py report --destination work/read_operator_fresh
```

Future transfers above 20 MB must use the existing IO governor. Keep transfers serial, poll at most once a minute, and stop after an unexpected transfer failure. Trinity limits remain 8 MB/s for shared reads or internet traffic, 4 MB/s for shared writes, and 18 MB/s aggregate per user. This build executes no network, SSH, submission, upload, or remote fetch.

The job-170056 identity proof is reduced under the pinned `out/PROOF_MASKS_LOST.json` declaration. Its five distance mask files were lost with an unreachable node. Camera items retain token, call, response, and answer equality with independently recomputed responses. Distance items retain token, call, and answer equality plus served-query/response digest equality, but lack independent re-serving from the original masks. A changed served query or response cannot retain its pinned digest; a backend change affecting items outside these five is caught only by the canary. The CPU receipt uses forced tokens and recorded distance query digests; it does not establish model-logit equality. Reduced mode requires the exact declaration hash and selected distance keys; absent or changed loss records fail closed.

```bash
"$PY" -B -m offnative.replay out --mode reduced \
  --lost-masks out/PROOF_MASKS_LOST.json \
  --lost-masks-sha256 f1ba60b7d987d57420ddd457428adbcb8069e508fd1bc00ac9c5498add1a5362
```

Production proof assets must explicitly set `proof_mode: reduced` and `lost_masks: {path, sha256}` with that pinned record. Generation still runs the original model and must match the selected token, call, answer, and digest identities. Camera replay remains independent. Without this declaration, the full proof requirements apply.
