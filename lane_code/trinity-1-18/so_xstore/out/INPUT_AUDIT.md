# Native preparation inputs and the export dependency

**N's complete native preparation is CPU work, but it cannot finish before the export selected for N's handover exists.** If N selects step 600, that export and its authenticated handover closure must exist first. This follows from the unconditional parent metadata reads and N's handover validation, not from a GPU requirement (`student_pilot/s1_admission.py:182`, `student_pilot/mdg_parent.py:40`, `student_pilot/r1_handover.py:38`, `student_pilot/r1_components.py:25`).

All source references below are relative to build 21b's `work/tree_r1`, supplied at `/scratch/jjyeung/orch_n30/so_xstore/in/tree21b`. Its source seal is `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`. This is an audit of code and supplied evidence, not a measured production read trace or a complete reusable key.

## What mode p does

The wrapper hides CUDA for mode p (`launch_s1/b/r.sh:65`). Its worker calls `s1_admission.admit(..., threads=16, prepare_only=True)` (`launch_s1/b/w.py:34`). Admission verifies configuration and source, rebuilds pointing and VQA, materializes routing, composes N routing when configured, binds the handover, runs native preparation, verifies its receipt, and audits retained RGB (`student_pilot/s1_admission.py:156`, `:182`, `:203`, `:210`, `:218`, `:221`, `:246`, `:250`). It returns before the CPU first-batch check (`student_pilot/s1_admission.py:287`).

The existing CLI already accepts `--prepare-only`, CPU/memory bounds and a wall limit (`student_pilot/s1_admission.py:344`). That entry does not implement portable storage or adoption. Its journals bind the current configuration, source, frame roots and CPU settings (`student_pilot/s1_admission.py:171`).

## Checkpoint, export and previous-job reads

| Input | Native read and consequence |
|---|---|
| Pinned parent artifact | `mdg_parent.bind` loads `cfg.init_artifact.artifact` even without MDG (`student_pilot/mdg_parent.py:28`, `:40`, `:44`). |
| Parent full-weight manifest and index | Both are read and hash checked before the no-MDG return (`student_pilot/mdg_parent.py:48`, `:54`, `:66`). The no-MDG proof explicitly says parent weight payloads were not verified (`:73`); that is not independence from parent metadata. |
| Parent embedding shard, MDG branch | With MDG, the native reader hashes the embedding shard and opens slices explicitly on CPU; tokenizer, vocabulary, shipped confusers and MDG initialization are also read (`student_pilot/mdg_parent.py:77`, `:80`, `:86`, `:97`, `:100`). |
| N's persisted handover | N's component deferral checks the pinned handover, donor configuration and artifact (`student_pilot/r1_components.py:25`, `:28`, `:29`). Native preparation calls those checks (`student_pilot/r2_contract.py:71`) and carries inherited component evidence (`student_pilot/carrier_c1_run.py:637`, `student_pilot/r1_components.py:103`). |
| Donor configuration, binding, preparation and checkpoint metadata | The persisted verifier requires these run keys for a training handover, reads their JSON and authenticates their pins (`student_pilot/r1_persisted.py:62`, `:73`, `:85`). The proof-only export path is restricted to mode q (`:21`). This is a checkpoint **metadata** dependency; it is not a claim that preparation loads optimizer tensors. |
| Persisted RNG files and available export payloads | The same verifier hashes checkpoint files whose names begin with `rng` (`student_pilot/r1_persisted.py:116`). It checks other checkpoint payloads for existence without reading them (`:122`). It also hashes every available heads/full-weight/export member even when `weights=False` (`:147`). Thus N's staged handover can read full export weight bytes despite the no-MDG branch's narrower parent-grounding reads. |
| Handover map and continuation identity | `bind_target` reads the selected artifact, authenticates the donor, compares configurations and derives the target progress map (`student_pilot/r1_handover.py:30`). Admission calls it when `r1_training.handover_receipt` is present (`student_pilot/s1_admission.py:218`). |
| Extra next-leg export metadata | The optional `r2` branch reads `r2.export_metadata`, checks init lineage and the code/mixture identity (`student_pilot/r2_contract.py:86`). |
| Wrapper init mirror | Before p, `tk_stage_init` copies and verifies the parent export, including heads, index and every weight shard (`launch_s1/b/c.sh:217`, `:245`, `:254`). The native reader may resolve it through `C1_INIT_LOCAL` (`student_pilot/carrier_c1_run.py:904`). |
| Wrapper resume checkpoint | `r.sh` runs the launch guard before staging (`launch_s1/b/r.sh:40`); `job.sh` also runs the guard/chooser (`launch_s1/job.sh:16`). These are outside native row preparation. A dedicated CPU entry need not run this GPU launch wrapper. |

