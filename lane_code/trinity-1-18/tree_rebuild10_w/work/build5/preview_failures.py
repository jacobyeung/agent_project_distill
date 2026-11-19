"""Identify final legacy failures absent from the diagnostic base replay."""
import json
from pathlib import Path
import re
L=Path(__file__).resolve().parents[2]
def read(name):return json.loads((L/name).read_text())
tree=read('work/build5/proofs/suite_tree/legacy/results.json')
base=read('work/build5/proofs/legacy_base/results.json')
def key(name):return re.sub(r"(['\"])[^'\"]*/work/tmp/[^'\"]*\1", "'<temporary path>'",name)
prior={key(name) for name,error in base['failures']+base['errors']}
rows=[dict(test=name,error=error) for name,error in tree['failures']+tree['errors'] if key(name) not in prior]
value=dict(note='Diagnostic only; the final same-package base replay is authoritative.',
           passed=len(tree['passed']),skipped=len(tree['skips']),unmatched=rows)
(L/'work/build5/FINAL_LEGACY_PREVIEW.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(passed=value['passed'],skipped=value['skipped'],unmatched=len(rows))))
for row in rows:print(row['test'],row['error'][-2400:])
