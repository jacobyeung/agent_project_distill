These drivers prepare vehicle P’s proof-2 CPU packet. The local fixture regenerated all 747 bound unit rows and reached READY. Orchard execution, the final independent review, content certification, fresh export sessions, and the CPU proof remain operator steps. Production GO remains false.

Work only in `/scratch/jjyeung/orch_n30/r1_ops/work/drv_p2`. The build made no SSH, Orchard, Git, GPU, or deletion call. All writes stayed here. The operator commands below describe future execution.

| Binding | Value |
|---|---|
| Bundle | `/project/community/jjyeung/okh7/i_6f8ed106` |
| Derived kit | `/project/community/jjyeung/okh7/x_6f8ed106` |
| H1 source | `/project/community/jjyeung/okh7/x_3fdda0fb` |
| Source manifest SHA256 | `661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3` |
| Operator archive | `p_6f8ed106.tar`, 13,967,360 bytes, 35 regular-file members |
| Archive SHA256 | `def1e1f2b1153328b024209e69fcbb71f2dd556b7376eacb836d40bb66d9845f` |
| Config identity | `2c67f1f25114ab1324cee10b796e86afc79d01999ad3881860ab35710e7fee5d` |
| Tree SHA256 | `b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b` |
| Run / job | `78d0a06c` / `a15_cot_ap78d0a06c` |
| V7 store | `/project/community/jjyeung/okh7/s_22b44165/d.db` |
| Unit source | `U_Faithful`: 747 rows, including 683 eligible feet rows |
| Selection SHA256 | `5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af` |

`packet_config.py` verifies the frozen `snap_2c67f1f2/out` packet, archive, every inner member, and the separate `units/{u.json,u.gz,m.json,i.json}` pins. `PACKET_PINS.json` records these bindings. `build_drivers.py` renders the shell scripts, export destinations, and decoded proof source from those verified bytes. `fixture_p2` is the packet fixture; `fixture_h` supplies incomplete H1 fixture inputs. Other copied fixtures and old test logs are not proof-2 evidence.

**CPU environment and selection.** `q1.sh` invokes H1’s authenticated CPU interpreter `/project/community/jjyeung/latency/envs/fit/bin/python3`, identified in `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/q.sh`. It requires Python 3.10 or newer and disables CUDA, bytecode, online model fetches, and multithreaded BLAS. It verifies and extracts the bound trainer archive into fresh `BUN/qt`, then uses that code for native unit regeneration. The environment must already exist on Orchard; the driver installs nothing.

H1’s retained raw receipt is `i_1be16f28/q_6c18a2bf/o/native/receipt.json`, SHA256 `2e25a01d943cc910f58260255ae5d2943fbbee2b7114f7d86e280c509e321f68`. The driver checks that receipt, its EQUAL report, parent selection, and ordered indices. It invokes `q.py` with `--unit-binding BUN/u.json --config BUN/config.json`, plus the parent, indices, implementation, and code record. It requires both native-regeneration flags and the exact final selection hash. `ev1.sh` verifies staging of `u.gz`, `m.json`, and `i.json`; `dv1.sh` requires the archive’s exact deriver SHA before creating the fresh kit.

**Operator order.** Run each remote script separately with one noninteractive login and no tty. Poll no more than once per minute. Stop on failure or an uncertain submission; inspect its existing state before proceeding.

```bash
cd /scratch/jjyeung/orch_n30/r1_ops/work/drv_p2
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
PY=/scratch/jjyeung/envs/p1cpu/bin/python
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
orch() { timeout 300 bash "$OSSH" 'bash -s' < "$1"; }
```

