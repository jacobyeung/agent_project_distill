# Next-leg trainer tree rebuilt from the sealed LEG-S1 source (lane tree_rebuild, 2026-11-15)

Question: can the lost next-leg trainer tree (A0 without fusion, A2 with GF-1) be rebuilt straight to its end state from the sealed LEG-S1 source and the recovered texts?
Answer: yes, up to the frame host. Base = trinity-1-18 tree_s1_admissionfix_168872, seal b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99. That is the source of kit 07ca49df / run 469ddece, and it equals /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar (845b1789) file by file. The seals 38917ea5 and 37845077 belong to earlier trees. Three Codex builds produced tree seal a1f559e2a58a3f317a88506081cf24b86727e646b52c1eb51afce59ba8232022 (838 files) and kits A0 9057919d… and A2 6737fcc9…. On CPU, 136/136 tests pass. Changed-statement coverage is 4358/4370; the unexecuted statements are 10 frame-host and 2 GPU, and none is CPU-reachable. Real rows, real export bytes, dense data, full stores and GPU have not been exercised.
Evidence: trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild/out/{BUILD1,BUILD2,BUILD3}_REPORT.md, PRELAUNCH_CARD.md, FRAME_HOST_JOB.md, TREE.diff, B3_COVERAGE_CLASSIFIED.json. Mirror: trinity-1-13:/scratch/jjyeung/n30_mirror/tree_rebuild/tree_rebuild_b3_a1f559e2.tar (sha256 39b2b5db82d0a5ae4b3208febf4aa49ab98fa8057a02733d464c2919c6d1c9df).
Options rejected: rebuilding pass by pass; restarting from the r1_contract.py fragment, which predates the root-map fix; drawing a second withheld-room list instead of using rows_rebuild's 634820b4; letting the tree hold its own grammar copy instead of the shared 49e814eb, wrapped.
What might not work, and how we would notice: the real row formats differ from the fixture envelopes (the real-row proof refuses); the 14 lost evidence records cannot be regenerated (the kits refuse at init_m544 evidence); the filtered populations raise repeats above 4 (the metadata gate refuses before materialization); the parent shell staging path is not reproduced end to end (the frame-host job shows it).
Tests that would settle it: REAL_ROW_PROOF.sh on rows_rebuild slices; the frame-host CPU job on Orchard; the two independent tree reviews; the first GPU step at world 4.
Status: built, not reviewed. Contract patches wait for the review_contracts verdict. No launch.


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

**Answer.** Keep the shared grammar byte-identical and enforce native event rules in a wrapper. Apply the one pinned room draw at intake and read time. Read component records by hash and gate actual bank items. Check filtered population metadata before materialization and use a deterministic native type sampler. Transport evidence and reader metadata through a portable dependency closure. Stage bounded opaque inspection kits with explicit missing-input blockers.

**Reasons and evidence.** The bank and record mutations, room-alias refusals, parent parity, reload equality and native sampler proofs are recorded in `BUILD2_REPORT.md`, `B2_MODEL_PROOF.json`, `B2_SAMPLER_PROOF.json` and `B2_FINAL_TEST_RESULTS.json`. Exact numeric results and their source paths are in the report. The shared-room digest mismatch remains explicit in `WITHHELD_BINDING.json`.

**Options rejected.** Self-asserted clean evidence, caller-selected bank labels, an independently drawn room list, natural type sampling under a revised table, an unlabelled dense fixture and a launch-capable kit without host proof would weaken admission. The implementation refuses those cases or leaves the corresponding capability blocked.

**Defaults.** The qualification rooms do not add an exclusion. The fusion warm-up follows the base setting and the full stage uses the remaining registered duration. The plan population table remains provisional. Historical record filenames that could not be recovered are labelled GUESS; their slot schema is a reconstruction default.

**What might not work and how we notice.** The opaque source capsule is not a native executable tree; the inspection job stops after verification. Real evidence and final reader indices remain unavailable, though their closure wiring passes a synthetic proof. Native inference and grounding runtime refuse recognized restricted-lineage reads; legacy bank adapters and the broader evaluation/export audit remain unfinished. The coverage classification identifies unexecuted CPU statements without disguising them as GPU work.

**Tests that would settle it.** Supply the hashed component records, complete filtered population receipts and final-reader indices; execute the native job entry from the staged closure; audit every lineage evaluation/export reader; run the frame-host producer/reader proof on real RGB and dense manifests. Close the listed CPU coverage gaps before treating the strict gate as passed.

**Status.** The implementation and bounded CPU proofs are delivered; deployable-kit integration and admission remain incomplete. No launch ran. See `BUILD2_REPORT.md` for the exact scope and test evidence.

## Build 3

Question: Can the repaired leg preserve its warm-start routing rows, execute a sealed source closure, enforce bank scope and supply a bounded CPU host proof before launch?

Answer: Use a vocabulary-bound keep switch, native source archives, explicit legacy-bank refusals and a separate CPU preparation packet. Missing real inputs refuse. The executable adapters and local evidence are delivered; host admission and launch remain blocked.

Reasons and evidence: The real loader preserves or resets tiny donor rows according to the switch (`out/B3_LOADER_PROOF.json`). The parent configuration records reproduce exactly (`out/B3_PARENT_REPRO.json`). Native producers and readers reach the CPU boundary (`out/B3_NATIVE_JOB_PROOF.json`). The final kit entries stop at named missing evidence (`out/B3_FRESH_ENTRY_PROOF.json`). Coverage and all remaining gaps are recorded in `out/B3_COVERAGE_CLASSIFIED.json`.

Options rejected: Do not reset verified same-lineage rows silently; do not trust caller bank labels; do not invent real counts or hashes; do not run full stores on Trinity; do not treat archive verification alone as executable integration. The parent archive convention is retained, with native internal source names explicitly disclosed.

What might not work and how we notice: Native staging/runtime or path relocation may fail on the host; input pin, import, write-boundary and preparation gates must report that failure. Real populations may violate repeat limits or exclusions; the metadata gate must refuse before training. A2 may exceed memory/time estimates; measured admission must replace guesses. Unsupported evaluation formats cannot produce registered reads until they have authenticated adapters.

Tests that would settle it: Run the bound CPU host job on GO, require every statement obligation and every rank's real first batch, inspect actual pose/camera/pointing metadata, then bind independent review and measured GPU admission. Run the registered paired reads using the exact scope and thresholds in `out/PRELAUNCH_CARD.md`. No such remote or GPU work ran in this build.

Status: Review artifacts delivered; real-data and host admission remain pending. See `out/BUILD3_REPORT.md` for the exact local coverage status and the staging/name-scope limitations.
