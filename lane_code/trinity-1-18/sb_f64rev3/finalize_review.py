import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
def read(name): return json.loads((OUT/(name+'.json')).read_text())
kit,base,patched=map(read,('kit_review','baseline_regression','patched_regression'))
assert (kit['tests'],len(kit['failures']),len(kit['errors']),len(kit['skipped']))==(49,0,0,0)
for r in (base,patched):
    assert (r['tests'],len(r['failures']),len(r['errors']),len(r['skipped']))==(109,0,1,0)
    assert '/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl' in r['errors'][0][1]
static,mutation=map(read,('static_review','mutation_review'))
assert mutation['kills']==mutation['mutants']==5
assert all(v['met'] for v in mutation['baseline'].values())
matrix=read('pilot_gate_matrix')
assert all(v['pilot_accepted']==(v['required_behavior']=='accept') for v in matrix['cases'].values())
assert read('builder_matrix')['all_required_behaviors_met']
rows=['The configured production inputs remain MISSING. Paths below come from the retained reviewer evidence and the reviewed config; no path or owner has been invented.',
      '', '| Input or evidence | Exact path or config location | Owner | Status |', '|---|---|---|---|']
for key,v in static['missing_inputs'].items():
    owner=v['owner']
    if key=='POOL.jsonl': owner='MISSING producer identity; orchestrator must assign the producer'
    path=v.get('path',v.get('location'))
    rows.append(f'| {key} | `{path}` | {owner} | MISSING |')
