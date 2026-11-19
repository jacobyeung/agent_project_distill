from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import re
import sys

L = Path(__file__).resolve().parent.parent
base = Path(json.loads((L / 'work/BASE.json').read_text())['root'])
sys.path.insert(0, str(base))
from student_pilot.p3_provenance import source_files

entries = [base / 'student_pilot' / name for name in ('s1_admission.py', 'carrier_c1_run.py')]
closure = source_files(entries)
fields = []
sites = []
pins = {}
patterns = re.compile(r'\b(pinned|load|open|safe_open|connect|from_pretrained|sha256|file_pin)\(|environ|getenv|^def |^class ')
for path in closure:
    name = str(path.relative_to(base))
    raw = path.read_bytes()
    pins[name] = hashlib.sha256(raw).hexdigest()
    source = raw.decode()
    for number, line in enumerate(source.splitlines(), 1):
        if patterns.search(line):
            sites.append(f'{name}:{number}: {line.strip()}')
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in ('cfg', 'config', 'settings'):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                fields.append(dict(file=name, line=node.lineno, operation='subscript', field=node.slice.value))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            value = node.func.value
            if isinstance(value, ast.Name) and value.id in ('cfg', 'config', 'settings'):
                field = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
                fields.append(dict(file=name, line=node.lineno, operation=node.func.attr, field=field))
fields.sort(key=lambda r: (r['file'], r['line']))
out = L / 'out/evidence'
(out / 'config_reads.json').write_text(json.dumps(dict(
    scope='Conservative static import closure; includes training-only and optional branches. Not an exact runtime read set.',
    sites=fields), indent=2) + '\n')
(out / 'read_sites.txt').write_text('Conservative static source closure, not an execution trace.\n' + '\n'.join(sites) + '\n')
(out / 'native_source_pins.json').write_text(json.dumps(pins, indent=2, sort_keys=True) + '\n')
logs = {
    '172660': (Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/r1_ops6/work/mon/last.txt'), 229, 230),
    '171377': (Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look1.out'), 346, 347),
}
timing = {}
for job, (path, start_line, end_line) in logs.items():
    lines = path.read_text().splitlines()
    start, end = [datetime.datetime.fromisoformat(lines[n - 1].split(' | ')[0].replace('Z', '+00:00')) for n in (start_line, end_line)]
    seconds = (end - start).total_seconds()
    timing[job] = dict(evidence='measured log envelope', file=str(path), start_line=start_line,
                      end_line=end_line, start=lines[start_line-1], end=lines[end_line-1],
                      seconds=seconds, minutes=seconds/60)
(out / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n')
print(json.dumps({'static_source_files': len(pins), 'config_access_sites': len(fields), 'read_sites': len(sites), 'timing': timing}, indent=2))
