# Build brief 5 of 8: reader-harness (lane `eff_reader_harness`, branch `eff/reader-harness`, Claude Opus, effort high, size L: 10 to 14 agent-hours)

Build one reader that every read of every export uses, so that a new read is a config with inputs and a plan of several reads runs in one job.

## Why

- Each read today is a new kit: the D0 read kit is a fork of the evalx27 package with a line-range `DIFF.md`, two fix rounds and two reader lanes (`REF/trinity-1-3/cont_ops/work/d0/readk/`); `trinity_read.py` exists in 14 distinct versions with 3 live builds (`AUD/kits/INVENTORY.md` section 2). A new read kit costs an estimated 3 to 6 h before submission.
- The general partition runs one of our jobs at a time, so D0 reads, K1 and VSTI queue one behind another (`B/events/k1_ops3/20261116T1102Z_ORCH_RULING_general_order.md`); the record on packed jobs estimates 1 to 4 h of queue per read (`distill_design/ORCHARD_PACKED_JOB_FEASIBILITY_20261114.md`, line 5). A plan that runs its reads in order inside one job pays that queue once and needs none of the isolation the packed design lacked.
- A read with the wrong frame layout costs 3 to 13 points and looks like a model result.

{{COMMON}}

## Scope: `tools/orchkit/reader/`

**`read.py`, the driver.** `read.py run --plan PLAN.json --pins PINS.json --out OUT/` executes a list of `orchkit-read-v1` configs in order. For each read it loads the export, builds prompts from the frozen item list, generates, scores, and writes predictions and one receipt (`{read_id, export sha, items sha, scorer digests, frames, counts, metrics, state}`). A read that fails is recorded with its traceback and the plan continues; a rerun skips every read whose receipt exists. The generator sits behind one small interface, so tests drive the whole plan with a deterministic stub and no model.

**Frame guard.** The driver compares the read's `frames.layout` and `frames.count` with the layout the export recorded at training and refuses a mismatch unless `layout_override_reason` is set; the receipt then carries the reason.

**`score/`, the scorers.** Port, without changing their arithmetic, the reviewed scorers of the D0 read kit: `REF/trinity-1-3/cont_ops/work/d0/readk/kit/reader/` (`chain.py`, `paired_read.py`, `official_adapter.py`, `official_score.py`, `records.py`, `worker.py`) and the native reader of `REF/trinity-1-18/trin_read/build_t6/trinity_read.py`. Keep the kit's rule that the official scorer source is a pinned member checked by digest before use: the main repository stays the authority for benchmark scoring, and this harness calls that source and never rewrites it. State in REPORT.md, per ported function, the source file and lines.

**`verdict.py`, the registered rules.** Port `stop_rule()` and the F1/F2 functions of `REF/trinity-1-3/cont_ops/work/d0/readk/f1f2.py`. Each rule function names the registered record it implements and that record's sha256, loads the record as the pinned member with role `record`, and refuses to return a verdict when the member's sha256 differs (use `cite.check_member` if lane eff_review_gate has delivered it; otherwise compare with `util.sha256_file` and say so). A record amendment then forces a code change and its review, which is the intent. Read `distill_design/D0_STOP_RULE_20261116.md` and `NEXT_LEG_INIT_RULE_20261116.md` once each; implement the stop rule as amended, and implement the init rule only if it is mechanical as written (list what is not).

**`plan.schema.json`** and `examples/plan_two_reads.json`.

**Runtime.** Modules under `reader/` run inside the model environment and may use its Python; anything the batch bootstrap runs before that environment is active stays 3.6-safe. The packed reader passes the opacity check: item identifiers, family names and scorer names bound for the batch host are opaque tokens whose meanings stay in a Trinity-side map, as in the existing kit.

## Files you own

`tools/orchkit/reader/` (all of it) and `tools/orchkit/tests/test_reader_*.py`, `tests/fixtures/reader/`.

## Tests (folder `tools/orchkit/tests/`)

1. The D0 read kit's own tests (`REF/trinity-1-3/cont_ops/work/d0/readk/tests/`), ported, all passing.
2. Parity: for every saved prediction file you can find on this node (in REF, in `/scratch/jjyeung/orch_n30/review_a0d/`, `/scratch/jjyeung/orch_n30/a0_design/`, or named by a design record as stored on trinity-3-30), the new scorer reproduces the banked number exactly. Targets: VSTI f17 66.95 and P1 m200 68.71; official VSI-Bench direct at step 544, six tasks 68.77; ReVSI direct, five categories 64.94; dev-S1 parent 71.64. List which targets had a prediction file here and which did not. Fetch nothing from another node, Orchard or GCS; a missing file is a line in REPORT.md and an input the orchestrator can order through the governor.
3. Plan runner with the stub generator: three reads, the second raises; reads one and three complete with receipts; a rerun executes only the second.
4. Frame guard: a mismatch refuses; an override passes and is recorded.
5. Rule guard: a changed record member refuses; the amended stop rule gives the registered verdict on each worked example the record contains.
6. The packed reader holds no word of the opacity list.

## Deliverables

Branch `eff/reader-harness`; `W/REPORT.md` with the parity table and the port map; the RESULT event; the result block in RECORD.

## Out of scope

Launch, staging and return (orchkit-core); any new scoring rule, routing rule or change to a registered rule; the D0 milestone reads in flight, which keep the confirmed read kit; concurrent steps in one job; running a model.

## Review

One independent review before any number from this harness is reported, because it scores. The reviewer starts from the parity table. Ask for it in the RESULT event.
