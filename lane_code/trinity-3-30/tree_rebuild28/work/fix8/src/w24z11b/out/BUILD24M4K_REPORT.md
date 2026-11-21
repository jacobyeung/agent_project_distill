CASE b — P_EXPORT_CONFIG_DIFFERENCE:max_pixels; patch out/TREE_CHANGE_24M4K.patch is not applied.
All eight real N configs pass the original handover comparison; explicit 16384/147456 pixels make all eight fail it. frame_count was already 32.
The proposal restores P's default processor path and fixes the separate admission layout call; three portable tests and synthetic duplicate-frame encoding pass.
PROCESSOR_TRACE_24M4K.md gives file:line paths through r, q and every training rank; TREE_CHANGE_NEEDED_24M4K.md states the review requirement and test limits.
Tree C remains 0c7614c8; kits remain q 72bf8930, n 1015612f, n_go dbc52f31 and qd 259c14de. GO remains false except the existing kit_n_go.
rcj supports b (P-only, default) and r (native a.py/pl.py/rb.py/rg.py); both launch fixes remain, with preempt/16 CPUs/128 GB/2 h/no GPU/no requeue.
Mode r stages the native planner's pins and runtime assets; it excludes RGB payloads but retains the required export weights. The local planner test documents unavailable-payload stubs.
The outside EXIT publisher independently emits both database identities, native artifacts, bounded gated samples and rdiff outputs/timings; SQLite databases stay job-local.
All 16 existing scan/kit/naming/resolver/guard/arming suites pass, as do new config, patch, planning, transport, mount, publication, sample and comparison fixtures.
UPLOADS_24M4K.json/.list contain only the two rcj helpers against Orchard's current baseline; the GO delta is empty. No upload or job ran.
Tests used a read-only host, only this workspace writable, isolated Python and bounded CPU resources; no superseded workspace imports, SSH, network, Git, GPU or other agents ran.
Full admission, production rows, the production database rebuild and Orchard execution were not tested; the current kits still refuse N until ORCH approves a tree change and review.
work/build24m4k/VALIDATION.json and FAILURES.json record local evidence; DELIVERY_24M4K.json and PACKAGE_CHECK.json identify and verify the full archive.
