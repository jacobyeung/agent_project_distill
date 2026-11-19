Production verdict: this component-evidence mismatch is fixture-only; it is not a launch blocker and needs no kit or tree fix.
The failing `v.json` pins `/tmp/q_22c714e1/prepared.json` at `48f780da664bc51af5f4065cf5e908a52bb2931b8f604c4594787bfdaf1bc1b2`; its physical file is `rehearsal3/prepared.json`.
Exactly seven fields differ: `receipt_sha256` in data_rows_r2, depth_init_vc, geometry_tower, heads_depth, heads_pose, init_m544 and segmenter.
Each records `70c8f62ed09b325fc63794625da30309ed13c363d9ca1b019d341cf365cd17fa`; native `artifact_status(cfg)` returns `9744cfe502b6080825f93052274c6726269a9d8bf49bed80384ae2167fb757e3`.
Both NOT_PRESENT records (heads_gf1_connector and heads_frame_embeddings), all status labels, reasons and data records match exactly; `rehearsal3/COMPONENT_EVIDENCE_DIFF.json` contains the complete values and field diff.
Cause: `rehearsal_preserve_metadata.py:41–49` publishes a donor receipt and rebinds it after preparation; the fixture must recompute component evidence before re-pinning that preparation.
Kit `h.py` and `rv.py.sync_preparation` preserve component_evidence; the native, handover-repinned and host-repinned preparations all retain the same stale evidence in rehearsal3.
Production `a.py:30–39` calls `production_proof.py:141–158`, whose native preparation runs through `s1_admission.py:225–231`; `carrier_c1_run.py:638–640` records artifact_status directly, and subsequent re-pinning preserves it.
Production keeps receipt b467c32b and artifact 5083243c fixed: seven DEFERRED slots and two mechanically proven NOT_PRESENT slots remain equal at step 100; `rehearsal4/PRODUCTION_COMPONENT_EVIDENCE.json` records the source invariant and authenticated pins.
This production verdict follows from code and metadata; production preparation, the real heads payload and the production step-100 export were not executed here.
Fixture repair: rehearsal4 recomputes evidence through the native function and re-pins preparation plus its fixture admission reference; `FIXTURE_DIFF.json.build24fr3` lists all changed fields.
PASS: native admission, prepared(), trainable groups, single-process native export, host/review re-pinning, stale-preparation refusal and official-read refusal (`rehearsal4/FIX3_VALIDATION.json`).
The rehearsal mounts the existing 939-file sealed source snapshot read-only to avoid concurrent live-tree changes; it shares existing stores/model/donor read-only and writes fresh run outputs in rehearsal4.
`go_rehearsal.sh` selects rehearsal4; shell syntax and `rehearsal_runner.py --prepare-only` pass. The four-rank reproduction and training were not run.
Lane command: `cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24 && nice -n 10 bash work/build24f/go_rehearsal.sh`.
