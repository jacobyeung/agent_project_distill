# Native intake blocker

The unchanged w19 `student_pilot.r2_contract.validate(row, "vqa")` calls the pinned shared direct-trace grammar. Its numeric provenance rules license instance lists and their counts, but do not license numerical increments in per-frame tallies.

Example: `sb_rowC2_39c100227b18cc042ddb2e28`

```text
<think>
Tally new instances at their first sampled frame:
tissue box: frame 1: 1 -> 1.
chair: frame 1: 1; frame 16: 2; frame 24: 1; frame 25: 1 -> 5.
1 < 5.
</think>

B
```

Native result: `ValueError: Shared grammar: line_kind,number_not_allowed,exhaustive_frames,number_not_allowed,number_not_allowed,line_kind`.

The semantic checker and `tally_gate.py` verify this row directly against GT. `ground_rows.pack/validate` accepts a normalized envelope, but that result does not override the direct intake failure. N needs explicit tally grammar support, followed by the unchanged build checks rerun against a new sealed kit. This packet does not change N.
