KIT FIXES COMPLETE; the GO rehearsal is BLOCKED by localhost-socket policy. Production remains NO-GO.
Both q and n exclude post-step-400 checkpoint members. The sealed tree is byte-identical; no upload or submission occurred.
Package: `out/tree_rebuild_b24d_7babb413.tar`; 10881670 bytes; SHA-256 `c28c8215930f83860f2fcf55152ab1c7e70fd2e38d9687d701919c6a347adfd4` (`out/DELIVERY_24D.json`).
Tree: `e1e64652087c2cde689620e4fb6edca57123feccae78c8a0a4b70ce8f7b35c10`. Kit n: `6dc663c3f945a3bef6995169c332e1bbaedfe7b7d07c6067c2db97464bffda48`. Kit q: `a5babe52404d8556e3cb41dbf40d093964a706311d3b6f7907846bbb4ae5720d` (`KIT.json`, `INVARIANTS.json`).

The step-400 resolver selects the export receipt/configuration/model closure, verifies the pinned DONE/e/r/RP and manifest, and authenticates export parts. RP’s checkpoint pointer is provenance only; h.json is not read.
The resolver records the transport archive hash as one object. It never opens, extracts, stages, or adds checkpoint members to required inputs; the pinned manifest still authenticates each selected member.
24c refuses the checkpoint-free archive at step-414 complete.json; 24d resolves it for both kits. Checkpoint injection refuses by name as E83, including every RNG member. Identity functions are unchanged (`RESOLVER_TESTS.json`).
The kit runs the sealed selection producer when P’s selection fingerprint differs. Every other field, including row-index hashes, must remain equal; a changed selection refuses as E86 (`REFRESH_TESTS.json`, `PRODUCTION_SELECTION.json`).
Kit n’s h.py authenticates the ADMIT result and writes its final prepared configuration to `/tmp/q_22c714e1/v.json`, before t.py. That file contains the prepared streams, row plan, handover mapping, persisted pins and fresh-init policy. The canary’s p/q/v.json is a separate opener witness.
Missing-v.json, corrupted pins, non-ADMIT results, wrong policy/world size and GO=false have regression tests (`LAUNCH_TESTS.json`).

| Path/stage | Result | Classification/evidence |
|---|---|---|
| q and n: decoded job.sh; bootstrap; j.sh staging; bwrap | PASS | Writable copies; native helpers; `SEQUENCE.json` |
| q and n: g.py | PASS | Only CUDA queries use fixture values; no GPU |
| q and n: a.py q / i.py | REFUSE | Missing production routing payload a67a3f6f489031d4.jsonl.gz; production-store boundary |
| q and n: d.py, log screeners, o.py | PASS | Native room report on fixture streams and result publication |
| n: h.py/t.py/u.py in the unarmed sequence | NOT REACHED | Shell skips training after the canary refusal |
| GO fixture: a.py q | ADMIT | Native synthetic-store/frame-host fixture; GO_PROGRESS.json records the completed phases |
| GO fixture: room audit | PASS | `GO_TRAIN.json` and its stage log |
| GO fixture: h.py writes v.json | PASS | `GO_TRAIN.json` and its stage log |
| GO fixture: fixture frame-host and review evidence | PASS | `GO_TRAIN.json` and its stage log |
| GO fixture: t.py / u.py / native train | REFUSE | `GO_TRAIN.json` and its stage log |
| u.py standalone preflight | BOUNDARY | Seal, GO, ADMIT400, identity and native admission passed; WORLD_SIZE=0 refuses before distributed startup (`U_PREFLIGHT.json`) |
| Four-rank training | BLOCKED | `GO_RESULT.json`; t.py invoked one torch.distributed.run; sandbox denied localhost TCP sockets (EPERM) before workers started. No optimizer steps ran. |

The CPU fixture uses the tiny native model, synthetic production stores and RGB, and gloo. The native producer’s retained point/VQA stores are reused without copying databases; their pinned readers and twin checks still execute (`boundary.py`).
The GO canary started before the i.py kit update, using an already regenerated native fixture selection. The final i.py no-op path is tested separately. CPU gloo uses native collectives with a 600-second fixture startup timeout.
Fixture setup refusals were a missing S1_REHEARSAL_ATTEMPT and an evidence write outside the writable bwrap mount. The fixture now sets b24d_go and writes evidence inside its mount. Both original logs are retained under `attic/build24d/go_gates_{first,second}/`.
The fixture records host/review refusals before supplying fixture-only gate receipts. Those receipts do not enter either kit and do not authorize production (`GO_GATES.json`).
No distributed worker reached an optimizer. Fresh optimizer state, the counter transition 0 to 2 and finite per-rank training losses remain unverified (`GO_RESULT.json`).
N is configured to start at zero from the step-400 export. Its first scheduled export is local step 100; its hard gate is local step 400. The fixture requests a stop/export at step 2, but no training export was produced (`GO_SETUP.json`, sealed carrier_c1_run.run_steps).
Tests: 83 passed; all 17 guard tests per kit. Decoded scans pass for q, n and the GO variant; changed-statement coverage is in `COVERAGE.json`.
Regeneration is byte-identical and idempotent. Both decoded runs preserve the writable kit file set and hashes (`INVARIANTS.json`, `SEQUENCE.json`).
Upload delta: 13 files, 116262 bytes against MINIMAL + 24B + 24C. Stream root: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24d/upload`; `out/UPLOADS_24D.list` supplies tar member names.
Armed variant: `out/kit_n_go/`, seal `66002d654f64f08c879955feac50cb43f5575050665d16f8121d5a9a6142fecc`. Its separate three-file delta is `out/UPLOADS_24D_GO.json` (a.json, SHA256SUMS.txt, BUILD.json); NOT FOR UPLOAD before the orchestrator’s launch GO.
All deployable normal controls remain GO=false. Production still needs valid host/review receipts for the final prepared configuration; the independent review gate is unchanged.
Production weights, complete production stores and GPU execution were not checked. Receipt hashes, identity semantics, admission, legality, removals, opener rows, step-544 lineage and the DEFERRED boundary retain their checks.
Existing packages are unchanged. Workspace growth: 932366799 bytes, below 1 GB (`DELIVERY.json`). Large generated fixture databases are retained locally and omitted from the overlay.
Evidence paths without a prefix are under `work/build24d/`.
