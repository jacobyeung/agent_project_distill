"""Remap executed statements through unchanged source lines, then union new proofs."""
import difflib
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]; O=L/'out'; T=L/'work/tree_r1'
old_kit=L/'work/build2/kits/a0a0a0a0'
read=lambda p:json.loads(p.read_text())
build=read(old_kit/'BUILD.json')
cfg=read(old_kit/build['config']['path'])
source=read(old_kit/cfg['r2_build2']['source']['path'])['files']
old=read(O/'B2_COMBINED_COVERAGE.json')
new=read(O/'B2_INTEGRATION_COVERAGE.json')
results={}; evidence={}
for name,entry in new.items():
    executed=set(entry['executed_lines'])
    universe=executed|set(entry['uncovered'])
    key=hashlib.sha256(name.encode()).hexdigest()
    if name in old and key in source:
        before=(old_kit/source[key]['path']).read_text().splitlines()
        after=(T/name).read_text().splitlines()
        mapping={a+i+1:b+i+1 for a,b,n in difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_matching_blocks()
                 for i in range(n)}
        preserved={mapping[line] for line in old[name]['executed_lines'] if line in mapping}
        executed.update(preserved & universe)
        evidence[name]=dict(old_source_sha256=source[key]['sha256'],
                            current_sha256=hashlib.sha256((T/name).read_bytes()).hexdigest(),
                            preserved_executed_lines=sorted(preserved & universe))
    results[name]=dict(changed_statements=len(universe),executed=len(executed),
                       executed_lines=sorted(executed),uncovered=sorted(universe-executed))
(O/'B2_COMBINED_COVERAGE.json').write_text(json.dumps(results,indent=2)+'\n')
(O/'B2_COVERAGE_REMAP.json').write_text(json.dumps(evidence,indent=2)+'\n')