rows += [
    '| Four-rank GPU pilot | MISSING output directory; `kit/scripts/mem_pilot.py --out DIR` writes `DIR/PILOT.json` | Orchestrator authorizes allocation; pilot operator is MISSING | MISSING; unmeasured |',
    '| Actual all-rank CPU first batches | MISSING evidence output path | W production binding; execution owner must be assigned by orchestrator | MISSING |',
    '| Complete production token audit | MISSING shard and summary output paths; `kit/scripts/token_audit.py --out` selects them | Production owner must be assigned by orchestrator | MISSING |',
    '| Reader memory evidence | MISSING evidence output path | Reader lane | MISSING |',
    '',
    'The GPU and closure entries in `sb_f64fix2/out/FIX2_REPORT.md` do not meet an exact-path handoff requirement. The pool entry names its path but explicitly lacks its producer. The orchestrator must assign those fields; this review cannot infer them.',
    '',
    'The config omits `r2_sampling`, `preparation`, and `r1_training.store_hashes.{pose,routing,pointing}`. It sets `r1_training.{row_plan_sha256,host_receipt,review}` to null. The report’s phrase “all null” should read “absent or null.”',
]
(OUT/'OPEN_ITEMS.md').write_text('\n'.join(rows)+'\n')
method='''The review ran on trinity-1-18, used CPU only, and wrote review artifacts only inside this workspace. The wrapper disables CUDA and network-dependent model loading, sets eight numerical-library threads and nice level 10, and caps virtual memory below 40 GB. No Git, SSH, GPU execution, or process termination was used.

`kit_check.py` adapts the retained reviewer runner to the reviewed kit and adds its new test module. `regression_check.py` retains both reviewer suites and redirects their writes here. Both runners install write guards and retain temporary directories. Test fixture files keep their native schemas; evidence JSONs in `out/` record input hashes.

`static_check.py` hashes and diffs every kit file and every `work/scripts` file, plus the regression script and wrapper. It checks every archive file against disk and every kit checksum. Generated logs, caches, temporary fixtures, and proof trees are not source-code changes. The archive is inspected without extracting or executing it.

`pilot_gate_matrix.py` retains the reviewer’s three controls and original retained encodes, changing only kit/output paths and provenance. `builder_matrix.py` reruns the builder’s expanded four-case matrix, including its explicitly synthetic flag-only ceiling case. `mutation_check.py` creates explicitly synthetic 300/301-row controls from the retained record schema; these test gate logic, not production sampling or admission. Its eight ceiling checks use the real auditor and trainer check_row with two-dimensional token tensors, four streams, and default/overridden ceilings.

The core refusal fix meets sb_f64rev2’s required code change. The task separately asks that longest-row selection include failed rows. The implementation still excludes failures from the summary’s longest list; it only includes them in per-stream counts and max_tokens, then refuses the audit. This distinction is reported explicitly rather than treating refusal as proof of literal list inclusion. No failed audit reached an accepted plan in the controls.

The OPEN-item assessment distinguishes existing configured paths from unassigned future evidence paths. An unknown path or owner is reported as MISSING. This review makes no production readiness or GPU memory claim.

The comparison to sb_f64fix and the mutation variants is retained because the task explicitly requires these designed comparisons.
'''
(OUT/'REVIEW_METHOD.md').write_text(method)
report='''# GO AFTER FIXES

The CPU gate rejects the required bad audits, but the literal failed-row inclusion requirement and exact-path/owner handoff remain incomplete. Production inputs are still MISSING.

1. **Core gate fix passes.** `mem_pilot.py:72-85` re-derives complete stream counts, refuses every failure/ceiling violation, and accepts tripwire-only rows. Failures beyond both capped lists and forged cached counts also refuse.
2. **Required edit — longest list.** `kit/scripts/token_audit.py:314` still excludes every failed row from `longest`; only `max_tokens` includes their known token counts. No failed audit is accepted, but this does not satisfy the task’s literal “longest-row selection includes failed rows.”
   Include failed records with known token counts in the ranked candidates; continue refusing tokenless fetch failures and all failed audits. Update `kit/tests/test_pilot_gate.py:89-105` to test failed-candidate inclusion and refusal, including a maximum-length failed row. Regenerate checksums/archive after code edits. Owner: kit builder.
3. **Required edit — handoff table.** In `out/FIX2_REPORT.md`, assign the pool producer and exact output paths/operators for items 4 and 8. Those assignments are MISSING; the orchestrator must supply them. Expand each path and owner in the table; `OPEN_ITEMS.md` lists verified input locations and unassigned fields.
   Change “all null” to “absent or null”: `r2_sampling`, `preparation`, and three stream-hash keys are absent. Owner: report author.

**Independent results** (commands run from `/scratch/jjyeung/orch_n30/sb_f64rev3`):
- `bash run_cpu.sh static_check.py`: archive SHA256 `472d7775378a82ee365f11aa531f25b065129e339be1a3157abe1b85d24c6f89`; all 58 archive files match disk and all 45 checksum entries pass. `out/static_review.json` binds inputs.
- The complete kit diff changes only `scripts/mem_pilot.py`, new `tests/test_pilot_gate.py`, and `SHA256SUMS`. Outside the kit, only the two reviewed wrapper paths change; regression code is identical. See `out/tree.diff`.
- `bash run_cpu.sh kit_check.py`: 49 tests pass, with no skips (`out/kit_review.json`).
- `bash run_cpu.sh regression_check.py baseline` and `bash run_cpu.sh regression_check.py patched`: each runs 109 tests, zero failures, one error for MISSING `/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl`; neither suite is fully passing.
- `bash run_cpu.sh pilot_gate_matrix.py`: all three reviewer controls pass; passing/tripwire audits accept and a failed-check audit refuses (`out/pilot_gate_matrix.json`).
- `bash run_cpu.sh builder_matrix.py`: all four builder controls pass, including flag-only ceiling refusal (`out/builder_matrix.json`).
- `bash run_cpu.sh mutation_check.py`: 5/5 mutants killed: remove failed counts, remove ceiling counts, reject tripwires, disable refusal, and trust cached counts. Seven independent controls pass on the unmutated gate (`out/mutation_review.json`).
- The same command exercises eight real-auditor ceiling cases; all refuse. `token_audit.audit:119,128-130` and trainer `check_row:1326-1330` use the same ceiling, before stream-specific returns. For normal two-dimensional batches, a real audit cannot emit `over_ceiling=true` with `check_row=ok`.
- `summarize` does mark the synthetic flag-only record launch-ready, but the pilot gate rejects it. This is not a real-audit bypass.

No reviewed files were edited. `out/OPEN_ITEMS.md` preserves exact production input paths and known owners; unassigned evidence paths/owners remain MISSING. Actual first batches, full token audit, GPU pilot, and reader evidence remain prerequisites for launch.
`bash run_cpu.sh finalize_review.py` validates these results and writes `out/REVIEW_INPUTS.json`; every review evidence JSON carries input SHA256s. `out/REVIEW_METHOD.md` records test scope and adaptations.
'''
assert len(report.splitlines())<=30
(OUT/'REVIEW_VERDICT.md').write_text(report)
(ROOT/'REVIEW_VERDICT.md').write_text(report)
inputs={}
for p in [Path(__file__),ROOT/'run_cpu.sh',*[OUT/(n+'.json') for n in ('static_review','kit_review','baseline_regression','patched_regression','pilot_gate_matrix','builder_matrix','mutation_review')],OUT/'tree.diff',OUT/'OPEN_ITEMS.md',OUT/'REVIEW_METHOD.md']:
    inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'REVIEW_INPUTS.json').write_text(json.dumps(dict(command='bash run_cpu.sh finalize_review.py',input_sha256=inputs,verdict='GO AFTER FIXES',report_lines=len(report.splitlines())),indent=2)+'\n')
(ROOT/'STATUS.md').write_text('The independent CPU review is complete. All 49 kit tests and all reviewer/builder matrix cases pass; both 109-test regressions have zero failures and the same missing-pool error. Five of five mutants are killed, and eight real-auditor checks reject ceiling violations. The core refusal fix passes, but the requested literal failed-row inclusion in longest candidates is absent, and several handoff paths/operators remain unassigned. The verdict is GO AFTER FIXES; exact edits and evidence appear in out/REVIEW_VERDICT.md. Production inputs and measurements remain MISSING.\n')
print('GO AFTER FIXES;',len(report.splitlines()),'report lines')
