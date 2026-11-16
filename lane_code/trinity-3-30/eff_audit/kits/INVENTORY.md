# Kit and tool sprawl inventory (eff_audit/kits, 2026-11-16 ~11:20Z, trinity-3-30)

Sources read (read-only): `/scratch/jjyeung/distill_sync/stage/{trinity-1-3,trinity-1-18,trinity-3-30,orch_n30}/` (code_sync filtered copy, 25,037 files, 264 MB), local lane folders `/scratch/jjyeung/orch_n30/*/`, STATUS.md files under `.../orch_n30/events/*/`, recovered orchestrator orders in `/scratch/jjyeung/orch_n30/seal_plan/recovered/evalx/written/`. Paths below are relative to `stage/` unless absolute. No git, no ssh, no deletion.

## 1. Kit families (who builds Orchard jobs, and how)

| Family | Origin | Forks seen (lane: path) | Parts |
|---|---|---|---|
| A. evalx "milestone" launcher | orch_cd/evalx (dead 2-18) | evalx27 `work/kit/launcher`, `work/kit/build/pass2/launcher`, `work/kit_revsi/build/f1/{baseline,empty}`; cont_ops `work/d0/readk/kit/launcher`; review_d0r `work/rk/kit/launcher`; review_d0r2 `recon1/kit/launcher`; trin_read `kit_src/launcher` (1-18); native_r4 `builds/01_vsti/code/...`; k1_partb_rh + k1_ops6 `reference/...` copies | orchard_launcher.py, orchard_job.py, orchard_stage.py, orchard_results.py, stdout_transfer.py, chain_save.py, return_io.py, trace_runtime.py, export_stage.py, ORCHARD_ASSETS.json, TRANSPORT.json, MODELS.json |
| A'. evalx native | orch_cd/evalx `orchard_native/` | native_r4, k1 (via `job_support.H.native()`) | native_launcher.py (string-patches A's batch template), native_stage.py, native_pin_graph.py, native_job.py, native_bootstrap.py |
| B. tree/student kit | orch_cd/leg_s1_tree `launch_s1/` | tree_rebuild build2/3/3b/4/5 (3-30), tree_rebuild_w (1-3, same kits), review_tree `lane3`, cont_ops `d0/a2`, D0 job B | job.sh, f.sh, b/{a,e,l,s,v,w,opaque,gcsput}.py, BUILD.json (r2-kit-v1), ANON_OK.json, k/*.json |
| C. k1 package | k1_ops3/4/5 (1-18) → k1_ops6 (3-30) | — | build_package.py, batch_entry.py, job_support.py, phase_worker.py, stage_job.py, make_manifest_v2.py, manifest_v2 |
| D. Trinity-side reader | trin_read | build, build_t5, build_t6 (1-3 and 1-18) | trinity_read.py (69-76 KB), namespace_worker.py, compare_tokens.py, launch_gcs.py |
| E. GT builds | gt_build, gt_rasters (1-18) | — | launch.py, rung1_build/{gov_register.py, stream_copy.sh, r1aws.py} |

## 2. Variant counts (sha256-distinct, staged copy; test-run copies excluded where noted)

| Tool | Copies | Distinct | Note |
|---|---|---|---|
| orchard_launcher.py | 9 (+2 on 3-30 local) | 9 (+2) | milestone→evalx27: 432 changed lines; evalx27→readk: 149; evalx27→kit_revsi: 20 |
| orchard_results.py | 5 | 5 | 7.6-20.9 KB |
| chain_save.py | 5 | 5 | 5.3-6.8 KB |
| orchard_job.py / orchard_stage.py | 4 / 4 | 4 / 4 | |
| export_stage.py | 2 | 2 | added in readk fork |
| trinity_read.py | 14 | 14 | incl. test roots; 3 live builds (build, build_t5, build_t6) |
| job.sh | 17 staged, 220 local | 17 / 57 | ~7 templates after normalizing the job-name token |
| f.sh | 12 | 12 | CPU general-partition variant |
| gcsput.py | 51 local | 2 | only diff: `range(4)` retries vs `range(1)` |
| opaque.py | 85 local | 1 | vendored, identical |
| e.py / l.py (same kit) | — | identical (506c3adc) | duplicate file inside one kit |
| storage.py | 20 local | 2 | |
| governed-stream launchers (call register.py) | 29 files | ~25 distinct | see §3 |
| ORCHARD ledgers | 14 files | 5 schemas | see §4 |
| pin/manifest JSON | >40 file names | ≥25 formats, most schema-less | see §5 |

Re-implemented helpers across staged non-test .py (files defining the function / distinct files): `sha|sha256` 283/179; `pin|checked` 132/65; `identity` (proc) 66/40; `canonical` 44/26; `atomic_json|write_json` 35/20; `unpack|extract` 33/20.

## 3. What every Orchard job / transfer re-implements

| Concern | Implementations found | Evidence |
|---|---|---|
| Governed stream (stop reader, wait `comm==ratelimit`, register.py, wait, verify sha, rename record) | 1-18 k1_ops3 `t2_launch.py, t3_launch.py, w544_launch.py, ark_pull_launch.py, partb/{meta_pull,bundle_up,bundle_up_p10,anchor_up}_launch.py`; 1-3 native_r4 `streams/{launch_gated,launch_push,launch_push_file,launch_tar}.py`; trin_read `launch_pull.py, launch_pull2.py, launch_curl.py, build_t6/launch_gcs.py, streams.sh, streams2.sh`; evalx27 `media_stream/{launch_read,launch_upload}.py`; gt_build `launch.py`; gt_rasters `gov_register.py` (pv-based, obsolete); 3-30 k1_ops6 copies | `bundle_up_launch.py` vs `_p10.py`: only `LANE` and `'--priority', '30'`→`'10'` differ; `anchor_up_launch.py` differs only in SRC/BYTES/OBJ/LANE. trin_read STATUS: "rt0 refused 06:10Z (launcher exec changed comm after a pause). Fix work/launch_pull2.py (no exec)" |
| Batch rendering + opaque job name | A: `render_batch` heredoc; A': string-replace of A's template (`"('evalx_'+job": "('evalx_native_'+job"`); B: job.sh/f.sh templates in build_kits.py; C: build_package.py | Token schemes differ: `'a15_cot_ap'+digest(...)[:12]` (launch_r2/build.py:242), `secrets.token_hex(4)` (pd_arm_configs.py:112), regex `[a-z][0-9a-f]{8,32}` vs `[a-f][0-9a-f]{8,32}` (launcher forks line 36) |
| Staging inputs into job /tmp | A orchard_stage.stage, A' native_stage.stage, B b/s.py stage_inputs, C stage_job.stage, readk export_stage | ORCH order 11-14 08:36Z: pilot 169477 failed `[Errno 17] File exists ... runs/469ddece` because native stage and export stage created the same folder |
| Pin checks | A ORCHARD_ASSETS + plan_sha256; A' native_pin_graph.py (34 KB); B a.py/v.py + BUILD.json; C manifest_v2; readk CODE_PINS/INPUT_PINS_T5/T5B/T6 | ORCH 11-14 17:27Z: "Faults 4 and 5 are one kind: a file changed and one of several places that record its hash was not regenerated." |
| Return upload | A orchard_results.publish → pool + stdout_transfer over ossh; B gcsput.py to Trinity-minted session URIs; chain_save budgeted tar; readk return_io.py; D0 `gcs_*.done` markers | ORCH 11-14 03:31Z: export stream died after a 1 KB/s governor pause; recovery required adding ranged-reopen to "the transfer helper" in that lane only |
| GCS fallback | A orchard_results "independent pool/GCS copies"; B gcsput; trin_read launch_gcs.py; k1 stage_job gcloud describe by generation | each with own retry count (gcsput 4 vs 1) |
| Ledger | per-lane `work/ORCHARD_LEDGER.jsonl` on the lane's node | schemas: `{meaning,token,utc}` (cont_ops, native_r4); `{meaning,object,token,utc}` (k1_ops3); `{destination,gcs,job_name,meaning,pool,token}` (readk, review_d0r*); `{gcs,gpus,job_name,kit_sha256,...}` (evalx27); pending-ledger 15 keys (k1). Ledgers on 2-18/2-28 are unreadable now |
| Watch/poll loops | cont_ops `loop5.sh, loop7.sh, watch_b.sh, c6/q3.sh, poll.sh, poll2.sh`, d0/a2 `w1/w2/w2b/w2c/w2loop/watch_a2.sh, q1-q5.sh`; native_r2 `loop.sh, loop2.sh`; trin_read `cardpoll/poll.py`; 19 `inv*.sh` Orchard probes | cont_ops STATUS: "tmux cont6_watch runs work/d0/jobB/c6/loop7.sh, one ossh call of c6/q3.sh every 10 min" |
| CPU rehearsal / coverage | k1 `RH13_SSH*.err` r1-r5, `r5_union_summary.txt`; evalx native_cpu_replica, native_local_check; trace_runtime.py; tree mutation_proof (5,581 files) | ORCH 11-15 02:49Z: "This is the fourth pilot lost to a line that no CPU run had executed" |
| Fork diff accounting | readk `DIFF.md` (line-range table vs evalx27 `f42aa1a4`), trin_read `kit_src/DIFF.md`, PATCH_MANIFEST.json | every fork needs a BEYOND/PATH table and an independent review because constants live in code |

## 4. Measured losses tied to kit plumbing

- evalx native pilots: order for pilot 1 at 2026-11-14T08:15Z, pilot 9 result ~2026-11-15T07:20Z (≈23 h, 9 Orchard pilots). Plumbing failures: 169477 directory collision (layout not rehearsed), 169537 stale code-object member vs pin, 169589 runtime-spec worker pin, 169687 wrong call argument on a never-executed line; pin audit found #35 worker-entrypoint pin "only seal_s23.py:111 and build_inputs.py:169 ever wrote it; every later builder deep-copies the old assets". (`seal_plan/recovered/evalx/written/2026111{4,5}T*_ORCH_*`)
- k1 package: 5 CPU rehearsal rounds (`k1_ops6/src118/RH13_SSH{,_r2..r5}.err`), 7 briefs (`build/BRIEF..BRIEF6B.md`), STATUS `PREPARED_WITH_GAPS_NOT_SUBMITTABLE`.
- tree kit: build2→3→3b→4→5 plus `kits_first/second/third/fourth/before_shared_rules/before_test_fixes`, `package_*` ×4, `retained_*` ×3 (`/scratch/jjyeung/orch_n30/tree_rebuild/work/build4/`, 90,225 files, 3.9 GB). `pins.py` hard-codes shas and `str.replace`s an old pin inside `r2_grammar.py`.
- Governed-stream launcher bug (exec changes comm) found and fixed in one lane only (trin_read 06:10-06:28Z); other lanes' launchers each carry their own version of the same 15 lines.
- Review lanes copy whole kits to reconstruct them (review_d0r2 `recon1/`, `recon2/`, `snap1/`, `full/`; review_tree `lane3/work/build3` duplicates tree_rebuild build3).

## 5. Pin manifest formats (staged, non-test)

Schema-tagged: `r2-kit-v1` (BUILD.json ×24), `evalx-orchard-existing-assets-v1` (ORCHARD_ASSETS ×11), `s1-routing-materialization-v1`, `r2-family-manifest-v1`, `s1-launch-build-v1`, `s1-composite-binding-acceptance-v1`, `student-generation-manifest-v1`, `s1-warm-start-durable-evidence-v1`. Schema-less: ASSETS.json (3 key sets), BATCH.pin.json, RH_RESULT.pin.json, TRACE.pin.json, BUILD.json `{encoding,payload,sha256}`, BINDING.json (2 key sets), SOURCE_PINS, CODE_PINS (2 key styles: `evaluator/x.py` vs `x.py`), SCORER_PINS, PROMPT_PINS, PINS.json, INPUT_PINS_T5/T5B/T6, LABEL_SOURCE_PINS (keyed by `/scratch/jjyeung/orch_cd/...` absolute paths on dead trinity-2-18), SEALED.json, V314_MANIFEST, PATCH_MANIFEST, FINAL_IDENTITY (list), SHA256SUMS.txt.

## 6. Minimal shared kit (proposal)

One package `orchkit/` committed to agent_project_distill (`tools/orchkit/`), sealed per epoch like collector/, stdlib-only, Python 3.6-compatible (Orchard bootstrap constraint seen in b/s.py):

1. `orchkit/pins.py` + one manifest format `orchkit-pins-v1`: `{schema, created_utc, commit, entries:[{role, logical_path, bytes, sha256, source:{kind:file|gcs|orchard, uri, generation}}]}`. Generated only by `pins.py build` from files; every other record (CONFIG, BATCH, runtime spec, family) embeds only the manifest's sha256, never a per-file hash. Kills the "several places record its hash" class.
2. `orchkit/launch.py` (one launcher): `prepare --kit DIR --config CONFIG.json` renders job.sh from one template (partition, gpus, time, signal, cpu-only guard as config fields), mints the opaque name with one function (`a15_cot_ap` + `secrets.token_hex(6)`), appends the ledger row, refuses dirty trees; `submit`/`status`/`fetch` via ossh.sh. Constants (step, artifact sha, pool, families) move from code to CONFIG validated by a JSON schema, so a new read is a new config, not a fork with a DIFF.md.
3. `orchkit/stage.py` (one stager, job side): typed entries from the pin manifest (tar/parts/gcs-generation/orchard-path), one `extract_stream` with collision policy declared per destination, sha check on every entry, `--rehearse` mode that lays out real logical paths with zero-byte stand-ins on CPU.
4. `orchkit/ret.py` (one return path): chain_save budget + pool publish + gcsput session upload as fallback, one receipt schema, ranged reopen on reset.
5. `orchkit/govstream.py` (one governed-stream launcher, Trinity side): promote native_r4 `launch_gated.py` shape — `govstream.py --lane L --bytes N --sha S|- --prio P --kind pull|push --out F -- CMD...`; never execs; verifies, writes RECEIPT, renames record. Replaces ~25 launchers.
6. `orchkit/reader/` harness: one `read.py --export ... --families ... --step N` with pluggable scorers (direct, native, paired); the trinity_read.py / chain.py / paired_read.py lineage collapses into it.
7. One ledger on NFS: `/data2/.../orch_n30/ORCHARD_LEDGER.jsonl` (small appends, flock), schema `{utc, token, job_id, lane, meaning, kit_pins_sha256, config_sha256, partition, gpus, pool, gcs}`; per-node ledgers become caches.
8. `orchkit/watch.py`: one Orchard poller (squeue/sacct + named files + metrics tail) writing a state file and one event on change; lanes stop writing loopN.sh/qN.sh.
9. Shared `orchkit/util.py`: sha, canonical json, atomic write, proc identity — the 179/65/40/26/20 duplicated definitions.

Migration order (cheapest first): govstream.py (pure Trinity, no seal impact) → ledger → watch.py → pins format for new kits → launcher/stager for the next read kit (readk fork as the reference) → tree kit B at its next epoch. Existing sealed kits stay byte-identical until their next epoch (provenance rule).

## 7. Risks

- A shared launcher becomes a single point whose change needs review for every family; mitigate by sealing orchkit per epoch and pinning its manifest sha in each kit.
- Python 3.6 on Orchard bootstrap vs 3.9+ features (`Path.is_relative_to` used in A) — shared code must stay 3.6-safe or ship two entry points.
- Main project shares the Orchard account; job-name opacity and the "no project word" rule must be enforced in one place (launch.py), with the ANON check moved there.
- NFS ledger adds tiny /data2 writes; keep appends < 1 KB, one per submission.
