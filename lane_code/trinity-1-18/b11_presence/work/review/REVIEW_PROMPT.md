# Read-only refutation review: presence-probe analysis and direct-read scripts (lane b11_presence)

You are a read-only reviewer. Do not edit, run GPUs, ssh, use git, or search outside the paths named here. Your job is to REFUTE: find concrete defects with file:line and, where possible, a failing test or a small CPU snippet that demonstrates them. Do not argue for the code. Write your verdict to /scratch/jjyeung/orch_n30/b11_presence/work/review/VERDICT.md: first line exactly one of `GO`, `GO AFTER FIXES`, `NO-GO`; then numbered findings (severity blocker/major/minor, file:line, evidence, the fix it needs). At most 80 lines.

## Files under review (lane folder /scratch/jjyeung/orch_n30/b11_presence)
- code/analysis.py (sha256 d975b4ec...): fits read-outs on K1 train and prices K1 held-out items.
- code/direct.py (sha256 e691987b...): step-544 direct read of the same held-out items in vLLM 0.23.
Context only (already tested, not under review): code/prep.py (builds out/prep/CAPTURES.jsonl, ITEMS.jsonl), code/scorer.py (writes journals out/journals/{V,IY}/<capture>.jsonl: rows {arm, capture, obj, frame 1..32, logit, lp_present, lp_absent, top} plus a final timing row), code/test_analysis.py (synthetic test), out/tests/*.json.
Accepted reader code they copy from: /scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader/evaluator/{parity.py,media.py,budget.py,scoring.py,worker.py,evalpath/official.py}.

## Spec the code must meet
1. Data: K1 = 296 training captures, split by room into train (239) and held-out (57); no room in both. Per (capture, object category) GT per-frame visibility over 32 anchors and GT first-seen frame (1..32, 33 = never, None = an invalid frame precedes it). Held-out items: 143 appearance-order (4 objects, 4 options, exact letter) and 104 counting (MRA, official_mra).
2. Read-outs fitted on K1 TRAIN ONLY, no held-out information anywhere in fitting or model/arm selection:
   - head: a learned temporal head over the 32 presence logits; its prediction is the argmax of its own output; no tuned threshold outside its weights.
   - thr0 (logit > 0) and thrfit (threshold fitted on train) are references only.
   - counting: number of distinct presence runs from a per-frame presence head fitted on train GT visibility.
   - primary arm among V/I/Y chosen by room-grouped CV on train only, fixed before held-out is read.
3. Pricing: appearance order by sorting predicted first-seen frames and choosing the matching option; GT-presence program as ceiling sanity; constant baseline = best single answer on train; direct = step-544 direct read (B2048 budget arm is the primary direct score).
4. Decision rule (fixed): head path iff primary-arm head minus direct on held-out appearance-order items >= 10 task points AND the paired 95% interval is above zero. Interval: room-cluster bootstrap.
5. direct.py must reproduce the accepted reader's protocol: prompt via parity.prompt (thinking on, 'ours' context), duplicate layout of the 32 anchors with frames_indices duplicated, media.kwargs, greedy, max 16384 tokens, seed 17, prefix caching off, B2048 via budget.classify/continuation (force-close and 64 answer tokens), scoring.score_item; parity.compare on the first 16 items. It is labelled unclaimed (vLLM 0.23 not 0.32). Resume must never double-count an item.

## Questions to try to refute
- Any held-out leakage (fitting, tau, arm choice, constants, tie-breaks)?
- Is the hazard head's first-seen distribution correct (sums to 1, indices 1..33 aligned to GT)? Is fit deterministic?
- Does answer_order pick the right option, including ties and orders not among the options?
- Is the bootstrap a correct paired room-cluster bootstrap? Is the decision computed on the right rows and arm?
- Do direct.py prompts, media metadata, budget continuation and scoring match the reader exactly (look for any divergence, e.g. score_item cap/finish arguments for the B2048 arm, text reconstruction, journal resume, the parity gate)?
- Any crash path on real journals (missing frames, partial captures, timing rows)?
