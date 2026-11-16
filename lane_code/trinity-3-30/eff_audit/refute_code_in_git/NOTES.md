# Refute check: change #1 code-in-git (2026-11-16)
- Base tar t_b01ce449beffe35b.tar: 792 files, 0 above 512 KB.
- lane_code_filter.py on that tree: keeps 766 (16 dups listed in DEDUP manifest), drops 10 non-dup files: .gitignore, SPEC_v3.12.md(dup?), 4 csv, 3 ppm, LICENSE, .provenance fixtures (dropped.txt).
- lane_code_sync.sh (mtime 11-16 06:19, after the 2-18 loss) already pushes every lane's code hourly to GitHub lane-code; last run 11:23Z verified.
- Staged tree_rebuild/work holds tree_r1, build1..build4 (dedup'd against base).
- Rebuild plan's 30-40 agent-h = S0..S8 incl. rows data rebuild, census, 6-8 h reviews, Orchard CPU job, GPU admission; code-only share is S3+S5 (13-18 h) plus part of S4.
- Lost 2-18 work was in-progress lanes (tree_r1 passes, rows_r3, contracts R2), not accepted builds; tree_commit.py commits accepted builds only.
