"""First-review failing inputs rerun on r4: HIGH-1 nadir flow, MEDIUM-5 point ground, HIGH-2 subclassing, MEDIUM-4 binding precedence."""
import sys, json
TREE = sys.argv[1]
sys.path[:0] = [TREE, TREE+'/generator/derivgen_v7', TREE+'/generator/ground_rows_out', '/scratch/jjyeung/orch_n30/review_contracts2/work/rr/work/tests_r4']
from pathlib import Path
from fixtures_contracts import fixture, session, response, CALLS
from trace_format.contracts import contract_epoch, response_status
from student_pilot.training_contract import audit_training_contract
out = {}
root = Path('/scratch/jjyeung/orch_n30/review_contracts2/work/tmp/nadir_flow')
c, make = fixture('nadir_positive')
with contract_epoch(True):
    s = session(make(), root/'on')
    r = {call: response(s, call) for call in CALLS}
out['nadir_responses'] = r
w = lambda t: '<tool_response>\n' + t + '\n</tool_response>'
row = dict(qid='x', question='What is the distance between the chair and the table (in meters)?', options=[],
           candidate_phrases=['chair', 'table'], trace_revision='3.14',
           events=[dict(call=CALLS[0], response=w(r[CALLS[0]])), dict(call=CALLS[1], response=w(r[CALLS[1]])), dict(call=CALLS[2], response=w(r[CALLS[2]]))],
           target='<think>\n...\n</think>\n<answer>1.2</answer>')
with contract_epoch(True):
    out['HIGH1_ground_ground_gap'] = audit_training_contract([row])
    out['HIGH1_first_review_literal'] = audit_training_contract([dict(row, events=[dict(call=CALLS[0], response=w('chair: heading unavailable\nsize 0.43 x 0.06 x 0.86 m')), dict(call=CALLS[1], response=w('table: heading unavailable\nsize 0.43 x 0.06 x 0.86 m')), dict(call=CALLS[2], response=w('distance 0.90 m'))])])
    # M6 core rule: after a true failure, a gap must defer
    out['M6_gap_after_failed'] = audit_training_contract([dict(row, events=[dict(call=CALLS[0], response=w('chair: not seen')), dict(call=CALLS[2], response=w('distance 0.90 m'))])])
    # MEDIUM-5
    pg = dict(qid='y', question='What is the distance between the chair and the table and lamp?', options=[], candidate_phrases=['chair','table','lamp'], trace_revision='3.14',
              events=[dict(call='<ground obj="chair">', response=w('chair: frames 2,3 (best 2)\nP1: cam2 (-0.64, -0.05, 2.05) m; f1 (-0.63, -0.05, 2.07) m; spread 0.00\nsize unavailable')),
                      dict(call='<ground obj="table">', response=w('table: frames 2,3 (best 2)\nP2: cam2 (0.66, -0.06, 2.13) m; f1 (0.65, -0.06, 2.15) m; spread 0.00\nsize 0.43 x 0.02 x 0.89 m')),
                      dict(call='<ground obj="lamp">', response=w('lamp: frames 2,3 (best 2)\nP3: cam2 (0.10, -0.06, 2.13) m; f1 (0.12, -0.06, 2.15) m; spread 0.00\nsize 0.43 x 0.02 x 0.89 m'))],
              target='<think>\n...\n</think>\n<answer>A</answer>')
    out['MEDIUM5_point_size_unavailable'] = audit_training_contract([pg])
    out['MEDIUM5_status'] = response_status(pg['events'][0]['response'])
    # partial-heading point ground with size unavailable
    pg2 = dict(pg); pg2['events'] = [dict(call='<ground obj="chair">', response=w('chair: frames 2,3 (best 2)\nP1: cam2 (-0.64, -0.05, 2.05) m; f1 (heading unavailable, -0.05, heading unavailable) m; spread 0.00\nsize unavailable'))] + pg['events'][1:]
    out['MEDIUM5_partial_point_size_unavailable'] = audit_training_contract([pg2])
    # MEDIUM-4 precedence: candidate_phrases vs candidate_manifest on the same row
    both = dict(row, uses_mask_cache=True, candidate_phrases=['chair','table'], candidate_manifest=['chair','table','lamp'],
                events=[dict(call='<ground obj="lamp" mode="box">', response=w('lamp: frames 2,3 (best 2)\nB1: f1 centre (0.1, 0.0, 2.0) m\nsize 0.4 x 0.4 x 0.4 m\nyaw 0 deg (0 = +x; positive +x toward -z about +y)'))])
    out['MEDIUM4_admission_both_fields'] = audit_training_contract([both])
    out['MEDIUM4_admission_phrases_only'] = audit_training_contract([dict(both, candidate_manifest=None)])
# HIGH-2 subclassing with the flag on and off
import types, numpy as np
from types import SimpleNamespace as NS
from fixtures_contracts import masks
for epoch in (False, True):
    with contract_epoch(epoch):
        import render_gaps_v314 as gaps
        from derivgen import ground_v313 as I, box_v313 as B
        geo = fixture('landscape')[1](); geo.ids = np.array([1,2]); geo.labels = ['chair','table']
        geo.inst = np.zeros((32,24,32), int)
        for iid, name in zip(geo.ids, geo.labels): geo.inst[masks(name).masks] = iid
        clip = NS(geo=geo, masks=lambda n:(masks(n).masks, np.ones(32)), programs=NS(T=NS(match_labels=lambda n, l:[x for x in l if x==n])))
        res = {}
        try:
            p = gaps.instance_provider(clip); res['instance_provider'] = [type(p).__name__, isinstance(p, I.GTInstances), [k.__module__+'.'+k.__qualname__ for k in type(p).__mro__][:5]]
        except Exception as e: res['instance_provider'] = ['ERR', type(e).__name__, str(e)[:200]]
        class MyReg(B.BoxRegistry):
            def mine(self): return 'override-ok'
        try:
            m = MyReg(); res['subclass_boxregistry'] = [m.mine(), isinstance(m, B.BoxRegistry), type(m).__mro__[2].__module__]
        except Exception as e: res['subclass_boxregistry'] = ['ERR', str(e)[:200]]
        class MyFused(B.FusedBoxProvider):
            provider_id = 'mine'
        try:
            f = MyFused(); res['subclass_provider_id_override'] = f.provider_id
        except Exception as e: res['subclass_provider_id_override'] = ['ERR', str(e)[:200]]
        res['issubclass_runtime_instance'] = isinstance(__import__('trace_format.box_v313', fromlist=['x']).FusedBoxProvider(), B.FusedBoxProvider)
        out[f'HIGH2_epoch_{epoch}'] = res
print(json.dumps(out, indent=1, default=str)[:6000])
json.dump(out, open(sys.argv[2], 'w'), indent=1, default=str)
