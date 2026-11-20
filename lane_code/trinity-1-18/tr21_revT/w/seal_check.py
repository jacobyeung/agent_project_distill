import sys, json
from pathlib import Path
for t in sys.argv[1:]:
    T = Path(t).resolve()
    sys.path.insert(0, str(T))
    for m in [k for k in sys.modules if k.startswith('student_pilot')]:
        del sys.modules[m]
    from student_pilot.source_seal import inventory
    from student_pilot.p3_provenance import digest
    files = inventory(T)
    print(t, digest(files), len(files))
    Path(t + '.files.sha256').write_text(''.join(h + '  ' + n + '\n' for n, h in sorted(files.items())))
    sys.path.remove(str(T))