The supplied measured jobs used the existing parent prefix `1d6eeb28f51688c4`, not an export that had yet to be produced (`so_in/.../r1_ops6/work/mon/last.txt:226`; `so_in/.../swarm_opt/work/o/look1.out:343`). That prefix matches the explicit parent constant (`student_pilot/r1_training.py:6`). Their successful preparation does not prove that a new N handover can prepare before its selected export exists.

## Configuration read surface

There is no small field allowlist in the current native code. `carrier_c1_run.identity` iterates the entire configuration, excluding only `preparation`, `admission`, `authorization`, and `milestone_gate`, with additional nested normalization (`student_pilot/carrier_c1_run.py:38`). Preparation writes that identity into its receipt (`:625`). In particular, it consumes `output`, `preparation_output`, and any present `run_key`. N's `target_identity` also iterates the configuration and retains those fields (`student_pilot/r1_training.py:102`). **The requested excluded-field rule requires a native refactor.** A wrapper cannot simply remove them from a key while these consumers remain unchanged.

The direct readers select the following additional branches. The source inventory in `evidence/config_reads.json` lists literal configuration access sites with file/line references; it is a static inventory, not a runtime read set.

| Field family | Native reader |
|---|---|
| schema, recipe, world/reference world, training mode, streams, MDG presence, mix, steps, milestones, weights, scheduled sampling, seed/recipe settings | `student_pilot/s1_admission.py:157`; `student_pilot/carrier_c1_run.py:69`; `student_pilot/carrier_c1_sweep.py:56`. |
| init/base identity, placement, parallelism, frame layout/count/markers/pair gap, all-frames, geometry, depth enable/source/init, pixel limits, trace/contract version, heading threshold | `student_pilot/carrier_c1_run.py:69`, `:502`, `:519`, `:629`, `:633`; `student_pilot/s1_routing.py:196`. |
| ground-target filter, REMOVE lists, dev/benchmark/pose/report exclusions, held-out QIDs/sources, scene coverage/division | `student_pilot/s1_admission.py:158`, `:185`; `student_pilot/carrier_c1_run.py:475`, `:491`, `:621`. |
| routing selection/catalog/frame map/frame plan/FPS authority/candidate manifest; route table/policy; tool-mode flag; vocabulary/opener settings | `student_pilot/s1_routing.py:202`; `student_pilot/carrier_c1_run.py:367`, `:633`; `student_pilot/r2_openers.py:24`. |
| R1 card, registry/component records, row sources/membership/batches, handover/persisted files/proof mode and sampler identity | `student_pilot/r1_training.py:42`, `:71`, `:102`; `student_pilot/r1_routing.py:161`; `student_pilot/r1_components.py:10`; `student_pilot/r2_contract.py:65`. |
| optional validation rows/slice, B7 inputs, H1 controls, R2 identity/membership/scene exclusions, extent receipt | `student_pilot/carrier_c1_run.py:422`, `:633`; `student_pilot/r2_contract.py:65`. |
| code seal, output/preparation locations and remaining configuration values | `student_pilot/carrier_c1_run.py:38`, `:185`, `:664`; `student_pilot/r1_training.py:102`. |

