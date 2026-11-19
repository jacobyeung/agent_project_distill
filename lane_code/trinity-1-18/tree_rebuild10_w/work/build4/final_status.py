"""Write the current handoff status from final receipts."""
import json
from pathlib import Path

L=Path(__file__).resolve().parents[2]
audit=json.loads((L/'work/build4/FINAL_AUDIT.json').read_text())
coverage=json.loads((L/'work/build4/CHANGED_COVERAGE.json').read_text())
text='''# Build 4 status

**NOT READY. The requested qualification is incomplete.** The updated tree, restaged kits, diff, inventory, seal, report and design record are delivered. No launch, network service or GPU was used.

The final report is `out/BUILD4_REPORT.md`. It records each review item's disposition, the real-row table, refusal causes, proof boundaries and remaining work. The current design decision is in `out/DESIGN_RECORD_tree_rebuild_20261115.md` under Build 4.

Both kits match the final source (`work/build4/FINAL_IDENTITY.json`). Both scans are clean, all relative config paths have a staging-plan entry, and both unsigned authorizations remain GO=false (`work/build4/KIT_CHECKS.json`). Physical staging with the actual pinned environment remains unproved.

The final extracted-package delta passes {tests} tests (`work/build4/package_final_delta/results.json`). The final all-tree attempt discovers 2,177 tests but stops at the lane reserve before executing them (`work/build4/package_1794787256256291931/PACKAGE_RESULT.json`). The earlier R2-only package ran 235 tests with one harness error; the corrected path passes in the delta check (`work/build4/package_1794786581946641940/PACKAGE_RESULT.json`). The complete package requirement remains unmet.

The final published-slice replay covers {families} slice/family entries. It sees {seen} rows, admits {admitted} and refuses {refused}, with every refusal counted and explained (`work/build4/FINAL_AUDIT.json`, `work/build4/rows_final_source/RESULTS.json`). Synthetic frame pins and published metadata stand in; this is not a full RGB-store census. Required grammar and merged-list pins match byte for byte (`work/build4/FINAL_AUDIT.json`).

All {mutations} review row mutations refuse on the exact final source (`work/build4/review_current/MUTATIONS.json`, `SOURCE.json`). The bank probes refuse (`work/build4/review_current/PROBE_BANK.json`). Applicable statement mutations are killed; final grammar mutations were rechecked (`work/build4/mutation_final/RESULTS.json`, `work/build4/mutation_current_grammar/RESULTS.json`).

Changed-statement coverage records {executed} of {changed} statements. The remaining {unexecuted} are conservatively CPU-reachable unresolved (`work/build4/CHANGED_COVERAGE.json`). This fails the requested zero-gap criterion.

Outstanding blockers: actual runtime/archive staging; complete full-state persistence and disk-budget qualification; missing vocabulary witness and real sealed bank membership; full-store sampler reindexing after late refusals; complete package pass; remaining CPU coverage. The report distinguishes implemented guards from unproved production behavior.

Completed temporary proof products are retained by rename with artifact-location indexes. Final storage is recorded in `work/build4/FINAL_STORAGE.json`. No automatic continuation or production action is pending.
'''.format(tests=audit['final_package_delta_tests'],families=audit['row_families'],
           mutations=audit['review_mutations'],executed=coverage['executed'],
           changed=coverage['changed_statements'],unexecuted=coverage['unexecuted'],
           **audit['row_totals'])
(L/'work/build4/STATUS.md').write_text(text)
