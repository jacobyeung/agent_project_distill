These drivers prepare packet A’s S2-on CPU proof for fix round 10 (`r1_drv5`). The local fixture reached READY after regenerating all 747 unit rows. Independent final review, content certification, fresh sessions, and the Orchard CPU proof remain pending. Production GO is false.

Work directory: `/scratch/jjyeung/orch_n30/r1_ops/work/drv_p4`. The build uses CPU only and writes only here. It makes no SSH, Orchard, Git, GPU, deletion, or real session-mint call.

| Binding | Value |
|---|---|
| Frozen packet | `/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out` |
| Archive | `p_69d2930d.tar`, 14,182,400 bytes, 37 regular-file members |
| Archive SHA256 | `a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589` |
| Config identity | `fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f` |
| Bundle | `/project/community/jjyeung/okh7/i_69d2930d` |
| Derived kit | `/project/community/jjyeung/okh7/x_69d2930d` |
| H source | `/project/community/jjyeung/okh7/x_3fdda0fb` |
| Source manifest SHA256 | `661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3` |
| Trainer tree SHA256 | `b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b` |
| Run / job | `673bc60f` / `a15_cot_ap673bc60f` |
| Launch switches | `S2=true`, `S1=false`, both `max_own_probability=0` |
| REMOVE list | `records/n.json`, also packaged as `n.json`; 601 rows |
| REMOVE SHA256 | `02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411` |
| REMOVE destination | `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/n.json` |
| VQA cells | room `1.70`; direction `31.19` |
| Session file | `drv_p4/sess_673bc60f.json` |
| V7 store | `/project/community/jjyeung/okh7/s_22b44165/d.db` |
| Unit source | 747 rows; 683 eligible feet rows |
| Selection SHA256 | `5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af` |

`packet_config.py` verifies the frozen archive, every archive member, and the required metadata, config, unit files, and REMOVE file against `SHA256SUMS`. It checks the explicit archive/config identities, both REMOVE copies, the seventh `remove_files` entry, cell values, and S2/S1/dual-zero conjunction. `PACKET_PINS.json` records the pins. `build_drivers.py` renders scripts and decodes the frozen proof program without modifying packet bytes.

`ev1.sh` checks both REMOVE copies against the fixed SHA and requires the config’s exact removal destination. It stages the list through `BINDING.record_files`. The generic `staging_check.py` hashes that new extra-file entry, and evidence creation requires its path in the verified list. `dv1.sh` checks the frozen deriver and both REMOVE copies before source reads, then checks the derived staging entry. `evp1.sh` and `dvp1.sh` report the workers’ REMOVE SHA checks and exit codes.

The CPU selection driver uses H1’s authenticated interpreter `/project/community/jjyeung/latency/envs/fit/bin/python3`. It disables CUDA, bytecode, online model fetches, and multithreaded BLAS. It verifies the trainer archive, H1’s raw native receipt, parent selection, ordered indices, unit bindings, and exact final selection hash. The raw receipt is `i_1be16f28/q_6c18a2bf/o/native/receipt.json`, SHA256 `2e25a01d943cc910f58260255ae5d2943fbbee2b7114f7d86e280c509e321f68`. The environment must already exist on Orchard.

Run the following operator commands in order. Run each remote script separately through one noninteractive login, without a tty. Poll at most once per minute. Stop after a failure or uncertain submission and inspect its existing state.

```bash
cd /scratch/jjyeung/orch_n30/r1_ops/work/drv_p4
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
PY=/scratch/jjyeung/envs/p1cpu/bin/python
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
orch() { timeout 300 bash "$OSSH" 'bash -s' < "$1"; }
```

