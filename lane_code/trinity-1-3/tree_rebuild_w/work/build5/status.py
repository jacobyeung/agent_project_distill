"""Keep the live status focused on measured outcomes and pending work."""
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
phase=sys.argv[1]
text='''# Build 5 status

PHASE

The targeted CPU repair proof passed in `work/build5/proofs/new/results.json`. It covers bounded late frame refusals and reader indices, exact registered sampler metadata, twin grouping, archive-space refusal, native map joins and each checklist step's byte-boundary behavior. The actual full store and real frame-host bytes remain unqualified.

Current changed-statement coverage is in `work/build5/CHANGED_COVERAGE.json`. Executions require a matching current file digest and compiled-code fingerprint. Each external-input classification names its missing input. Locally reachable gaps remain in `work/build5/GAPS.json` until covered by current-source tests.

The final package suite, same-case legacy/base comparison, final empty-kit staging, artifact seal and delivery report remain pending. `work/build5/EXPLORATORY.json` records the incomplete exploratory run; it is not qualification evidence.

The harness measures temporary bytes before and after every test, preserves package members, and overwrites completed owned scratch products in place with hash receipts. It restores imports between tests and modules. Generator, legacy and R2/shared groups use separate interpreters and identical guards. No forbidden child process or network operation inside a test is permitted.

The frame-host checklist is `out/FRAME_HOST_JOB.md`. Both delivered authorizations will remain closed. No launch, remote call, GPU work, real checkpoint/frame copy or full-store materialization has occurred.
'''.replace('PHASE',phase)
(L/'work/build5/STATUS.md').write_text(text)
