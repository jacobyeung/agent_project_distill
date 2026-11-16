# Read-only re-review after fixes: presence-probe analysis.py and direct.py (lane b11_presence)

Read-only. No edits, GPUs, ssh, git, or searches outside the named paths. REFUTE: concrete defects with file:line plus a failing test or CPU snippet. Final message: first line exactly `GO`, `GO AFTER FIXES` or `NO-GO`; then numbered findings (severity, file:line, evidence, fix). At most 60 lines.

Spec: as in /scratch/jjyeung/orch_n30/b11_presence/work/review/REVIEW_PROMPT.md (read it). Earlier versions: work/review/analysis.v1.py and work/review/direct.v1.py. Two earlier reviews returned NO-GO; their findings are in /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T125709Z_b11_review/final_message.md and .../20261116T125630Z_b11_review/final_message.md.

Under review now (lane folder /scratch/jjyeung/orch_n30/b11_presence):
- code/analysis.py (sha256 2ccbb4d6...): two phases. `fit` (default) reads only train captures' journals and writes out/analysis/FROZEN.json; `--read-heldout` reads FROZEN.json (refuses if code or prep changed), reads only held-out journals, never refits, and decides only with full coverage of the 143 held-out appearance-order items. Answer rule: exact option match, else wrong; head_optlik is a secondary report. Torn final lines tolerated, interior malformed lines raise.
- code/direct.py (sha256 e7f13c6d...): continues on forced_close or stopped_unclosed; continuation scored with answer tokens and cap 64; parity on the first 16 selected items on every invocation; journal rows bound (sha) to cell, model files, item and frames; stale bindings refused; torn tail repaired (moved aside) on resume; fsync after each chunk.
- Tests: code/test_analysis.py (synthetic journals; result out/tests/ANALYSIS_SYNTH.json, all checks true) and code/test_direct.py (scripted engine stand-in; out/tests/DIRECT_FAKE_ENGINE.json, all true).

Verify each earlier finding is fixed, and look for new defects the fixes introduced (leakage, decision gate, answer rule, bootstrap, reader-protocol divergence in direct.py, resume correctness).
