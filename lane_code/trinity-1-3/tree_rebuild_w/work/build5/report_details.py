"""Retain trace-supported cause notes without changing packaged comparison code."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
value=json.loads((L/'work/build5/SUITE_COMPARISON.json').read_text())
notes=[]
for row in value['failures']:
    if not row['cause'].startswith('unclassified:'):continue
    error=row['base_error']
    if 'Operation not permitted' in error and '_socket.socket.__init__' in error:
        cause='sandbox refuses socket creation before the distributed fixture can start'
    elif "self.assertTrue(all(r['finite'] for r in records))" in error:
        cause='legacy first-batch fixture expects failed-row substitution, but native final-mode fetch refuses it'
    else:raise ValueError('A cause still requires inspection: '+row['test'])
    notes.append(dict(test=row['test'],original_cause=row['cause'],cause=cause,
                      source='work/build5/SUITE_COMPARISON.json',base_traceback=error,
                      implementation='work/base/tree_b01ce449/student_pilot/carrier_c1_run.py:1279'
                      if "all(r['finite']" in error else 'socket creation site in the recorded base traceback'))
sizes=[]
for variant in ('tree','base'):
    path='work/build5/proofs/suite_'+variant+'/temporary_sizes.json'
    rows=json.loads((L/path).read_text())
    maximum=max(rows,key=lambda row:max(row['before_bytes'],row['after_bytes']))
    sizes.append(dict(variant=variant,source=path,maximum=maximum,
                      above_cap=[row for row in rows if max(row['before_bytes'],row['after_bytes'])>200_000_000]))
record=dict(cause_notes=notes,temporary_sizes=sizes)
(L/'work/build5/REPORT_DETAILS.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(cause_notes=len(notes),temporary_sizes=[dict(variant=r['variant'],
    maximum_bytes=max(r['maximum']['before_bytes'],r['maximum']['after_bytes']),above_cap=len(r['above_cap'])) for r in sizes])))
