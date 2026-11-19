Vehicle N uses MINIMAL. Normal kits have GO=false; the GO template is not uploaded. Production remains blocked by the missing host-receipt producer (PRODUCTION_BLOCKERS.md).
Init is P's step-400 export 5083243c from run 6ed2c7aa through its authenticated export-only receipt. Nothing after P's step 400 initializes N.
Tree: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`.
Kit n: `3e3538abc3611404d3692da1954c19d35485d165921bcabf4039bafe3b9fc9f1`; kit q: `3d14429690aae6ebd1dc569010802487d37944368a4e6b78a9e016b69717d6a8`.
GO template: `8d141d15e6a9c14983ed38a426e662200d76b5b3104121266b05b9529b6eb8c2`. Seals and deltas: work/build24i/INVARIANTS.json and UPLOADS_24I_GO.json.
N requests advanced, four GPUs/four ranks, one launcher, 48 CPUs, 800G and 24:00:00. Slurm signals the batch shell with TERM 600 seconds before the limit.
TK_JOB_START records allocation-start epoch seconds and reaches bwrap, torchrun and train(). Shell preparation limits are 48; native admission and review evidence use 8 threads.
The job runs its own mode-q canary and room audit. h.py requires a genuine matching host result at Q_NS/p/host.json, then pins it and writes Q_NS/v.json.
Before training, both GO variants publish v.json (at most 50 MB), identity.txt, and evidence to <n_root>/o/<jobid>/live/. The identity comes from the sealed tree in the job view.
Evidence names are e0.json (pose), e1.json (VQA), e2.json (routing), e3.json (pointing), e4.json (d.py rooms.json bytes), and e5.json (its sha256 and size). Their combined cap is under 2 MB.
Each stream file reports every opened database hash, admitted count, question-type counts, full-store empty-reasoning and recorded trace-form counts, and 40 deterministic rows with frames, indices and timestamps omitted.
The native readers are carrier_c1_run.Rows.row and c1_pose_mix.PoseMix/RowSource. Samples use random.Random(20261119).sample over sorted admitted native row IDs.
Reasoning comes from the explicit reasoning field or target/suffix <think> body. Trace forms use routing.form, form, or answer_form; absent form metadata is reported as not_recorded.
Any nonzero answer-only count refuses R1_ANSWER_ONLY_ROWS before WAITING_REVIEW. The retained fixture refuses for 16,000 pose and 8,000 pointing rows; no production census is claimed.
The 79,971-row fixture took 52.4 seconds and produced 429134 bytes. Linear full-store estimate: about 6.1 minutes for at most 555,756 source rows; host timing is unmeasured (work/build24i/EVIDENCE_RUNTIME.json).
WAITING_REVIEW.json contains utc, identity, v_sha256 and deadline_utc. The wait is 120 minutes (k/a.json review_wait_seconds=7200), polling every 30 seconds; expected independent review time is 15–20 minutes.
n_review1 writes <n_root>/n_r/review.json. The directory must be owned by the job user and mode 0700; the file must be regular, non-symlink, owned by that user and mode 0600.
The JSON requires verdict PASS and config_identity equal to live/identity.txt. All additional fields belong under evidence. Missing files remain pending; unusable files, FAIL, wrong identity and timeout refuse.
Acceptance copies the receipt to Q_NS/p/rv.json, pins its sha256 as r1_training.review, synchronizes the preparation receipt pins, and writes REVIEW_ACCEPTED.json {utc,identity,review_sha256} before t.py.
Refusal writes REVIEW_REFUSED.json with utc, identity and refusal. No training starts; the final copier still runs. TERM/USR1 interrupts the review helper and follows the same cleanup path.
out/arm_go.py takes no review argument and emits only the three-file GO delta. Review is never embedded in k/a.json. Arming, independent review and orchestrator launch GO are separate.
PREP_FIELDS.json/.md list 33 exact preparation paths; prep_diff.py pre.json v.json rejects all others. N_IDENTITY.txt identifies only the localised input, not the prepared production config.
After verification, the batch shell copies log tails, metrics, attempt/run metadata, marker hashes and .steps every 600 seconds and at exit; each copy is capped at 50 MB with at most 40 MB of log tails.
Exports occur at steps 100, 200, 400, 600, 800, 1000 and at stop; a separate copier checks them every 10 seconds. SESSION_NAMES_24F.json fixes their unchanged four-part GCS object names and three once-claimed stop generations.
The copier reads <n_root>/n_s/sess.json (owner-private directory 0700; regular non-symlink file 0600). Missing/unusable sessions leave archives local with a named status; no credential is supplied.
Checkpoints occur at step 1, every 7,200 seconds and at stop. Timed checkpoints remain local; the final completed stop checkpoint goes to <n_root>/n_ck/<jobid>/ if size plus 50 GiB is free, otherwise GCS is attempted or a local-only marker remains.
Signal cleanup allows 420 seconds for the workload, 10 for copier shutdown and 155 for publication, leaving 15 of the 600-second warning. No KillWait grace is assumed; large-transfer completion is unproven.
Accepted loss: node loss between exports restarts the leg from the last export with a fresh optimizer. Small-file GCS mirroring awaits the orchestrator's credential ruling.
The declaration is r1_training.routing_slices=deferred_first_boundary; init_policy=step400_export_weights_fresh_v1. N starts a fresh optimizer, counter and schedule; its first 200 steps are local steps 1–200.
N keeps P's regenerated S1 routing base (receipt ca0616db, database 4e8e6c04); all six deferred routing cells contain zero new rows. Distance calls, unit conversions and camera wording receive no targeted new examples.
VQA adds 7,971 direction twins and removes 109 named-route matches (107 newly removed), leaving 55,808 direction and 8,562 route-planning rows (work/build24/CENSUS.json).
Held-out wording exclusions, K1 and room rules remain active; routing_opener_init=keep and the step-544 lineage stay pinned. Two absent head slots remain NOT_PRESENT; seven other slots remain DEFERRED and block official reads.
Relative-count rows, answer-prior weights, the frame-host alias and step-time patches wait for the first boundary. N has no tower-scale freeze; H3 can fire again at the first look.
