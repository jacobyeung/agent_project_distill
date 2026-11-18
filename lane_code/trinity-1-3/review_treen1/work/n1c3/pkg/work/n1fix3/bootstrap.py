"""Retain the prior harness and bind the build's read-only evidence."""
import hashlib
import json
import os
from pathlib import Path

L = Path(__file__).resolve().parents[2]
B = L / 'work/n1fix3'
B.mkdir(parents=True, exist_ok=True)
for name in ('test_runner.py', 'compact_tmp.py', 'packet_runner.py', 'packet_final.py',
             'packet_support.py', 'packet_recovery.py', 'PACKET_INPUTS.json', 'compare.py',
             'coverage.py', 'coverage_all.py', 'classify_coverage.py', 'seal.py',
             'make_delivery.py', 'PACKAGE_TEST.sh', 'PACKET_TEST.sh', 'package.py'):
    p = L / 'work/build9' / name
    if p.exists():
        raw = p.read_bytes()
        if name not in ('test_runner.py', 'compact_tmp.py'):
            raw = raw.replace(b'work/build9', b'work/n1fix3').replace(b'tree_rebuild_b9_', b'tree_rebuild_bn1_').replace(b'package9_', b'package_n1_')
        (B / name).write_bytes(raw)
for suite in ('suite_base', 'suite_tree'):
    for group in ('generator', 'legacy', 'r2'):
        src = L / 'work/build9/proofs' / suite / group
        dst = B / 'proofs' / suite / group
        dst.mkdir(parents=True, exist_ok=True)
        for p in src.glob('*.json'):
            (dst / p.name).write_bytes(p.read_bytes())
(B / 'STATUS.md').write_text('# Build n1 status\n\nContracts and build 9 state read. R1 input binding and native training-path audit are in progress. GO=false.\n')
(B / 'DECISIONS.md').write_text('''# Build n1 decisions

- R1 uses the vehicle-N card, S2 off, size zero, no fusion, and GT responses. The card is configuration data; official items and answer statistics are not inputs.
- A v7 receipt and a passing appended-row validator exist. Bind v7 provisionally; complete-store validation, remote availability and full scene coverage remain separate requirements.
- Only bounded real-row slices are read locally. Full-population production counts remain blocked unless authenticated producer evidence proves them; slice counts are never extrapolated.
- Preserve all registry slots. The deployed-policy records remain native-evaluation requirements. A GF-1 connector record is inapplicable only when no connector is configured; this requires explicit launch-scope enforcement.
- Missing evidence remains a named refusal. No unknown scene overlap qualifies as clean.
- A source-only package is permitted under the requested package build. No large input or checkpoint is copied. Suite groups resume only when their exact input hashes match.
- The requested RESULT event is staged locally because this build may write only within the lane. The orchestrator publishes it and requests the single review.
''')
sizes = {}
for label, root in [('lane', L), ('tmp', L/'work/tmp')]:
    total = 0
    pending = [root]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
    sizes[label] = total
(B/'INITIAL_STORAGE.json').write_text(json.dumps(sizes, indent=2)+'\n')
print(json.dumps(sizes))
