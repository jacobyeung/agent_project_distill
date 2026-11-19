Vehicle N uses MINIMAL. Production launch is BLOCKED; normal kits have GO=false. The GO template has no review and is not uploaded.
Init is P's step-400 export 5083243c from run 6ed2c7aa through its authenticated export-only receipt.
No checkpoint or state after P's step 400 initializes N. No handover fill remains.
Tree: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`.
Kit n: `32569efe9de922415cad1a0302763601c28ba435f82505ccce2d16e260a1a31d`; kit q: `3d14429690aae6ebd1dc569010802487d37944368a4e6b78a9e016b69717d6a8`.
GO variant: `8d96ece0054dd1b731929e90d77f5d83b9a39be847bacbde4c51c680bba66379`. Seals: work/build24h/INVARIANTS.json and out/UPLOADS_24H_GO.json.
N requests advanced, four GPUs/four ranks, one launcher, 48 CPUs, 800G and 24:00:00.
SBATCH signals the batch shell with TERM 600 seconds before the limit. The allocation runs its own mode-q canary.
TK_JOB_START records allocation-start epoch seconds and reaches bwrap, torch.distributed.run and train().
Shell CPU-stage OMP/MKL/OpenBLAS limits are 48. Native canary admission uses 8 Torch threads; training uses 8 per rank.
Checkpoint cadence is step 1, every 7,200 seconds, and at stop. Timed checkpoints remain node-local.
Exports occur at local steps 100, 200, 400, 600, 800, 1000, and at stop.
After kit verification, the batch shell copies log tails, metrics, attempt/run metadata, marker hashes and .steps every 600 seconds and at exit.
Each small copy is at most 50 MB, including at most 40 MB of log tails, under x_22c714e1/o/<jobid>/live/ on /project.
A separate worker checks export artifact markers every 10 seconds and sends immutable export tars through four GCS parts when sessions exist. A broken export records its status without blocking later exports.
SESSION_NAMES_24F.json fixes unchanged milestone names plus three once-claimed stop generations.
The copier reads `/project/community/jjyeung/okh7/x_22c714e1/n_s/sess.json` outside the kit, ignoring TK_KIT_HOME; --sessions PATH may select another filename only inside n_root/n_s. Live, claims, n_ck and sessions paths inside either kit copy or outside their expected subtrees refuse.
The sessions directory must belong to the job user with mode 0700; sess.json must be a regular non-symlink file with mode 0600 and a JSON object mapping part names to URLs.
An unusable sessions file records `export not uploaded: sessions unusable (<reason>)`, uploads nothing, and keeps the tar node-local. The private node-local copy has mode 0600.
At exit, the latest completed stop checkpoint goes to x_22c714e1/n_ck/<jobid>/ if its size plus 50 GiB is free; otherwise GCS is attempted or it remains local with a marker.
Small-file GCS mirroring awaits the orchestrator's credential ruling. The kit contains no credential or session URL.
Accepted loss: if the node dies between exports, the leg restarts from the last export with a fresh optimizer.
Declaration: r1_training.routing_slices=deferred_first_boundary; init_policy=step400_export_weights_fresh_v1.
N starts a fresh optimizer, counter and schedule at zero. Its first 200 steps are local steps 1–200 from P's step-400 weights.
N keeps P's regenerated S1 routing base (receipt ca0616db, database 4e8e6c04); all six deferred routing cells contain zero new rows.
Distance calls, unit conversions and camera wording receive no targeted new routing examples; routing-slice gates start when those slices enter.
VQA adds 7,971 direction half-turn twins and removes 109 named-route matches (107 newly removed), leaving 55,808 direction and 8,562 route-planning rows (work/build24/CENSUS.json).
Held-out wording exclusions, K1 removals and room rules remain active. P's opener rows stay routing_opener_init=keep; the step-544 lineage remains pinned.
The two absent head slots retain NOT_PRESENT; seven other slots stay DEFERRED and block official reads. The pose record remains bound.
Relative-count rows, answer-prior weights, frame-host alias and step-time patches wait for the first boundary.
N has no tower-scale freeze in the point-depth head; H3 can fire again at the first look for the same cause.
TERM/USR1 signals only torchrun workers with an installed USR1 handler, waits up to 420 seconds, then runs final publication; the trainer exit code is preserved.
The 585-second cleanup budget reserves 15 seconds of the 600-second warning and assumes no KillWait grace. A wait timeout copies small evidence only; large-copy completion is not guaranteed.
h.py requires a real host result at Q_NS/p/host.json and a sha256-pinned independent review of the final config; each invalid receipt refuses before t.py.
The sealed mode-q path produces no frame_host result. The hidden-view input identity is not a verified final training identity; see out/PRODUCTION_BLOCKERS.md.
n_review1 must supply the review. out/arm_go.py stages it and writes UPLOADS_ARMED only when called; no armed production kit or review is supplied.
