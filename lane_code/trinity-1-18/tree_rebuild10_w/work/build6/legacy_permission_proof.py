"""Name the failing operation in base-matched sandbox exceptions."""
import json
from pathlib import Path

B = Path(__file__).resolve().parent
source = 'work/build6/SUITE_COMPARISON.json'
value = json.loads((B / 'SUITE_COMPARISON.json').read_text())
rows = []
for row in value['failures']:
    if not row['preexisting'] or row['cause'] != 'unclassified: PermissionError: [Errno 1] Operation not permitted':
        continue
    traces = [row['tree_error'], row['base_error']]
    sockets = all('_socket.socket.__init__(' in trace for trace in traces)
    rows.append(dict(test=row['test'], source=source, socket_constructor_in_both=sockets,
                     cause=('Sandbox refuses the legacy socket-construction fixture.' if sockets
                            else 'Operation not permitted; inspect retained tracebacks for the exact operation.'),
                     tree_error=row['tree_error'], base_error=row['base_error']))
(B / 'LEGACY_PERMISSION.json').write_text(json.dumps(rows, indent=2) + '\n')
for row in rows:
    print(json.dumps({k: v for k, v in row.items() if not k.endswith('_error')}))
