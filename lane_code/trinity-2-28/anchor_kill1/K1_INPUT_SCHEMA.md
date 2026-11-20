# K1 input contract

The production K1 comparison has not run. Its source pools are on trinity-1-18.
`anchor_analysis.py kill` is a tested scoring kernel, not a completed raw-pool adapter.

The kernel expects one JSON record per operand occurrence: exactly two per row,
2,024 occurrences over the exact 1,012 decision row IDs in
`sb_cachk/out/v2/POPULATION.json`. Before running, the adapter must assert those
exact IDs, train flags, room exclusions and source hashes. A count alone is insufficient.

Each record contains `row_id`, `room`, `capture`, `operand`, `baseline_id`,
`gt_visibility` (anchor string to GT mask area fraction), and `candidates`.
Each candidate contains `id`, `members` (anchor string to positive mask pixel count),
and `on_target` (boolean from the pinned K1 raster identity test).
Preserve stored pool order; it breaks equal-area ties. Null baseline IDs represent
not-seen calls. A missing eligible GT anchor produces no Locate line and not seen.

The adapter must reconstruct the linked candidates from the same sb_kbox4 served
configuration. It must reproduce the deployed candidate IDs and member frames
in the local SEEDS.json audit before computing any paired score. That audit's
on-target definition is IoU >=0.5 at the chosen track's largest frame; retain
the same identity definition for A3x and expose a cited-frame IoU sensitivity.
Do not substitute the carry seed masks for complete candidate pools.

The kernel reports on-target and not-seen rates, paired room-bootstrap change,
f, h, and nearest-visible-anchor sensitivity. It does not reproduce the served
distance replay. The specification's distance-type points and on-target points
must remain distinct. Both the exact-input adapter and independent review remain
owed if the missing inputs arrive.

The exact source file paths and available SHA256 pins are in
`K1_MISSING_INPUTS.json`; sizes are explicitly unknown because the files are
remote and SSH is forbidden. `K1_TRANSFER_FILES.txt` lists paths relative to
`/scratch/jjyeung` for a single InfiniBand tar pipe. The list contains 209 training
capture pools; only the registered 204 decision captures may contribute scores.

The transfer is a data request, not an instruction to launch an agent or repeat
a killed job. The transfer owner must stat the named files, record their sizes,
confirm the transfer fits within W's 20 GB limit and leave 100–200 GB free on
the destination scratch disk before moving bytes. Additional geometry dependencies
may be necessary for distance replay; request them only after inspecting the code.
