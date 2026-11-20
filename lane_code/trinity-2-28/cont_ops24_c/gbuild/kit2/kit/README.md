# Grounding funnel analysis kit

This is a CPU analysis and frame-planning kit. It is **blocked, not GPU-ready**.
The production 64/96-frame ground-call adapter is not implemented. The launcher
reports missing inputs and exits 2 on a run request; it never starts inference.

Run from the delivered bundle root:

```
python3 -s -m unittest discover -s kit -v
python3 -s kit/analyze.py
bash kit/run_funnel.sh 0 --dry-run
python3 -s kit/score_evidence.py joined_evidence.jsonl funnel_results.json
```

`analyze.py` consumes the two bundled corpus files under `work/`. It inventories
300 required object occurrences per step, including objects whose call was
skipped. `summary.json` separates final-answer scores from unit-normalized gap
scores. Its frame-support groups are observable proxies; they are not S0–S5.
The code reproduces the reader's question-only operand parser and official MRA
threshold arithmetic. Room bootstrap draws whole physical rooms 10,000 times,
then averages items with their multiplicities. Undefined subgroup draws are
counted and omitted from percentile calculations; they are never zero-filled.

`funnel.py` assigns the first observed failure. An upstream unknown stops the
assignment. The worse of two stages means the earlier stage, not the larger
stage number. The synthetic matcher uses any raw target match at IoU > 0.5 for
proposal existence and at least half a selected track's member frames to bind
an annotated identity. The selected correct frame count
excludes unmatched frames. Real GT joins must retain raw pixel visibility and
annotation validity separately; an invalid pose is not an invisible object.
No word-substring instance binding is allowed (for example lamp to ceiling).

`tasks.json` contains the same called items at each step and nested 32/64/96 source
indices. Repeatedly inserting the midpoint of the largest gap adds frames
without removing an original anchor; it leaves the answering frames unchanged.
It includes a 32-frame parity arm. It does not force calls on non-calling items.

The real first-capture dry run checks source-frame plans and replays the logged
selector argmax for `scannet/scene0515_00`. It stops before RGB decoding and
proposal inference because the RGB, raw masks and dense annotation joins are
missing. It is not a synthetic image substituted for a real capture.

The inference adapter must satisfy `ADAPTER_REQUIREMENTS.md` before this kit can
be called a rerun kit. `INPUTS_REQUIRED.json` records known sources and unknown
sizes explicitly. No kit output is a training row.
