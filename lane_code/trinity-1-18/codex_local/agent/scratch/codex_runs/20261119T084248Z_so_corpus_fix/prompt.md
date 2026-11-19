# so_corpus_fix: the trace-corpus ingest tool's second review round

`L=/scratch/jjyeung/orch_n30/so_corpus_fix`. Due 10:30Z 2026-11-19 (`date -u` at each step).

## Inputs (copies in `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/corpusin/`)
- The ingest tool `ingest_read.py` (with `corpus_score.py`, `pub.py`, `add_read.sh`, `SCHEMA.md`, `HOWTO.md`, its build/review briefs `BRIEF_*.md`) and its tests `tests/` (`test_synthetic.py` runs here; `test_real_returns.py` needs real returns that are not on this node: do not try to run it, say so).
- The second review's verdict `REVIEW2_VERDICT.md` (NO-GO on three synthetic cases; real outputs verified lossless and score-exact): (1) kit report alias `devrows:<id>` retried for any record (ingest_read.py:420) must apply only to key-only records; (2) native must validate required arms and their exact key sets against the request/report declarations (:661); (3) native must compare full task identity (question, options, scene/video, truth, every identity field) before a join and refuse contradictions (:643).
- The published corpus index (read only, small): `/data2/jjyeung/agent_project_data/distill_trace_corpus/INDEX.jsonl` and `SCHEMA.md` there.
- `LEFTOVER.md` (the corpus lane's list; you own item 1 only).

## Tasks
1. Copy the tool into `$L/work/tool/`; for each of the three findings add a synthetic test that fails on the current code (show the failure) and passes after the smallest fix; keep every existing test passing.
2. Decide, from the code and the published INDEX.jsonl (format, arms, ids of each published read), whether the fixed tool would change the bytes of any published read; list each published read_id with "unchanged" or "would change, because ...". If any would change, write the exact re-ingest commands (new read_ids, never overwriting) for the owner to run on trinity-3-30; do not run them.
3. Deliver `$L/out/patches/01_ingest_review2.diff` against the input `ingest_read.py` (+ tests), `$L/out/REPORT.md` (first line `VERDICT: ...`, test commands with exact outputs).
## Standing rules (nobody answers questions while you run; decide, record the decision and its reason, continue)
- You run once, on trinity-1-18. Your only writable folder is `$L` (named above). Everything else is READ-ONLY. Inputs copied for you are under `$L/in/` and `/scratch/jjyeung/orch_n30/so_in/` (a mirror of trinity-3-30 paths: `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/...`).
- No git, no ssh, no scp, no Slurm, no deletion outside `$L`, no GPU (`CUDA_VISIBLE_DEVICES=""`), no paid model API. Network only for reading library documentation when this dispatch has network.
- Searches stay inside named small directories (`$L`, `/scratch/jjyeung/orch_n30/so_in`, the Python env's site-packages). Never search or list `/home`, `/data*`, `/project`, `/` or `/scratch` recursively; sweeping searches have crashed nodes.
- Load: another user trains on all eight GPUs of this node. Prefix every command that computes with `nice -n 10`; set `OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false` and `torch.set_num_threads(8)` in test code; at most 8 cores and 30 GB RAM at any time; keep `$L` under 3 GB.
- Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` (Python 3.12, torch 2.11 CPU, transformers 5.12), with `PYTHONDONTWRITEBYTECODE=1`. The production trainer runs torch 2.11 + CUDA 12.9 on 4x H100 80 GB (Orchard), so the installed torch source in this env is the same version: cite it (file:line) for every framework behaviour you rely on, and cite the official documentation page when you have network. Never rely on memory for framework behaviour.
- Any change you build to production code goes behind an explicit switch whose default is OFF, so the default path stays byte-identical to the input tree; deliver it as a unified diff in `$L/out/patches/NN_<name>.diff` against the input tree, plus tests in the patch. Never edit the input tree in place: work on a copy under `$L/work/`.
- Write `$L/work/STATUS.md` after each task (time from `date -u`). Final report `$L/out/REPORT.md`: first line `VERDICT: <DONE|PARTIAL> <one sentence>`; then numbers (measured vs estimated, always labelled), patches with test commands and their exact outputs, what could go wrong and how we would notice, and what is not done. If time runs short, finish tasks in order, package what is done and say what is not.
- Do not invent measurements. A number you did not measure or read from a named file is an estimate and says so.
