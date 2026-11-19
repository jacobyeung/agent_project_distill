from pathlib import Path
import json,sys,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24';B=L/'work/build22'
sys.path[:0]=[str(D),os.environ.get('R2_TREE',str(L/'work/tree_r1')),str(L/'work/build21')]
import joblib as J
from student_pilot.r1_coverage import deferred,validate_binding,source_names
from student_pilot.r1_persisted import scope
from student_pilot.r1_handover import pin_values
cfg=J.load(D/'kits/q/k/n.json');prior=J.load(B/'kits/q/k/n.json')
for field in ('remove_files','scene_division','exclusions','benchmark_scene_exclusions','dev_scene_exclusions'):
    assert cfg[field]==prior[field],field
for field in ('direction_twins','v7_k1_removal','v7_k1_union','wording_exclusion','camera_wording_exclusion','launch22'):
    assert cfg['r1_training'][field]==prior['r1_training'][field],field
assert cfg['streams']['vqa']==prior['streams']['vqa']
paths={x['sha256']:x['local_path'] for x in J.load(D/'UPLOADS_q.json')['files']}
with scope(paths):
    assert deferred(cfg)
    validate_binding(cfg)
    assert source_names(J.load(cfg['r1_training']['row_sources']['path']),cfg)==()
card=J.load(D/'inputs/mix.json');zero={c['type']:0 for c in card['cells'] if c['stream']=='routing' and c['type']!='routing_base'}
assert all(c['rows_per_step']==0 for c in card['cells'] if c['type'] in zero)
rows=J.load(B/'REMOVAL_CENSUS.json');native=J.load(B/'proofs/census/CENSUS.json');aug=J.load(B/'AUGMENTED_CENSUS.json')
print('Native census fields:',list(native))
families=rows['families']
for name,value in families.items():
    value['new_removals']=value.get('newly_removed',0)
    value['eligible']=value['after']+(7971 if name=='direction' else 0)
# Six relative-distance rows fail the unchanged native reader beyond list filtering.
assert native['vqa']['eligible_by_cell']['relative_distance']==19827
for name,count in native['vqa']['eligible_by_cell'].items():
    if name in families:families[name]['eligible']=count
base=J.load(paths[cfg['streams']['routing']['sha256']])
result=dict(schema='build24-minimal-census-v1',GO=False,VQA=families,
    evidence={str(p.relative_to(L)):J.sha(p) for p in (B/'REMOVAL_CENSUS.json',B/'LIST_CENSUS.json',B/'AUGMENTED_CENSUS.json',B/'proofs/census/CENSUS.json')},
    method='The authenticated build-22 VQA census applies unchanged: store, twins, every removal, exclusions and reader implementation are identical. Only routing selection changes.',
    routing=dict(receipt=cfg['streams']['routing'],database=base['database'],rows=base['count'],types=base.get('types'),
        source='P pinned runtime config and regenerated S1 base; production database not available here'),
    deferred_cells=zero,heldout_wording_hits=native['heldout_wording_hits'],K1_unremoved=aug['unremoved_hits'],room_rule_hits=aug['source_r0'],
    twin_room_mismatch=aug['twin_room_mismatch'],named_removal_matches=rows['matched'],twin_rows=aug['twin_rows'],
    limitations=['P base receipt is authenticated; the production routing database was not rescanned.','Production pose and pointing counts are inherited.','The native host must materialize and certify the augmented VQA database.'])
assert result['heldout_wording_hits']==result['K1_unremoved']==result['room_rule_hits']==result['twin_room_mismatch']==0
J.write(D/'CENSUS.json',result)
print('PASS VQA census identity and MINIMAL routing:',base['count'],zero)
