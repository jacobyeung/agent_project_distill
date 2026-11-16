"""Count supplied frame metadata forms without retaining row bodies."""
from collections import Counter
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
root = L / 'work/rows_slices/slices_final'
counts = json.loads((root / 'COUNTS_A0_v4.json').read_text())
result = []
for family, spec in counts['families'].items():
    forms = Counter()
    path = root / spec['slice_file']
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            assert number <= 2000
            row = json.loads(line)
            form = tuple((key, len(value) if isinstance(value, list) else type(value).__name__)
                         for key, value in [
                             ('frame_indices', row.get('frame_indices')),
                             ('ground_record.frame_indices', row.get('ground_record', {}).get('frame_indices')),
                             ('student_input.frames', row.get('student_input', {}).get('frames'))])
            forms[form] += 1
    result.append(dict(family=family, source=str(path.relative_to(L)),
                       forms=[dict(fields=list(key), rows=n) for key, n in forms.items()]))
(L / 'work/build6/ROW_FRAME_METADATA.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
