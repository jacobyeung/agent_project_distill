import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
units=json.loads((B/'proofs/rows/UNITS.json').read_text())
p=L/'out/MIX_A0.md';s=p.read_text()
s=s.replace('| 22280 | 0.1289 |','| 10945 | 0.2623 |')
s=s.replace('Population values below are plan metadata, not newly filtered counts.', 'Population values below are plan metadata except units, whose admitted population comes from `work/rows_slices/slices_final/COUNTS_A0_v4.json`.')
s=s.replace('| routing | units | program with GT response | 2.400 | 2.871028 | 10945 | 0.2623 | `work/records/design/NEXT_LEG_REBUILD_PLAN_20261115.md#4`; `out/MIX_A0.json` |', '| routing | units | program with GT response | 2.400 | 2.871028 | 10945 | 0.2623 | `work/rows_slices/slices_final/COUNTS_A0_v4.json`; `out/MIX_A0.json` |')
p.write_text(s)
(B/'STATUS.md').write_text('''# Build 6 status

The contract patches are installed. Exact hashes and hunk dispositions are in `work/build6/INTEGRATION.json`.

The next-leg edits require a pinned init, gate final family retention, accept direct square-feet and inches answers, and require distance/room score breakdowns by asked unit. Their tests are pending.

The packet suite and diagnostic R2 suite are running. Packet supporting fixtures are absent from the supplied folder; no passing suite is claimed. The complete packaged tree/base comparison remains pending.

The bounded unit conversion check passed; room square-feet coverage is absent. Counts, hashes and the precise scope are in `work/build6/proofs/rows/UNITS.json`. Real-row replay remains unqualified until its reader and grammar results are reconciled.

Both kits remain non-admitting. Restaging, final coverage, the delivery package and final report are pending. No launch, remote service or GPU was used.
''')
(B/'EVIDENCE_DISPOSITION.md').write_text('''# Init evidence disposition

The selected launch input is pinned in `out/INIT_INPUT.json`. No tested D0 export was supplied, so the recorded default is the step-544 fallback. This file records a choice and supplies no admission evidence.

Every evidence obligation in `out/RECORDS_TO_REGENERATE.md` remains. None is removed. The init record and the pose, depth, frame-embedding and depth-init lineage records must bind the selected artifact and its full ancestry. The slot `init_m544` retains its registry name for compatibility; its evidence must describe the selected input, including D0 if the input pin changes.

The program-choice records, external frozen-tower records, row-population record and connector-training record retain their existing checks. A different input pin requires fresh export metadata and opener-vocabulary evidence. No missing record was fabricated.
''')
