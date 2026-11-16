"""Validate evidence coverage and required positive controls; defects stay defects."""
import ast,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
comparison=json.loads((W/'comparison.json').read_text());families={r['family']:r for r in comparison['families']}
binding_source=L/'work/base/work/base/tree_b01ce449/generator/derivgen_v7/derivgen/bindings.py'
constants={}
for node in ast.parse(binding_source.read_text()).body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('FAMILIES','F17'):
        constants[node.targets[0].id]=ast.literal_eval(node.value)
expected=constants['FAMILIES']|constants['F17']
checks=[]
def check(name,ok,source,detail=None):checks.append(dict(name=name,passed=bool(ok),source_path=str(source),detail=detail))
check('native_semantic_family_enumeration',all('point_program/'+t in families for t in expected),binding_source,sorted(expected))
check('native_semantic_families_render_in_all_arms',all(all(families['point_program/'+t]['rows_per_arm'][arm]>=3 for arm in ('base','off','on')) for t in expected),W/'comparison.json')
check('every_on_row_audited',all(all(s['audit'] is not None for s in r['samples'] if s['statuses']['on']=='rendered') for r in families.values()),W/'comparison.json')
check('served_near_nadir_fused_distance_admitted',comparison['summary']['near_nadir_distance_admitted'],W/'comparison.json')
annotation=families['production_annotation/object_abs_distance']
check('served_near_nadir_annotation_distance_admitted',all(s['audit'] and s['audit']['verdict']=='admitted' for s in annotation['samples'] if s['variant'].startswith('nadir_positive')),W/'comparison.json')
check('off_failure_retained',not comparison['summary']['off_parity'],W/'comparison.json')
check('all_on_deltas_mapped_or_reported',all(d['contract_change'] is not None or any(e.get('family')==r['family'] and e.get('variant')==s['variant'] and e.get('path')==d['path'] for e in comparison['defects']) for r in families.values() for s in r['samples'] for d in s['differences']),W/'comparison.json')
repro=json.loads((W/'off_parity_reproduction.json').read_text())
check('minimal_reproduction_is_base_success_off_error',repro['arms']['base']['status']=='rendered' and repro['arms']['off']['status']=='error' and 'heading_defined' in repro['arms']['off']['error'],W/'off_parity_reproduction.json')
artifacts=[]
for arm in ('base','off','on'):
    for name in (f'{arm}.json',f'supplement_{arm}.json',f'keypoints_{arm}.json'):
        p=W/name;artifacts.append(dict(source_path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
out=dict(all_evidence_checks_pass=all(c['passed'] for c in checks),checks=checks,artifacts=artifacts,source_path=__file__)
(W/'validation.json').write_text(json.dumps(out,indent=2))
print(json.dumps(dict(all_evidence_checks_pass=out['all_evidence_checks_pass'],checks=checks)))
assert out['all_evidence_checks_pass'],'Evidence validation failed; inspect validation.json'
