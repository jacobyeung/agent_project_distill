# Next-leg trainer tree rebuilt from the sealed LEG-S1 source (lane tree_rebuild, 2026-11-15)

Question: can the lost next-leg trainer tree (A0 without fusion, A2 with GF-1) be rebuilt straight to its end state from the sealed LEG-S1 source and the recovered texts?
Answer: yes, up to the frame host. Base = trinity-1-18 tree_s1_admissionfix_168872, seal b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99, the source of kit 07ca49df / run 469ddece (= /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar, 845b1789). Current tree seal ba346bd9e8ba41ed0cd77fea5ae494df544b959ff9f80731f83d761f51a32343 (855 files, build 5); kits A0 8cdda797… and A2 58a9b42e…, both GO=false. Package suite: 2,185 run, 1,645 passed, 474 failure events that the untouched base shares case for case, 0 tree-only regressions; R2 343/343. Changed statements: 3,693 observed, 73 frame-host, 3 GPU, 0 CPU-reachable gaps. Real frame-host inputs, full stores and GPU have not been exercised. Unit rows: 2.871 per step, all distance programs in cm, ft and in; no square-feet rows (room stays direct).
Evidence: trinity-1-3:/scratch/jjyeung/orch_n30/tree_rebuild_w/out/BUILD5_REPORT.md, TREE_SEAL.json, FRAME_HOST_JOB.md, PRELAUNCH_CARD.md, MIX_A0.json; work/build5/CHANGED_COVERAGE.json, SUITE_COMPARISON.json. Package tree_rebuild_b5_ba346bd9.tar (sha256 bc31a06dd37e742dbf8bad493cbe5d90c18b2bf1dbb6b9f7ef992137a0b33726) in that out/ and at trinity-1-18:/scratch/jjyeung/n30_mirror/tree_rebuild/. Builds 1-3 history: trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild/out.
Options rejected: rebuilding pass by pass; restarting from the r1_contract.py fragment, which predates the root-map fix; drawing a second withheld-room list instead of using rows_rebuild's 634820b4; letting the tree hold its own grammar copy instead of the shared 49e814eb, wrapped.
What might not work, and how we would notice: the real row formats differ from the fixture envelopes (the real-row proof refuses); the 14 lost evidence records cannot be regenerated (the kits refuse at init_m544 evidence); the filtered populations raise repeats above 4 (the metadata gate refuses before materialization); the parent shell staging path is not reproduced end to end (the frame-host job shows it).
Tests that would settle it: REAL_ROW_PROOF.sh on rows_rebuild slices; the frame-host CPU job on Orchard; the two independent tree reviews; the first GPU step at world 4.
Status (2026-11-16 10:30Z): build 6 running: contracts r6 integration (exact patches on 32 files, three-way merge on 3 diverged files), orders T1-T5 (init as one pinned input), square feet as a valid direct unit. Second review requested only after build 6's suite completes with zero CPU gaps. No launch.


## Build 1

**Question.** How can the next-leg tree admit honest traces and construct native trainer inputs before the real row and frame stores arrive?

**Answer.** Use one versioned grammar and manifest boundary, bind the accepted init at preparation, preserve native masked event encoding, and authenticate final row/target membership in the trainer. Build dense membership from content and source ordinals while retaining each row's clock. Missing frame material stops at an explicit host boundary.

**Reasons and evidence.** The recovered review failures concern raw logical reads, scene aliases, clocks, masked responses and missing exclusion receipts. The implemented paths and their exact source locations are in `BUILD1_REPORT.md`; retained tests, mutations and coverage are in `TEST_RESULTS.json`, `MUTATIONS.json`, `CPU_PATH_PROOF.json`, `FAMILY_ENCODER_PROOF.json` and `COVERAGE_CLASSIFIED.json`.

**Options rejected.** Flat direct targets containing responses would supervise external values. Path- or canonical-name-based dense identity would split identical content. Unknown scene overlap or missing upstream receipts would erase exclusions. An exact parent-run resume would hide changed code or mixture. A silent frame fixture would misrepresent a real-data proof. The implementation refuses each alternative.

**Defaults and risks.** The shared validator and real-row envelopes are unavailable, so the documented conservative syntax and versioned envelope are integration defaults. Metadata cannot prove visual relations. Native ground-event continuations rely on the admitted row lineage and printed response provenance; they do not claim a newly checked geometry backend. Full-store admission requires a separate frame host. The installed native video processor has a failure reproduced on the untouched base. These limits are disclosed in `BUILD1_REPORT.md`.

**Tests that settle the open points.** Reconcile the shared validator against the retained mutation corpus; publish the complete pinned family inventory; run `work/build1/REAL_ROW_PROOF.sh` on those inputs; then run native CPU admission with the real root map and export metadata on the frame host. Exercise full-store resource guards there before any GPU admission.

**Status.** The bounded build and synthetic CPU proofs are delivered. Real-row, frame-host and pretrained-model validation remain pending; no training or launch was performed. Exact counts, seal identities and source paths are in `BUILD1_REPORT.md`.

## Build 2

**Question.** How can the tree bind the shared grammar, withholding, component policy and revised mix while real evidence and dense assets are unavailable?
