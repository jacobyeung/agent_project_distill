Production verdict: this trainable-group mismatch is fixture-only; the metadata comparison finds no production launch blocker.
Native `r1_handover.py:293–305` reconstructs P from its pinned preparation/model config and compares its live group table with N before wrapping (`carrier_c1_run.py:2924`).
The tied fixture donor has 27 LLM tensors / 992,686 parameters; the post-load untied target has 28 / 1,984,942, adding `lm_head.weight` with 992,256 elements (`rehearsal3/CAUSE_GROUPS.json`).
The heads, pose, encoder-copy, frozen-parameter and frozen-module tables agree; the exact native refusal is reproduced.
Production artifact 5083243c and receipt b467c32b authenticate the metadata; the receipt pins the export and topology inputs rather than storing an optimizer group table itself.
`rehearsal3/PRODUCTION_GROUPS.json` shows equal P/N native tables, equal exported/full_ft accounting (8,953,803,264 trainable LLM parameters), equal recorded pose/depth names and independent embedding/head parameters.
That production check uses staged metadata and meta tensors, with P's pinned base/camera/depth metadata and N's recipe, overrides and attachments; it reads no production weights.
`rehearsal3/model` and `donor/export` carry independent equal-valued embedding/head tensors; native `p_export_receipt.produce` binds the regenerated donor preparation, export and receipt.
The synthetic pose-model boundary supplies this untied manifest before native preparation validates it; retained row stores remain pinned. Native target loading changes no parameter ownership afterward.
The current native exporter preserves the step-544 lineage, routing vocabulary, readout settings and component metadata exactly (`rehearsal3/METADATA_PRESERVED.json`).
The canary returned ADMIT; room, handoff and fixture gates pass. Its row/forward audit covers the same weight bytes; native handover and gates also pass after metadata rebinding.
RAN and PASS: `nice -n 10 bash work/build24f/check_rehearsal_groups.sh`; native loading and `verify_trainable_groups` pass, and a deliberately tied target refuses (`rehearsal3/SINGLE_PROCESS_GROUPS.json`).
`FIXTURE_DIFF.json.build24fr2` records changed fixture fields and tensor inventories; `rehearsal3/FIX2_VALIDATION.json` records validation.
The lane runs: `cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24 && nice -n 10 bash work/build24f/go_rehearsal.sh`.
The launcher selects `rehearsal3`; this agent has not run the four-rank reproduction or training rehearsal. Native code, kits, production configuration, admission and legality are unchanged.
