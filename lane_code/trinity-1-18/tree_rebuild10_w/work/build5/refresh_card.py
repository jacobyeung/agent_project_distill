"""Refresh the prelaunch card from final qualification receipts."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
def read(name):return json.loads((L/name).read_text())
suite=read('work/build5/SUITE_COMPARISON.json')
coverage=read('work/build5/CHANGED_COVERAGE.json')
delivery=read('work/build5/DELIVERY.json')
kits=read('work/build5/kits/RESULTS.json')
assert suite['regressions']==suite['r2_failures']==suite['shared_grammar_failures']==0
assert coverage['classes'].get('CPU-reachable unresolved',0)==0
assert not suite['fatal']
for variant in ('tree','base'):assert read('work/build5/proofs/suite_'+variant+'/results.json')['complete']
path=L/'out/PRELAUNCH_CARD.md'
body=path.read_text().split('\n## Build 5 qualification\n',1)[0]
body=body.replace('Current qualification is tracked in `work/build5/STATUS.md`.',
                  'The packaged CPU qualification is complete; actual frame-host inputs remain unqualified. Evidence: `out/BUILD5_REPORT.md`.')
section=['','## Build 5 qualification','',
 f"The package suite ran {suite['run']} tests: {suite['passed']} passed; {suite['preexisting']} failure events reproduce on the untouched base. Remaining tree-only regressions, R2/shared failure events and CPU-reachable coverage gaps are zero. Sources: `work/build5/SUITE_COMPARISON.json`, `work/build5/CHANGED_COVERAGE.json`.",'',
 f"Package: `{delivery['path']}`. SHA256: `{delivery['sha256']}`. Tree seal: `{delivery['source_revision']}`. Source: `work/build5/DELIVERY.json`.",'',
 '| Kit | Seal | Authorization |','|---|---|---|']
for kit in kits:section.append(f"| `{kit['kit_path']}` | `{kit['kit_sha256']}` | Closed |")
section+=['','Source: `work/build5/kits/RESULTS.json`. Both kits were staged from empty and passed the visible-string scanner.','',
 'The real runtime, parent archives, frame map, bank catalog, staged export vocabulary, remote round trip, full trainer-state recovery and native runtime-output scan still require frame-host evidence. The mandatory receipts and refusal conditions are listed in `out/FRAME_HOST_JOB.md`. No launch is authorized.']
path.write_text(body.rstrip()+'\n'+'\n'.join(section)+'\n')