| Order | Command | Expected output / gate |
|---|---|---|
| 0 | `sha256sum -c DRIVER_SHA256SUMS.txt` | Every entry reports `OK`. Check before running the three installer builders. |
| 1 | `orch u1.sh` | `PASS outer SHA; 37 members; sums.txt exact inventory; files 0600`. Bundle must start absent. |
| 2 | `orch q1.sh` | `PASS native receipt reused; native_unit_regeneration_executed=true; ordered indices checked; projection 5db993b1…`. |
| 3 | `"$PY" -B review_build.py` | `READY rv1.sh; six-review chain pinned; final verdict GO`, or accepted `GO AFTER FIXES` with every LOW fix printed. Current result: `PENDING: missing review_r1p6`. Continue only after READY. |
| 4 | `orch rv1.sh` | `PASS installed six-review chain; final review_r1p6 accepted for packet A; no production GO granted`. |
| 5 | `orch ev1.sh` | `STARTED e0; pid …`. |
| 6 | `orch evp1.sh` | Require `e0 rc=0`, `PASS REMOVE n.json SHA 02315a74…`, and `PASS four evidence records; staging missing=0; durable archive read-back verified; production_go_granted=false`. |
| 7 | `orch dv1.sh` | `STARTED d0; pid …`. Kit must start absent. |
| 8 | `orch dvp1.sh` | Require `d0 rc=0`, the REMOVE SHA check, `status=READY`, A’s exact identity, and `missing_source_members=[]`. |
| 9 | `orch scan1.sh > scan1.out` | Exact packet/archive/run identity, final `MANIFEST` SHA, and `PENDING independent complete content scan…`. Give the scan and final contents to the independent reviewer. |
| 10 | `"$PY" -B cert_build.py ANON_OK.json` | `READY sc1.sh; proof-2 classified scan and ORCH 1758Z exemptions pinned`. Requires the independent inputs below. |
| 11 | `orch sc1.sh` | `PASS independent CLEAN certificate installed for proof 2; classified scan and ORCH 1758Z bound; no production GO`. |
| 12 | `bash L1_mint.sh` | `PASS 20 fresh create-only sessions; mode 0600; URI contents withheld`. Run locally on trinity-1-3 with H1’s authenticated GCS setup. |
| 13 | `"$PY" -B session_build.py` | `READY si1.sh mode 0600; contains secret capabilities; never display`. |
| 14 | `orch si1.sh` | `PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld`. |
| 15 | `timeout 300 bash "$OSSH" 'bash -s -- general' < pr1.sh` | Queue snapshot, sealed-kit checks, CPU sbatch line, and `SUBMITTED job_id=…`. |
| 16 | `orch pm1.sh` | Queue and bounded private log tails for `BUN/job.id`; eventually `<job>.proof.json`. `NOT_YET` and `RUNNING` do not mean PASS. |

`u1.sh` carries the archive as base64 over the single stdin stream. `u3.sh` is the extraction body for inspection, not a separate normal step. The bundle isolates selection outputs, evidence workers `e0`/`d0`, `p0.lock`, `submission.started`, `sbatch.out`, and `job.id` to A. The local mint files are `sess_673bc60f.json`, `mint_673bc60f.started`, and `mint_673bc60f.private.log`. `pr2.sh` shares `pr1.sh`’s bytes and attempt guard. Both wait scripts refuse automatic submission. `pq.sh` and `qcheck.sh` display only the queue. `go_submit_6f8ed106.sh` is an inert refusal script.

The final independent review is `events/review_r1p6/REVIEW_VERDICT_R1P6.md`, expected November 17 at about 1:20 p.m. PT. Its antecedents are `review_r1p`, `review_r1p2`, `review_r1p3`, `review_r1p4`, and `review_r1p5`, with correspondingly named verdict files. All five antecedents currently parse successfully.

The final gate requires exactly one explicit `Packet A` section or A table row. Within that section, A must have exactly one GO or GO AFTER FIXES verdict and its full archive SHA or config identity. A conditional verdict must list only explicit LOW fixes without blocking conditions. An A section may place the verdict on its heading or a separate `Verdict: GO` line. B’s section, hash, verdict, and fixes cannot satisfy A’s gate. Missing, stale, negative, ambiguous, unsupported, or above-LOW results fail closed. The installer preserves all six texts and hashes; the evidence worker independently applies the same policy. No driver rewrites a reviewer’s text.

`scan1.sh` inventories new and inherited names, archive members, staging locators including `n.json`, session/export destinations, both partition argv forms, and selected shell command lines. It does not certify content. The independent reviewer must inspect the final contents and `proof_decoded.py` and produce a classified scan record plus a certificate for A.

