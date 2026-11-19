"""Write the current kit contract and the requested finding-to-test mapping."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
snapshot=ROOT/'out_round5'
simulation=json.loads((OUT/'evidence/round5_simulation.json').read_text())

grid='''The processor limit is **576 spatial patches (derived from source)**.
`T=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`:
`T/student_pilot/batches.py:155` passes `longest_edge = 32*384*384`.
`TF=/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers`:
`TF/models/qwen3_vl/video_processing_qwen3_vl.py:50–57` computes the temporal
pixel budget in `smart_resize`; `:95` defines 16-pixel patches and `:235`
converts resized pixels to spatial grid dimensions. Thus the 32-frame spatial
limit is `(32*384*384)/(32*16*16) = 576`, independent of orientation.
The audit accepts `[32,18,32]`, `[32,32,18]` and `[32,24,24]`, and refuses
`[32,20,30]` (600 patches). Tests execute the installed `smart_resize` function
on 1920×1080, 1080×1920, 512×512 and 480×480 sources; they do not simulate a
full torchvision processor call. Eight maximum-grid FP32 pixel tensors occupy
**905,969,664 bytes (derived)**, below the unchanged 1-GiB group guard before
other tensors; the audit still measures the complete group including targets.
'''

pooled='''1. Concatenate loss vectors in rank order 0–3. Within each rank, sort the
   component keys and stream-mean keys, then append the ordered microstep losses.
   If the complete OFF vectors agree bitwise, require bitwise ON equality.
2. Otherwise define `D = max_(rank,i) abs(OFF2−OFF1)` and
   `M = max_(rank,i) max(abs(ON−OFF1), abs(ON−OFF2))` over **all four ranks**.
   Accept iff `M <= 2 × D`; the multiplier is fixed at 2 before seeing ON.
   There is one pooled decision, and per-rank diagnostics cannot veto it.
   A zero D permits zero numerical difference only; the global bitwise branch
   remains strict, including signed zero.
3. Require matching CPU hashes and ordered row draws, checkpoint, plan, state,
   field names and ON provenance. Nonfinite values fail. Any rejection keeps
   `C1_CPU_PREFETCH=0`.

`acceptance.json.pooled` records the global D, M, multiplier, threshold, OFF
spreads and ON differences. `acceptance.json.ranks` retains local diagnostics;
their `accepted` flags describe the per-rank rule and are not acceptance gates.
Only the top-level `accepted` field admits the replay. Pooling can mask a small
discrepancy behind a noisy scalar or rank. The strict CPU row-hash gate remains
mandatory. This screen is not a calibrated confidence interval from two repeats.
'''

sim='''### Simulation: false-refusal rate under OFF nondeterminism

These are **simulation results, not production measurements**. Each of 100,000
trials per row draws three independent standard-Gaussian loss vectors with the
same true mean, four independent ranks and the stated number of independent,
equally noisy scalars per rank. Seed: 20261119. Both rules use multiplier 2.
The delivered snapshot rule requires every per-rank bound to pass; the pooled
rule takes D and M over all four ranks. The simulation cross-checks its vectorized
decisions against both Python implementations on 32 trials per row.

| Noisy scalars per rank | Delivered per-rank false-refusal | Pooled false-refusal |
|---:|---:|---:|
'''
for row in simulation['scenarios']:
    sim+=f"| {row['scalars_per_rank']} | {100*row['delivered_per_rank_false_refusal']:.3f}% | {100*row['pooled_false_refusal']:.3f}% |\n"
sim+='''
Exact counts are in `evidence/round5_simulation.json`; reproduce them with
`work/simulate_round5.py` using the CPU environment in REPORT. The one-scalar
case gives about 80% false refusal for the delivered rule and 13% for pooling.
For the per-rank one-scalar case, `1-(2/3)^4 = 80.247%` is the analytical reference.
Monte Carlo standard error is at most 0.158 percentage points per table entry.
Correlated or differently scaled losses can behave differently; these rates do
not estimate production error rates. Components and stream means share losses,
so their effective scalar count can be small. If both OFF runs and ON are bitwise
equal, neither rule refuses. Replay and continuation screens are correlated;
their table rates must not be multiplied as independent probabilities.
'''

command='''Run the loss check as soon as the first continuation record is complete.
Set `CONTINUATION_METRICS` to that attempt's `metrics_<attempt>.jsonl` and
`LAUNCH_METRICS` to the first launch's completed metrics file. The command reads
the existing files and prints JSON; it does not stop jobs or change switches.

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' "$PYTHON" -I -s -B \\
  "$DELIVERY/kit_timing/continuation_check.py" --replay-out "$REPLAY_OUT" \\
  --continuation "$CONTINUATION_METRICS" --first-only
```

After continuation update 21 completes, run both kill rules:

```bash
date -u
nice -n 10 env CUDA_VISIBLE_DEVICES='' "$PYTHON" -I -s -B \\
  "$DELIVERY/kit_timing/continuation_check.py" --replay-out "$REPLAY_OUT" \\
  --continuation "$CONTINUATION_METRICS" --launch "$LAUNCH_METRICS"
```

Exit 0 means the requested checks passed; any nonzero exit blocks acceptance.
`--first-only` reports `wall_pending=true` and cannot clear kill rule 2. The full
check requires 20 complete timing updates, refuses missing or reordered ranks,
inconsistent steps, changed loss keys, nonfinite timers and changed switch values,
and reports both wall and data medians/ratios. It excludes the first continuation
update's cold start. Apply the next-checkpoint OFF action above after a failure.

The admitted checkpoint/configuration and CPU-audited row plan remain prerequisites.
Normal trainer metrics contain no `plan_sha256` or ordered row-draw array
(`T/student_pilot/carrier_c1_run.py:1735–1745,2509`), so this checker cannot
independently authenticate them from metrics. The ordered replay and CPU audit
must already pass, and r1_ops must launch the continuation with those exact
admitted inputs. The command checks the matching logged step, losses and switches.
'''

mapping='''## Review round 5: finding -> fix -> test

| Finding | Fix | Regression or evidence |
|---|---|---|
| 1 LOW | Derive the 576-patch spatial cap from trainer `longest_edge` and installed `smart_resize`; share it with the audit sidecar. | Installed resize on 16:9, portrait and square sources passes; 600-patch and temporal-overflow grids refuse. Snapshot rejects all four accepted source cases. |
| 2 LOW | Pool D and M over all four ranks, with multiplier 2, in replay and continuation. Record simulation false-refusal rates. | Each rank in turn exceeds its local bound but passes the pooled replay; all four outside local bounds still refuse. Strict bitwise, schema, signed-zero and nonfinite controls remain. |
| 3 INFO | Provide a read-only continuation command for the immediate loss check and the full wall rule. | CLI fixtures pass pooled losses and an 11/13 wall ratio, refuse ratio 1 and excessive loss, and refuse incomplete/invalid records. Snapshot lacks the command. |
| 4 INFO | Require the processor manifest's exact path/SHA256 pin to equal the merged receipt's model pin; load it through the trainer's pin verifier. | Valid pin passes; changed bytes or an alternate path refuse before processor construction. Snapshot attempts to load the wrong processor. |
| 5 INFO | Cite LF lines 694/698/702/706 and explain carriage returns. | Read actual bytes, verify all four step identities and eight carriage returns, and require corrected citations in both documents. |

The review's proposed fixture in which **every** rank's sole scalar exceeds its
local bound yet the pooled maximum passes cannot exist: for the rank j with
largest D, `M_j > 2*D_j = 2*D_global` implies `M_global > 2*D_global`.
The regression instead makes each rank fail its local bound in turn while a
different rank supplies larger OFF spread; it also checks the impossible case
correctly refuses. This preserves the requested four-rank max policy and multiplier.

The continuation calculation is a small core plus CLI parsing and fail-closed
record validation; the complete helper is about 80 lines. The extra validation
prevents missing ranks or incomplete timing windows from silently passing.

The production shape lists are at LF lines **694/698/702/706** in `look2.out`.
The same file contains eight carriage returns: `str.splitlines()` yields 720
lines while LF counting yields 712. There are no extra configuration lines.
'''

note=(snapshot/'NOTE_FOR_TREE_REBUILD.md').read_text()
note=note.replace(note.splitlines()[0],'VERDICT: DONE All five round-5 kit findings are addressed; trainer patches remain byte-identical and the 31-test coordinator gate has passed.')
note=note.replace('0 < h*w <= 520','0 < h*w <= 576')
needle='Inherit production thread settings for both arms.'
note=note.replace(needle,needle+' `BASE_MANIFEST` must match the\nmerged receipt’s `model` path and SHA256 exactly. `data_only.py` checks that pin\nbefore loading the processor and uses `run.load(run.pinned(receipt["model"]))`,\nthe trainer’s preparation path at `carrier_c1_run.py:792,800`.\n')
note=note.replace('covers the audited outputs; it does not establish a universal processor bound.', 'covers the audited outputs; future rows still require the same checks.\n\n'+grid)
a=note.index('1. If OFF repeats agree bitwise')
b=note.index('## First continuation and r1_ops readouts')
note=note[:a]+pooled+'\n'+sim+'\n'+note[b:]
note=note.replace('1. At `start_step + 1`, compare each rank’s `components` and `stream_means` with',
    '1. At `start_step + 1`, concatenate `components` and `stream_means` from all four ranks and compare with')
note=note.replace('on that subset. Require zero row-draw/plan mismatches and zero nonfinite values.',
    'over all four ranks on that subset, using the same shared `pooled_loss_acceptance`\n   helper as replay. Require zero row-draw/plan mismatches and zero nonfinite values.')
note=note.replace('The optional **`C1_CPU_PREFETCH_FALLBACK=1`**',command+'\nThe optional **`C1_CPU_PREFETCH_FALLBACK=1`**')
note=note[:note.index('## Review round 4: finding -> fix -> test')]+mapping
(OUT/'NOTE_FOR_TREE_REBUILD.md').write_text(note)

report=(snapshot/'REPORT.md').read_text()
report=report[report.index('## Numbers:'):report.index('## Review round 4:')]
report=report.replace('look2.out:702,706,710,714','look2.out:694/698/702/706').replace('look2.out:701,713','look2.out:693,705').replace('look2.out:703','look2.out:695')
report=report.replace('h*w <= 520','h*w <= 576')
report=report.replace('`out_round3/` preserves the complete input delivery; its build-20 series is archival and is not the current deployment target. ', '`out_round5/` preserves the complete input delivery. ')
report=report.replace('zero warmup, from the same pinned checkpoint and CPU-audited plan. Define per rank', 'zero warmup, from the same pinned checkpoint and CPU-audited plan. Define over all four ranks')
report=report.replace('Otherwise require **M <= 2 × D** on every rank','Otherwise require one pooled **M <= 2 × D**')
report=report.replace('rank. Compute D and M on that same subset;', 'rank. Compute pooled D and M across all four ranks on that same subset;')
report=report.replace('Both CPU arms', 'Both CPU arms')
report+='\n'+grid+'\n'+sim+'\n'+mapping
report='VERDICT: DONE All five round-5 kit findings are addressed; handed-over trainer patches remain byte-identical.\n\nThe kits use the processor’s 576-patch limit, pool replay and continuation loss\nchecks across four ranks, verify the processor pin, and provide executable\ncontinuation kill-rule checks. `out_round5/` preserves the input delivery.\nNo production GPU run or speedup measurement was performed.\n\n'+report
report+='''
## Exact local commands and outputs

Final local test outputs will be inserted after the serial test runner completes.

'''
old=(snapshot/'REPORT.md').read_text()
report+=old[old.index('## Coordinator command'):old.index('## Sources, risks and remaining host work')]
report+='''## Sources, risks and remaining host work

SOURCE_NOTES retains installed torch 2.11 citations for the unchanged trainer.
This audit uses `torch/_tensor_docs.py:5523–5533` for `.tolist()` and
`torch/_torch_docs.py:9815–9825` for setting intra-op threads before CPU work,
under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages`.
The official [Tensor.tolist documentation](https://docs.pytorch.org/docs/2.11/generated/torch.Tensor.tolist.html)
and [set_num_threads documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html)
were checked. The pooled bound is an operational policy, not a framework guarantee.

The CPU audit covers only the first ten continuation updates. Later oversize
groups can refuse with fallback OFF. A noisy rank can mask a smaller loss
discrepancy under pooling; D/M and the strict CPU hashes expose the relevant
evidence. Host contention can erase data-wait savings; the wall rule detects that.
The continuation checker reads logged metrics, so checkpoint/configuration/plan
admission remains required; metrics alone do not authenticate row draws.

Actual production torchvision coverage, CPU audit, GPU replay, CUDA attribution,
production memory fit and speed measurements remain host work. None ran here.
The eight known unrelated broad-suite failure entries remain outside this fix.
No trainer patch, input tree, GPU, Git, SSH or external job was changed or used.
Before/after comparisons and the delivered-rule simulation are retained because
the dispatch explicitly requests them as regression evidence.
'''
(OUT/'REPORT.md').write_text(report)

p=OUT/'kit_timing/README.md';readme=p.read_text().replace('h*w <= 520','h*w <= 576')
readme=readme.replace('otherwise each rank’s maximum ON-to-either-OFF deviation is at most twice that rank’s maximum OFF-to-OFF deviation', 'otherwise the maximum ON-to-either-OFF deviation across all four ranks is at most twice the maximum OFF-to-OFF deviation across all four ranks')
readme+='''
`--manifest` must match the merged receipt's exact `model` path/SHA256 pin;
the audit verifies it before processor construction. The spatial cap is derived
from trainer `longest_edge` and installed `smart_resize`; the handover note gives
both source locations, the arithmetic and simulation false-refusal rates.

Use `continuation_check.py --replay-out "$REPLAY_OUT" --continuation
"$CONTINUATION_METRICS" --first-only` for immediate pooled first-update losses.
After update 21, replace `--first-only` with `--launch "$LAUNCH_METRICS"` to
require the slowest-rank wall median ratio over updates 2–21 versus the launch's
last 20 updates to be strictly below 1.00. Both commands are read-only and return
nonzero on refusal. The complete executable commands and prerequisites are in
the handover note. Per-rank acceptance fields are diagnostic; replay admission
uses only the global pooled result.
'''
p.write_text(readme)
