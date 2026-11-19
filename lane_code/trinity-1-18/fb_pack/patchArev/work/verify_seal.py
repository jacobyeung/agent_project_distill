"""Compute the kit seal of work/base and work/new and compare with the sealed file list."""
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parent
EXPECTED = '57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
sys.path.insert(0, str(W / 'base'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

listed = {n: v for v, n in (l.split('  ', 1) for l in (W / 'TREE_FILES.sha256').read_text().splitlines())}
out = {'listed_files': len(listed), 'listed_digest': digest(listed)}
for name in ('base', 'new'):
    inv = inventory(W / name)
    out[name] = dict(files=len(inv), digest=digest(inv), seal_ok=digest(inv) == EXPECTED,
                     differs=sorted(p for p in set(inv) | set(listed) if inv.get(p) != listed.get(p)))
print(json.dumps(out, indent=1))
