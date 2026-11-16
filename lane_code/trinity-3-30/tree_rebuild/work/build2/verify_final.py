"""Check delivery identities and retain source snapshots outside the final kit folder."""
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]; O=L/'out'
read=lambda path:json.loads(path.read_text())
required=['BUILD2_REPORT.md','COMPONENT_POLICY.md','RECORDS_TO_REGENERATE.md','MIX_A0.json','MIX_A0.md',
          'GRAMMAR_DIVERGENCE.md','TREE.diff','TREE_FILES.sha256','TREE_SEAL.json',
          'DESIGN_RECORD_tree_rebuild_20261115.md','B2_COVERAGE_CLASSIFIED.json','B2_KITS.json']
for name in required:
    if not (O/name).is_file() or not (O/name).stat().st_size: raise ValueError('Missing delivery: '+name)
seal=read(O/'TREE_SEAL.json')['tree_sha256']; kits=read(O/'B2_KITS.json')
for kit in kits:
    root=L/kit['kit_path']
    if kit['source_sha256']!=seal or read(root/'BUILD.json')['source_sha256']!=seal:
        raise ValueError('Kit/tree seal differs')
    if hashlib.sha256((root/'SHA256SUMS.txt').read_bytes()).hexdigest()!=kit['kit_sha256']:
        raise ValueError('Kit inventory identity differs')
if (L/'work/tree_r1/student_pilot/trace_grammar.py').read_bytes()!=(L/'work/shared/trace_grammar.py').read_bytes():
    raise ValueError('Shared grammar bytes differ')
for prefix in ['B2_FINAL_','B2_CLOSING_','B2_INTEGRATION_','B2_CONFIG_','B2_FALLBACK_']:
    result=read(O/(prefix+'TEST_RESULTS.json'))
    if result['failures'] or result['errors']: raise ValueError('Failing delivery proof')
cov=read(O/'B2_COVERAGE_CLASSIFIED.json')
if not cov['strict_cpu_gate']: raise ValueError('Uncovered CPU statement remains')
if (O/'DESIGN_RECORD_tree_rebuild_20261115.md').read_text().count('\n## Build 2\n')!=1:
    raise ValueError('Design record section is not unique')
snapshots=L/'work/build2/snapshots'; snapshots.mkdir(exist_ok=True)
for name in ('a0a0a0a0','a2a2a2a2'):
    original=L/'work/build2/kits'/name
    if original.exists(): original.rename(snapshots/name)
path=O/'B2_COVERAGE_REMAP.json'
value=path.read_text()
for name in ('a0a0a0a0','a2a2a2a2'):
    value=value.replace('work/build2/kits/'+name,'work/build2/snapshots/'+name)
path.write_text(value)
size=lambda root:sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
tmp_bytes=size(L/'work/tmp');lane_bytes=size(L)
if tmp_bytes>200000000 or lane_bytes>2000000000:raise ValueError('Storage bound exceeded')
summary=dict(status='INSPECTION_ONLY',tree_sha256=seal,tmp_bytes=tmp_bytes,lane_bytes=lane_bytes,
             strict_cpu_gate=cov['strict_cpu_gate'],kits=[k['kit_path'] for k in kits],
             source='out/B2_KITS.json; out/B2_COVERAGE_CLASSIFIED.json; final filesystem metadata')
(O/'B2_DELIVERY_CHECK.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
