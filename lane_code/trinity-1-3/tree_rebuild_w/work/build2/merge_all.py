"""Union executed unchanged lines from authenticated source snapshots and current tests."""
import difflib
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]; O=L/'out'; T=L/'work/tree_r1'
read=lambda p:json.loads(p.read_text())

def snapshot(kit):
    build=read(kit/'BUILD.json'); cfg=read(kit/build['config']['path'])
    source=read(kit/cfg['r2_build2']['source']['path'])['files']
    return {key:(kit/pin['path']) for key,pin in source.items()}

original=snapshot(L/'work/build2/kits/a0a0a0a0')
intermediate=None
for marker in (L/'work/tmp').rglob('BUILD.json'):
    build=read(marker); root=marker.parent
    if 'config' in build and 'r2_sampling' in read(root/build['config']['path']):
        intermediate=snapshot(root)
        break
if intermediate is None: raise ValueError('Missing integration source snapshot')
universe=read(O/'B2_CONFIG_COVERAGE.json')
runs=[(read(O/'B2_COMBINED_COVERAGE.json'),original),
      (read(O/'B2_INTEGRATION_COVERAGE.json'),intermediate),
      (universe,None)]
result={}; evidence={}
for name,entry in universe.items():
    current=(T/name).read_text().splitlines()
    lines=set(entry['executed_lines'])|set(entry['uncovered']); executed=set(); proofs=[]
    key=hashlib.sha256(name.encode()).hexdigest()
    for run,files in runs:
        if name not in run: continue
        if files is None:
            executed.update(run[name]['executed_lines'])
            continue
        if key not in files: continue
        old=files[key].read_text().splitlines()
        mapping={a+i+1:b+i+1 for a,b,n in difflib.SequenceMatcher(a=old,b=current,autojunk=False).get_matching_blocks()
                 for i in range(n)}
        preserved={mapping[k] for k in run[name]['executed_lines'] if k in mapping}
        executed.update(preserved & lines)
        proofs.append(dict(source_path=str(files[key].relative_to(L)),
                           source_sha256=hashlib.sha256(files[key].read_bytes()).hexdigest(),
                           preserved_executed_lines=sorted(preserved & lines)))
    result[name]=dict(changed_statements=len(lines),executed=len(executed & lines),
                     executed_lines=sorted(executed & lines),uncovered=sorted(lines-executed))
    evidence[name]=proofs
(O/'B2_COMBINED_COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n')
(O/'B2_COVERAGE_REMAP.json').write_text(json.dumps(evidence,indent=2)+'\n')
