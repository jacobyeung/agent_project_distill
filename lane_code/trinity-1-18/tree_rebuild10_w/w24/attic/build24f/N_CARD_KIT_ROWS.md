Vehicle N uses MINIMAL. GO remains false; the kit awaits independent review.
Init = P’s step-400 export `5083243c` from run `6ed2c7aa`, via the export-only receipt `b467c32b`.
No checkpoint or state after P’s step 400 initializes N. No handover fill remains.
Tree: `e1e64652087c2cde689620e4fb6edca57123feccae78c8a0a4b70ce8f7b35c10`.
Kit n: `a2613a727be9bc53f6e38f56a102454d59ea437a42fe6fe1d1e73609e9a9f09f`.
Kit q: `d7eb355d0caa0fd6eb127a821e57508ef82f024626f61e1f3594a0a74a44fb35`.
Seal and pin sources: `work/build24e/KIT.json`, `out/M400_PINS.json`.

N requests advanced, four GPUs/four ranks and one launcher; the allocation runs its own mode-q canary.
Declaration: `r1_training.routing_slices: "deferred_first_boundary"`.
Init policy: `r1_training.init_policy: "step400_export_weights_fresh_v1"`.
The export supplies weights only. N starts a fresh optimizer and a fresh step counter at zero.
N’s first 200 steps therefore use local steps 1–200, including a fresh schedule and sampler position.
They start from P’s step-400 weights; they do not resume P’s optimizer or advance P’s counter to 600.

N keeps P’s routing stream: the regenerated S1 base, with receipt `ca0616db` and database `4e8e6c04`.
Recovery, absolute_distance, units, coverage_distance, coverage_units and camera_wording hold zero new rows.
Distance calls, unit conversions and camera wording receive no targeted new routing examples in this window.
Their behavior can still change through training; improvement is not established by the CPU fixture.
Routing-slice gates start at the boundary where those slices enter.

| VQA change against P | Count |
|---|---:|
| Named-route removal list after the existing lists | 109 matches; 107 newly removed |
| Direction half-turn twins, path (b) | +7,971 |
| Eligible direction rows | 55,808 |
| Eligible route-planning rows | 8,562 |
Counts and unchanged exclusion pins: `work/build24/CENSUS.json`.

Held-out wording exclusions, K1 removals and room rules remain active.
P’s trained opener rows stay `routing_opener_init=keep`; the step-544 lineage remains pinned.
The two absent head slots retain NOT_PRESENT; seven other slots stay DEFERRED, blocking official reads.
The pose record stays bound. Relative-count rows, answer-prior weights and the frame-host alias wait for the first boundary.
Step-time patches remain absent/OFF.
N launches without a freeze of the tower scale in the point-depth head. H3 can fire again at N’s first look for the same cause.
CPU evidence: `work/build24b/CPU_SUMMARY.json`; both kits ADMIT at init 400 and every rank has finite full-forward loss.
