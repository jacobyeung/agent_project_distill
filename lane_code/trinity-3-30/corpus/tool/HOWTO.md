# HOWTO: add one read to the trace corpus (lane cont_ops18, trinity-3-30)

The corpus lives at `/data2/jjyeung/agent_project_data/distill_trace_corpus/` (`reads/<read_id>.jsonl.gz`, `index/<read_id>.json`, `INDEX.jsonl`, `SCHEMA.md`, `raw/`). Files there are written once and never overwritten. The tool and staging live on trinity-3-30 under `/scratch/jjyeung/orch_n30/corpus/` (`tool/`, `stage2/`, `pub/`); a copy of the tool sits in the corpus root as `tool/`.

## After each fetched, complete return (one command, CPU, seconds)
```
cd /scratch/jjyeung/orch_n30/corpus && bash tool/add_read.sh <return dir or result.tar.gz> <read_id> <set> <vehicle> <job id> "<purpose>" <RESULT event path> [--inputs <package dir>] [--official]
```
- `read_id`: `<run>_s<step>_<set>_<vehicle>_<token>`, e.g. `6ed2c7aa_s400_devS1R0_direct_a59a7bff4c4`.
- `--inputs`: routed packages only (the package folder holding `package/0.tgz`, e.g. `r1route/out3/A4`).
- The script runs `ingest_read.py ingest` into `stage2/`, prints item count, sha256 and the per-arm mean scores, then publishes the read file and its index line with `copy_archive.py` (governed, 4 MB/s) and rebuilds `INDEX.jsonl` in staging. Exit 2 means a partial or failed return: nothing is published; fix the fetch or rerun with `--archive-partial` only for a return that is final and known partial.
- Check the printed means against your RESULT before you post it (or run `python3 tool/corpus_score.py stage2/reads/<read_id>.jsonl.gz --arm B2048 --by question_type`).

## Rules
- Run on trinity-3-30 only; never point `--out` at /home or /data*.
- `SAME` on a rerun is normal. Exit 3 (different bytes for an existing read_id) means a new read_id is needed; never overwrite.
