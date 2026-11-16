The source patches exclude byte-identical authority copies; their hashes are in `out/SCORER_COPIES.json`.

| File | Change |
|---|---|
| `a.py` | Build the named report locally after return; keep allocation outputs neutral. |
| `adapter.py` | Bind per-scene index comparison receipts without changing comparator frames. |
| `boundary.py` | Exercise tagged answers and refused-geometry decoding through the CPU boundary. |
| `budget.py` | Separate item-start cutoff from subprocess kill and reserve return time. |
| `engine.py` | Check strict canary scores, exclude refused parity positions, and scope geometry refusals. |
| `entry.py` | Accept a separately staged selected-frame reference list. |
| `indices.py` | Compare all prepared scene selections without recopying pixels. |
| `orchard.py` | Preserve the allocation and require staged bwrap in the inherited allocation entry too. |
| `o.py` | Place packets on shared storage, preserve CUDA allocation, use staged bwrap, and continue after proof exceptions. |
| `pixels.py` | Reject a decoded video whose full frame count differs from its selection. |
| `policy.py` | Refuse camera calls and disable own-geometry fallback on refused captures. |
| `report.py` | Withhold incomplete scores, name refused subtasks, disclose proof and frame checks, and use runtime refusal wording. |
| `scorer.py` | Use strict authority metrics and test the kit scorer on both comparators. |
| `venue.py` | Require an explicit host-bwrap fallback; default to staged bwrap. |

Tests preserve V1b coverage with these intended changes: namespace expectations use staged bwrap; geometry-refused non-camera items must decode; pixel fixtures include the total frame count; deadline tests use the distinct cutoff policy; release status comes from the current receipt. The tower fixture now prepares its own sample inputs instead of relying on a prior build directory.

Inherited transport tests that mutate external temporary pools remain unexecuted. Their names and reasons are in `out/TESTS.json`.
