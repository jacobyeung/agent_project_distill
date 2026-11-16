# Trace ruling for the repair seal (2026-11-15)

**Status:** proposed ruling, read-only analysis. Nothing was built, launched or admitted. It needs the orchestrator's acceptance and two user defaults (section 2.9). Paths are under `/scratch/jjyeung/orch_cd/` unless absolute. Scripts and their outputs are in `trace_ruling/work/`.

## Question

Which trace should each training row of the repair seal carry, and what should the model do at inference, so that (1) no row is answer-only and no trace states a quantity that the frames, a printed response or an explicit computation does not supply, and (2) the model does not route a type whose program loses to direct answering with deployed perception?

## Answer

1. **Form by type (O1).** Program rows only for absolute distance, room size and the three camera types. Every other type gets a direct row whose trace locates objects by frame, states relations in words, and writes out the question's own steps. No direct trace is empty, and none states a measurement.
2. **Deployed responses for the routed object types only (O3, restricted).** Render absolute-distance and room rows from the pipeline that runs at inference, on training scenes. Keep rows whose response agrees with ground truth, and rows whose response is a real failure and whose trace then answers directly from the frames. No row ends in a refusal.
3. **Direction and counting stay direct.** O2 is rejected for this seal and O4 is rejected outright. O3 for hard direction and a tool-plus-reconcile form for counting are gated experiments, not seal content.
4. **The builder re-renders two families and rebuilds one.** Facing and totals become direct rows; units stay program rows but in the sealed event schema; recovery is rebuilt on routed types with real failure statuses. The integration tree must stop admitting direct rows that contain calls and responses; today it supervises that text.

The sealed leg did train answer-only rows: 15.3 of its 192 language rows per step. It also trained 95.0 rows per step that state a measurement with no derivation. Both forms end with this seal.

---

# Part 1: facts

## 1a. Row families and trace forms

### The sealed leg (job 169097, steps 1 to 544)

A step holds 192 language rows: 128 VQA and 64 routing. The design step is 320 rows (pose 64, VQA 128, MDG 32, routing 64, pointing 32; `leg_s1_tree/out/NO_FLAG_MIX.md:7-13`). The run had no MDG stream and used 288 (`leg_s1_tree/out/PRELAUNCH_CARD.md:37-43`; `leg_s1_review/CONTINUATION_FACTS_20261114.md:32`). The language rows are the same in both.

Counts and expected rows per step are exact for production: the local pass reproduced both production digests (`leg_s1_tree/out/ADMITTED_TYPE_HISTOGRAM_07ca49df.md:3,11-18,31-36`). Expected rows are natural shares under the stream quotas, not per-type quotas. `NO_FLAG_MIX.md:35-43` gives design values within 0.2 rows of these.

| Stream | Type | Trace form | Rows | Expected rows per step |
