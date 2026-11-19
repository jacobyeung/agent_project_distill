Vehicle N uses MINIMAL. Normal q/N kits have GO=false; only the GO template is armed. Production requires the reviewed routing-selection pin and the independent prepared-config review.
Init is P's authenticated step-400 export 5083243c from run 6ed2c7aa. Nothing after P step 400 initializes N; N starts a fresh optimizer, counter and schedule.
Tree: 189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710. Exactly the three Option T files differ from tree 57a1f14d; 937 files remain identical.
Kit q: 6215397d48349983ef30c5b7492618d570f4586d0c85f9d101e00c7bb96669c3; kit N: 814db98aabae2859b8be5bc8e509cc8fd43bd9baa32c11ec293176f155b116f8.
GO template: 05f0ffa1c8467c46c61f958ad239e9aef393bc3e6e293a55202c507ec84fbd76. Upload deltas and stream root are in UPLOADS_24K.json; the three-file GO delta is separate and is not uploaded.
N requests advanced, four GPUs/four ranks, one launcher, 48 CPUs, 800G and 24 hours. Slurm signals TERM 600 seconds before the limit. TK_JOB_START reaches bwrap, torchrun and train().
Mode q plans authenticated copies in bootstrap scratch. The native tree creates fresh q and runs the copier through its staging hook. Pool refresh bytes belong to the plan; metadata is source_code.json.
The request uses job_tmp, k/h.json binaries, the pinned staging plan and routing_selection, and the existing k/r.json routing_base. It adds no routing_inputs or routing slices.
The native canary writes q/host.json and pins it in q/RESULT.json.host_receipt. h.py accepts only that exact path and hash, retains all host assertions and loader checks, and writes v.json.
P receipt ca0616db has no regenerated digest. out/jr.sh runs a.py r on preempt without a GPU: 16 CPUs, 128G, two hours; logs use x_22c714e1/j/.
Mode r stages the same inputs, runs the native routing builder and P regeneration/equality recipe, and publishes routing_selection.json to <n_root>/o/<jobid>/. Production stores are available only on Orchard.
The lane reviews that file, then runs out/arm_routing.py to bind u/<its sha256> in fresh q and N GO copies and emit their upload delta. Until then, mode q refuses R1_ROUTING_SELECTION_PIN_MISSING.
Both GO variants publish v.json (at most 50 MB), identity.txt and live evidence to <n_root>/o/<jobid>/live/ before WAITING_REVIEW. The job computes the prepared identity with its sealed tree.
Evidence names are e0–e3 for pose/VQA/routing/pointing, e4 for the room audit, e5 for its hash and size, e6 for BENCH v2, and e7 for dev-S1. Their combined cap is under 2 MB.
The BENCH v2 list is benchmark_scene_exclusions, sha256 3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970. The dev-S1 list is dev_scene_exclusions, sha256 a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5.
These are the two lists bound by N’s config. The room authority supplies canonical and physical-room mappings; it does not replace either exclusion list. Every stream reports both list hashes beside whole-store counts after removals.
The census uses native Rows.row and PoseMix/RowSource, Rooms.canonical/room and the native exclusion readers. Any protected-room row refuses R1_PROTECTED_ROOM_ROWS before the wait.
Each stream publishes admitted counts, database hashes, question types, answer-only/trace-form counts and 40 deterministic sampled native row IDs. Frames, indices and timestamps are omitted; the sampling seed is 20261119.
Only answer-only VQA or routing rows refuse R1_ANSWER_ONLY_ROWS. Pose and pointing answer-only rows remain published and do not refuse, as required by rulings 2000Z/2001Z.
The retained fixture scanned 79,971 rows in 53.7 seconds, produced 964,322 bytes, and found zero protected-room rows. It published 16,000 pose and 8,000 pointing answer-only rows without refusal. No production census is claimed.
The fixture-rate estimate for at most 555,756 source rows is 6.2 minutes. Host timing is unmeasured. Independent review is expected to take 15–20 minutes.
WAITING_REVIEW.json records utc, identity, v_sha256 and deadline_utc. The wait is 7,200 seconds and polls every 30 seconds. n_review1 supplies <n_root>/n_r/review.json.
The review directory must be user-owned mode 0700; the receipt must be a regular non-symlink user-owned file mode 0600. It requires verdict PASS and config_identity equal to live/identity.txt; extra fields belong under evidence.
Acceptance pins a private receipt snapshot and synchronizes preparation pins before t.py. Missing files wait; FAIL, wrong identity, unusable files and timeout refuse. TERM/USR1 interrupts the wait and still runs final publication.
PREP_FIELDS.json/.md and prep_diff.py retain the allowed preparation paths. N_IDENTITY.txt identifies the localized input, not the prepared production config. Arming, independent review and launch GO are separate.
The copier reads training output Q_NS/p/q/r and publishes bounded log tails, metrics, attempt metadata, marker hashes and .steps every 600 seconds and at exit, capped at 50 MB including at most 40 MB of log tails.
Exports occur at steps 100, 200, 400, 600, 800, 1000 and at stop. The export copier polls every 10 seconds. SESSION_NAMES_24F.json fixes object names and three once-claimed stop generations.
The copier reads the private <n_root>/n_s/sess.json. Missing or unusable sessions retain local archives with a named status. No credential is included; small-file GCS mirroring awaits the orchestrator ruling.
Checkpoints occur at step 1, every 7,200 seconds and at stop. Timed checkpoints remain local; the final stop checkpoint uses <n_root>/n_ck/<jobid>/ when size plus 50 GiB is free, otherwise GCS is attempted or local-only status remains.
Signal cleanup budgets are 420 seconds for the workload, 10 for the copier and 155 for publication, leaving 15 seconds. No KillWait grace is assumed; large-transfer completion is unproven.
Node loss between exports restarts from the last export with a fresh optimizer. The routing_slices declaration remains deferred_first_boundary; all six deferred cells contain zero new rows.
VQA retains 7,971 direction twins and 109 named-route removals (107 newly removed), leaving 55,808 direction and 8,562 route-planning rows. Held-out wording, K1, legality and room rules remain active.
routing_opener_init=keep and the step-544 lineage stay pinned. Two head slots remain NOT_PRESENT; seven other slots remain DEFERRED and block official reads. Relative counts, answer priors, frame-host alias and step-time changes wait for the first boundary.
The external native-host fixture is work/build24k/go_rehearsal_k.sh. It reads rehearsal3 (fallback rehearsal2), attaches only the fixture review, and has not been run.