| Order | Command | Expected output / gate |
|---|---|---|
| 0 | `sha256sum -c DRIVER_SHA256SUMS.txt` | All entries report `OK`. Run before generating the review, certificate, or session installers. |
| 1 | `orch u1.sh` | `PASS outer SHA; 35 members; sums.txt exact inventory; files 0600`. Bundle must start absent. |
| 2 | `orch q1.sh` | `PASS native receipt reused; native_unit_regeneration_executed=true; ordered indices checked; projection 5db993b1…`. |
| 3 | `"$PY" -B review_build.py` | `READY rv1.sh; four-review chain pinned; final verdict GO`, or accepted `GO AFTER FIXES` with every LOW fix printed. Currently: `PENDING: missing review_r1p4`; do not run the next step until READY. |
| 4 | `orch rv1.sh` | `PASS installed four-review chain; final review_r1p4 accepted for exact packet; no production GO granted`. |
| 5 | `orch ev1.sh` | `STARTED e0; pid …`. Reads and verifies staging inputs in a background CPU worker. |
| 6 | `orch evp1.sh` | Wait for `e0 rc=0` and `PASS four evidence records; staging missing=0; durable archive read-back verified; production_go_granted=false`. |
| 7 | `orch dv1.sh` | `STARTED d0; pid …`. Kit must start absent. |
| 8 | `orch dvp1.sh` | Require `d0 rc=0`, `status=READY`, the exact config/source bindings, and `missing_source_members=[]`. |
| 9 | `orch scan1.sh > scan1.out` | The saved inventory ends with the proof-2 packet identity, final `MANIFEST` SHA, and `PENDING independent complete content scan…`. Give it and the final bytes to the independent reviewer. |
| 10 | `"$PY" -B cert_build.py ANON_OK.json` | `READY sc1.sh; proof-2 classified scan and ORCH 1758Z exemptions pinned`. Requires the independent inputs described below. |
| 11 | `orch sc1.sh` | `PASS independent CLEAN certificate installed for proof 2; classified scan and ORCH 1758Z bound; no production GO`. |
| 12 | `bash L1_mint.sh` | `PASS 20 fresh create-only sessions; mode 0600; URI contents withheld`. Run locally on trinity-1-3 with the authenticated H1 GCS setup. |
| 13 | `"$PY" -B session_build.py` | `READY si1.sh mode 0600; contains secret capabilities; never display`. |
| 14 | `orch si1.sh` | `PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld`. |
| 15 | `timeout 300 bash "$OSSH" 'bash -s -- general' < pr1.sh` | Prints the queue, verifies the kit, binds `p.py --partition general`, prints the CPU sbatch line, and reports `SUBMITTED job_id=…`. |
| 16 | `orch pm1.sh` | Prints the queue and bounded private log tails for `BUN/job.id`; reports `<job>.proof.json` when available. `NOT_YET` and `RUNNING` do not mean PASS. |

`u1.sh` frames its archive as base64 on the single stdin stream; the script is about 18.9 MB. `u3.sh` is the extraction body for inspection and is not a separate normal step. Every runtime bundle, kit, selection directory, evidence worker, and attempt marker belongs to proof 2. `pr2.sh` has the same bytes and attempt guard as `pr1.sh`; it is not a retry path. `wait_general.sh` and `wait_general2.sh` refuse automatic submission. `pq.sh` and `qcheck.sh` only display the user’s queue.

**Independent review.** The final file is `events/review_r1p4/REVIEW_VERDICT_R1P4.md`, expected around 11:30 a.m. PT on November 17. Its antecedents are `review_r1p`, `review_r1p2`, and `review_r1p3`, with the correspondingly named verdict files. The builder accepts final GO, or GO AFTER FIXES with only explicit LOW fixes and no blocking conditions. The final verdict must name the full archive SHA or config identity. Missing, stale, negative, ambiguous, or above-LOW conditional verdicts fail closed. The installer preserves all four texts and hashes; the evidence worker independently revalidates them.

**Content certificate inputs.** `scan1.sh` inventories the new and inherited names, code-archive members, staging locators, planned sessions, export destinations, both partition argv forms, and selected shell command lines. It does not certify content. The independent reviewer must inspect the final contents and decoded proof program and produce a classified scan record plus `ANON_OK.json` for this packet.

The certificate uses the proof-1 precedent’s fields with explicit proof-2 identity bindings:

| Input | Required values |
|---|---|
| `ANON_OK.json` | `status=CLEAN`, `hits=0`, reviewer, full `config_identity`, full `operator_archive_sha256`, final `manifest_sha256`, and `scan_sha256` for `scan1.out`. |
| Provenance | `scan_record` identifies the reviewer’s classified JSON; `exemption_record` must be `events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md`. The builder verifies the exact exemption SHA and retains both provenance hashes. |
| Classified JSON | Reviewer; full `config_identity` or `operator_archive_sha256`; `inputs.scan_sha256`; `inputs.manifest_sha256_in_scan`; and a `hits` list whose classes are `inherited-accepted`, `exempt-content`, or `new-visible`. |
| Exemptions | Every `new-visible` hit has a unique ID. `private_tree_contents_accepted` may reference only a reviewer-classified `log line: KH/o/<job>.proof.log` or `log lines: KH/o/<job>.proof.log` surface. `inherited_token_accepted` requires the reviewer’s `inherited_token=true` and only the inherited account-home token. No other visible hit is accepted. |
| `external` | Exact path/SHA entries for all 35 sealed bundle members. `CERTIFICATE_REQUIREMENTS.json` supplies these pins; its `REVIEW_REQUIRED` status grants no certification. |

By default, the builder resolves relative `scan_record` paths under the orch_n30 event root and reads local `scan1.out`. For a reviewer record delivered here, use `"$PY" -B cert_build.py ANON_OK.json --scan-record CLASSIFIED.json`. The certificate must live in this directory. An altered scan, foreign packet, missing external pin, unclassified hit, or unsupported exemption fails. The installer verifies the final kit inventory and external bytes before writing a private certificate, and refuses an existing CLEAN certificate. The proof-1 certificate is not an input.

**Sessions and submission.** `L1_mint.sh` uses `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py`, namespace `8865619b`, run `78d0a06c`, and five slots `m100 m200 mstop mstopB mstopC`, four parts each. It atomically creates `mint_78d0a06c.started`, writes `sess_78d0a06c.json`, and keeps helper output in `mint_78d0a06c.private.log`. Do not display those capabilities or `si1.sh`.

`pr1.sh [PARTITION]` defaults to `general` and accepts the packet’s `general` or `advanced` arguments. Use general because advanced is closed to this operator. The guard checks one unfiltered queue snapshot and refuses any `a15_cot_ap*` or `jjy_*` job on the selected partition, in any state. It also refuses this run’s job name on any partition. Queue failures stop submission. The same partition reaches both `p.py` and sbatch.

Submission uses a bundle-local flock and exclusive `submission.started` marker. A second invocation cannot submit another job. If the connection times out around sbatch, inspect the queue, marker, and `BUN/sbatch.out`; absence of `job.id` does not prove submission failed. The snapshot cannot serialize unrelated operators, so coordinate the partition externally.

The CPU allocation requests 48 CPUs, 800G memory, four hours, and no GPUs. After completion, require PASS for `disk_plan`, `routing_selection`, `empty_root`, `temporary_paths`, `runtime_binaries`, `directory_modes`, `loader_audit`, and `required_families`. Verify the exact identity, manifest, requested/actual partition, node, zero GPU allocation, loader audit, and five traces per populated family. No driver launches the production GPU wrapper or grants production GO.

**Local validation and storage.** `test_results_p2.txt` records native regeneration of all 747 rows, unit staging pins, a production-form fixture at READY, all four evidence-identity refusals, and rejection of an altered deriver. Two absent H1 archive members use labeled sentinel bytes; this tests derivation and evidence control flow, not production data authenticity or RGB admission.

`builder_results_p2.txt`, `guard_results_p2.txt`, `evidence_results_p2.txt`, `certificate_results_p2.txt`, `contract_results_p2.txt`, and `syntax_results_p2.txt` record the smaller review, session, certificate, partition, binder, and syntax checks. All 19 top-level shell scripts pass `bash -n`. Tests use fake capabilities, simulated independent records, and local Slurm stubs; none mint sessions or submit jobs.

The initial full-fixture test exceeded the 300 MB new-scratch limit: its test tree occupies about 484 MiB. `REMOVAL_CANDIDATES.md` queues a user-only command to free about 403 MiB of redundant copies while retaining READY evidence. No deletion ran. Future negative evidence checks use small metadata copies; `test_local.py` checks its estimated budget and refuses a bulk rerun while any `tests_p2_*` directory exists. Do not rerun the bulk fixture without user cleanup. The small tests and final checks did not repeat full-kit derivation.