| Certificate input | Required binding |
|---|---|
| `ANON_OK.json` | `status=CLEAN`, integer `hits=0`, reviewer, full `config_identity`, full `operator_archive_sha256`, final `manifest_sha256`, and `scan_sha256` for `scan1.out`. |
| Provenance | `scan_record` identifies the classified JSON. `exemption_record` must be `events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md`; its fixed SHA is verified. |
| Classified JSON | Reviewer; full A config identity or archive SHA; `inputs.scan_sha256`; `inputs.manifest_sha256_in_scan`; and a `hits` list classified as `inherited-accepted`, `exempt-content`, or `new-visible`. |
| Exemptions | Every new visible hit has a unique ID. `private_tree_contents_accepted` can reference only `log line: KH/o/<job>.proof.log` or its plural form. `inherited_token_accepted` requires `inherited_token=true` and the inherited account-home surface `/home/jjyeung` or `argv token: /home/jjyeung`. Unknown IDs and other visible hits fail. |
| External files | Exact path/SHA entries for all 37 sealed bundle members, including both REMOVE copies. `CERTIFICATE_REQUIREMENTS.json` supplies these pins and grants no certification. |

Relative `scan_record` paths resolve under the event root; paths beginning `events/` resolve under orch_n30. For a local reviewer record, use `"$PY" -B cert_build.py ANON_OK.json --scan-record CLASSIFIED.json`. The certificate must reside in this work directory. The installer verifies the final kit manifest, its listed bytes, the archive, and all external pins before creating a private certificate. It refuses an existing certificate. It retains both provenance hashes.

`L1_mint.sh` uses H1’s `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py`, namespace `8865619b`, run `673bc60f`, and five slots `m100 m200 mstop mstopB mstopC`, four parts each. It creates its attempt marker exclusively and keeps helper output private. Do not display session capabilities or `si1.sh`.

`pr1.sh` defaults to `general`; it also binds the packet’s `advanced` argument, but general is the operator path because advanced is closed to this operator. One unfiltered queue snapshot must contain no `a15_cot_ap*` or `jjy_*` job on the selected partition, in any state, and no A job name on any partition. Queue errors stop submission. The same partition reaches `p.py` and sbatch. Coordinate unrelated operators externally.

A bundle-local flock and exclusive attempt marker prevent repeat submission. If the connection times out around sbatch, inspect the queue, marker, and `BUN/sbatch.out`; a missing `job.id` does not prove failure. The CPU allocation requests 48 CPUs, 800G memory, four hours, and zero GPUs. After completion, require PASS for `disk_plan`, `routing_selection`, `empty_root`, `temporary_paths`, `runtime_binaries`, `directory_modes`, `loader_audit`, and `required_families`. Check identity, manifest, requested/actual partition, node, zero GPU allocation, and five traces per populated family. Production submission requires separate authorization.

Local validation evidence lives in `*_p4.txt` and `storage_results_p4.json`. The READY fixture is `tests_p4_6ogiqq03/derived_ready`. It uses two labeled sentinel members to complete incomplete H1 fixture inputs, so it tests derivation and evidence control flow without attesting production data or RGB. `fixture_p4` contains A’s exact archive members. Other retained fixtures and logs are not evidence for this handoff.

Validation covers native regeneration, READY derivation, REMOVE staging and corruption refusals, four evidence identity refusals, altered-deriver refusal, 108 sealed switch cases, A/B review isolation, review/certificate/session builders, both partition bindings, duplicate-submit guards, scan inventory, and shell/Python syntax. Tests use simulated independent records, fake capabilities, and local Slurm stubs. New files remain below 300 MB; immutable local inputs use hardlinks and negative evidence fixtures contain metadata only. `test_local.py` refuses a bulk rerun while `tests_p4_*` outputs exist.

`rv1.sh`, `sc1.sh`, and `si1.sh` remain inert placeholders at handoff. Check `DRIVER_SHA256SUMS.txt` before builders replace them with validated independent inputs. Generated installers intentionally differ from that handoff manifest. No production review approval, certificate, session, or authorization is created by the build.