## File and code read surface

Every path below denotes the whole pinned dependency family, including children identified inside a receipt. Concrete production paths and a complete observed file list cannot be recovered from the two step logs. The supplied build report lists absent payload dependencies (`out/BUILD21_REPORT.md:63` in the input package); its receipt-reader and CPU-proof results do not constitute an execution trace of this lane's proposed store.

| File family | Reader |
|---|---|
| Configuration JSON and source seal | `student_pilot/s1_admission.py:156`; `student_pilot/carrier_c1_run.py:186`. |
| Sealed source tree and source archive; imported native modules and installed runtime | `student_pilot/carrier_c1_run.py:188`; `student_pilot/p3_provenance.py:65`; `student_pilot/source_seal.py:80`. Authentication checks the whole sealed tree plus archive; imported library versions are a separate runtime dependency. |
| All stream receipts, SQLite rows/targets, source memberships, divisions and parent division ancestry | `student_pilot/carrier_c1_run.py:486`, `:351`, `:540`; `student_pilot/carrier_c1_data.py:552`; `student_pilot/r1_routing.py:57`. |
| Composite pose sources, plans, teacher/model metadata and selection indices | `student_pilot/carrier_c1_run.py:497`; `student_pilot/c1_pose_mix.py:131`. |
| Pointing masks/raster keys and retained RGB | `student_pilot/carrier_c1_data.py:513`, `:578`; `student_pilot/s1_admission.py:42`, `:78`. The frame audit checks existence for every retained frame but hashes a fixed sample, not every frame byte. A portable store would need additional complete object verification. |
| REMOVE lists; exclusions; coverage reference/source map; optional validation inputs | `student_pilot/row_removals.py:31`; `student_pilot/s1_exclusions.py:12`, `:29`; `student_pilot/carrier_c1_run.py:422`, `:491`, `:621`. |
| Routing selection and relocation catalog, eligible gzip/packed sources and indices, frame map/plan/FPS authority, candidate manifest, legacy SQLite store | `student_pilot/s1_routing.py:72`, `:81`, `:87`, `:220`, `:223`, `:228`, `:314`, `:372`; `student_pilot/s1_pool.py:225`. |
| Base model manifest and non-weight architecture/tokenizer/processor assets | `student_pilot/mdg_parent.py:11`, `:34`, `:39`; `student_pilot/s1_routing.py:216`, `:240`. |
| Parent export, handover, component evidence and optional MDG assets | The preceding parent/export table; `student_pilot/carrier_c1_run.py:637`, `:641`. |
| Existing native request/phase/result/prepared receipts and frame inventory when resuming | `student_pilot/s1_admission.py:175`, `:241`, `:246`, `:257`; `student_pilot/first_batch_progress.py:25`. Native refusal and resume behavior must survive any store miss. |
| Wrapper staging archives, inventories/manifests, model, runtime record and init mirror | `launch_s1/b/c.sh:270`, `:298`, `:310`, `:315`, `:322`, `:325`, `:326`. These are staging inputs, outside the native function itself. |

## Environment and nondeterministic state

Build 21b resolves five environment names through `job_env.key`: `Q_E1` through `Q_E5` override the legacy Orchard, Slurm-site, model-root, frame-root-map and student-alias names whenever the corresponding alias is present (`student_pilot/job_env.py:3`). A complete native key must record the selected name, its presence and its value. Recording only the legacy name would miss a consumed input.

The launch fixes `TRAINER`, `R1_TRAINER`, `R1_MOUNT`, `R1_STUDENT_HEX`, model/frame roots, `C1_INIT_LOCAL`, Python search paths, runtime record, cache/offline settings and CPU-library thread counts (`launch_s1/b/c.sh:361`). Native relocation reads `STUDENT_ORCHARD`, `STUDENT_FRAME_ROOT_MAP`, `R1_MOUNT` and `STUDENT_MODEL_ROOT` (`student_pilot/orchard_paths.py:7`, `:11`, `:23`, `:58`). Student aliases read `R1_STUDENT_HEX` (`student_pilot/students.py:55`); rehearsal reads `S1_CPU_REHEARSAL` via `launch_s1/b/q0.py:6` and `:12`. CUDA visibility is a native precondition (`student_pilot/s1_admission.py:135`). The import graph also contains optional environment-dependent branches; `evidence/read_sites.txt` retains their direct sites without claiming all execute for N.

