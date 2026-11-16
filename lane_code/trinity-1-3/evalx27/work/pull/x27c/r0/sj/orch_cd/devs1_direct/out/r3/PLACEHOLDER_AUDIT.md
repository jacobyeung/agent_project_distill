The active r3 frame manifest and receipt templates contain no placeholder rate. Historical outputs remain unchanged. Findings include non-timing mentions of room-label placeholders, identified by JSON pointer in the inventory. The complete JSON inventory records every JSON pointer or source line.

| File | Occurrences | Disposition |
|---|---:|---|
| `/scratch/jjyeung/orch_cd/back_dir/out/r2/DEV_BACKDIR/FRAMES.json` | 153 | Read-only facing-away payload: must replace timing manifest and pins before binding. |
| `/scratch/jjyeung/orch_cd/back_dir/out/r2/DEV_BACKDIR/TASKS.jsonl` | 150 | Read-only facing-away payload: must replace timing manifest and pins before binding. |
| `out/BIND_CHECKLIST.md` | 1 | Superseded output; do not run or resume. |
| `out/DESIGN_RECORD.md` | 3 | Superseded output; do not run or resume. |
| `out/FRAMES.json` | 153 | Superseded output; do not run or resume. |
| `out/MISSING_LABELS.jsonl` | 11 | Superseded output; do not run or resume. |
| `out/RECEIPTS_cp1m200.templates.jsonl` | 142 | Superseded output; do not run or resume. |
| `out/RECEIPTS_f17.templates.jsonl` | 142 | Superseded output; do not run or resume. |
| `out/RUNCARD.md` | 1 | Superseded output; do not run or resume. |
| `out/TASKS.jsonl` | 1547 | Superseded output; do not run or resume. |
| `out/adapter.py` | 1 | Superseded output; do not run or resume. |
| `out/r2/DESIGN_RECORD.md` | 1 | Superseded output; do not run or resume. |
| `out/r2/EXCLUDED.jsonl` | 11 | Superseded output; do not run or resume. |
| `out/r2/EXCLUDED_MISSING_ROOM.jsonl` | 22 | Superseded output; do not run or resume. |
| `out/r2/FRAMES.json` | 153 | Superseded output; do not run or resume. |
| `out/r2/MISSING_LABELS.jsonl` | 150 | Superseded output; do not run or resume. |
| `out/r2/RECEIPTS_cp1m200.templates.jsonl` | 1525 | Superseded output; do not run or resume. |
| `out/r2/RECEIPTS_f17.templates.jsonl` | 1525 | Superseded output; do not run or resume. |
| `out/r2/RELEASED_DEV.jsonl` | 889 | Superseded output; do not run or resume. |
| `out/r2/RUNCARD.md` | 1 | Superseded output; do not run or resume. |
| `out/r2/TASKS.jsonl` | 1525 | Superseded output; do not run or resume. |
| `out/r2/adapter.py` | 1 | Superseded output; do not run or resume. |
| `out/r2/test_adapter.py` | 1 | Synthetic fps=1 fixture in superseded tests. |
| `out/test_adapter.py` | 1 | Synthetic fps=1 fixture in superseded tests. |

Facing-away `FRAMES.json` has the same 152 captures and frame/anchor bytes as this lane’s pass-2 manifest; all 152 carry fps=1. Its cell names and PINS still describe the old input. The r3 adapter refuses that manifest. `TASKS.jsonl` also contains 150 fps=1 fields. `ITEMS.jsonl`, `ROWS.jsonl` and `STRATA.jsonl` carry no fps=1 fields. Both the task timing and frame manifest need rebuilding and repinning. This audit does not write to the other lane.

The active r3 tests deliberately submit fps=1 in negative cases; those values never enter payload receipts.
