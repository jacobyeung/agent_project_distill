import json
import sys
from pathlib import Path
from fixtures_contracts import L
from trace_format.contracts import contract_epoch
from generator_fixture_r4 import generate

def test_production_generator_on_off():
    import student_pilot
    tree=Path(student_pilot.__file__).resolve().parent.parent
    baseline=json.loads((L/'work/generator_baseline_r4.json').read_text())
    outputs={};differences={}
    for kind in ('landscape','nadir_positive'):
        with contract_epoch(False):off=generate(tree,kind)
        assert json.dumps(off,sort_keys=True)==json.dumps(baseline[kind],sort_keys=True)
        with contract_epoch(True):on=generate(tree,kind)
        outputs[kind]=dict(off=off,on=on)
        differences[kind]=[]
        for family in ('count_events','distance_events'):
            for index,(a,b) in enumerate(zip(off[family],on[family],strict=True)):
                assert a['call']==b['call']
                for key in set(a.get('audit',{})) | set(b.get('audit',{})):
                    if a.get('audit',{}).get(key)!=b.get('audit',{}).get(key):
                        assert kind=='nadir_positive' and key in {'metric_only','metric_values','metric_gaps','metric_metadata',
                            'full_precision_box','full_precision_boxes'}
                        differences[kind].append(f'{family}[{index}].audit.{key}')
                if a['response']!=b['response']:
                    assert kind=='nadir_positive' and 'heading unavailable' in b['response']
                    differences[kind].append(f'{family}[{index}].response')
        if kind=='landscape':
            assert on['count']==off['count']
            assert on['distance']==off['distance']
        else:
            assert 'heading unavailable' in on['distance']
            assert '<gap ' in on['distance']
            assert on['distance'].split('<gap ',1)[1]==off['distance'].split('<gap ',1)[1]
            assert 'heading unavailable' in on['count']
    (L/'work/test_artifacts_r4/GENERATOR_PARITY_R4.json').write_text(json.dumps(dict(source=__file__,outputs=outputs,differences=differences,
        allowed_changes=['Partial f1 coordinates and box yaw when reference heading is undefined',
                         'Private box operands use the metric frame when reference heading is unavailable',
                         'Runtime audit includes metric_only and heading metadata for partial boxes']),indent=2))