UUIDs, resolved absolute paths, timing and resource counters enter current receipts and journals (`student_pilot/first_batch_progress.py:14`, `:40`, `:44`; `student_pilot/s1_admission.py:82`, `:86`, `:171`, `:281`). SQLite stores the resolved physical frame path (`student_pilot/s1_admission.py:33`, `:63`). These are native format issues; post-hoc string replacement is not a portability proof.

## CPU and resources

N also authenticates `r1_training.wording_exclusion`, the row-source catalog and the two coverage sources during validation (`student_pilot/r1_training.py:68`, `student_pilot/r1_coverage.py:38`). The K1 union check reads and compares its base, extra and union REMOVE lists (`student_pilot/r1_coverage.py:83`). Those inputs belong in the dependency closure when their branches are active.

| Quantity | Evidence and limit |
|---|---|
| GPU requirement | Native admission requires empty CUDA visibility and sets CPU thread limits (`student_pilot/s1_admission.py:135`, `:142`). The MDG tensor slice explicitly uses CPU (`student_pilot/mdg_parent.py:86`). No preparation path shown here requires a GPU allocation. This is not a claim that imports or library initialization never call any `torch.cuda` Python helper. |
| CUDA helper distinction | Torch 2.11's `manual_seed` dispatches to CUDA seed helpers (`/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/random.py:45`). An absolute zero-CUDA-function claim requires a runtime trace of the actual branch; it is not established by hiding devices. |
| CPU cores | The measured wrapper requests 16 intra-op threads in native admission (`launch_s1/b/w.py:45`) and sets I/O threads to 16 (`launch_s1/b/r.sh:65`). This is a configured limit, not measured peak utilization. The local candidate tests use at most eight threads. |
| RAM | Admission defaults to a 256 GiB address-space ceiling, not a 256 GiB RSS requirement (`student_pilot/s1_admission.py:133`, `:139`). Phase journals record `peak_rss_kib` (`student_pilot/first_batch_progress.py:44`), but those production records are absent from the supplied logs. Peak production RAM is **unknown**. The 800 GB launch request (`launch_s1/build.py:225`) includes training and is not a preparation measurement. |
| Disk | Full native input/output peak is **unknown**. Logs show staged database sizes but not the complete preparation/frame footprint (`so_in/.../swarm_opt/work/o/look1.out:123`). Measure source bytes, prepared bytes, RGB bytes, temporary peaks and store/adopt copies independently. No full dataset was staged here. |
| Walltime | Measured mode-p envelopes are 8,434 s = 140.57 min (`so_in/.../r1_ops6/work/mon/last.txt:229`–`:230`) and 8,716 s = 145.27 min (`so_in/.../swarm_opt/work/o/look1.out:346`–`:347`). Neither measures eight-core CPU-only allocation performance. |
| Reservation guidance | An initial 16-core/256-GiB/6-hour production CPU reservation is an **unvalidated sizing estimate**, based on the native defaults and measured elapsed time with allowance for staging. It must be adjusted from real resource telemetry. It is not an instruction to run that load in this lane. |

Torch's installed docs require setting intra-op threads before eager/JIT/autograd work and inter-op threads before inter-op work (`torch/_torch_docs.py:9815`, `:9828` under the same environment). Official versioned references: [intra-op threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html), [inter-op threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_interop_threads.html).

**Conclusion: N can prepare on CPU alongside job 172660, but full native preparation for an N handover that selects step 600 must wait for that export and its authenticated metadata.**
