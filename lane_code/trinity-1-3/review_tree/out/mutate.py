import json, sys, os, copy, re
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/review_tree/work'); H = W/'h'
sys.path.insert(0, str(W/'stage3/5c2ca33ca02a_t/o/ee000001')); sys.path.insert(0, str(H))
os.environ['STUDENT_R2_LOCAL_NODE'] = '1'
import mk
from student_pilot.r2_intake import intake
from student_pilot.r2_materialize import materialize
OUT = H/'mut'; OUT.mkdir(exist_ok=True)
def rows(p): return [json.loads(l) for l in open(p)]
def first_ok(fam, src):
    adm, _ = intake(H/(src+'_env')/(fam+'.manifest.json'))
    q = adm[0]['row']['qid']
    return next(r for r in rows(H/src/(fam+'.jsonl')) if r['qid'] == q)
def run(name, fam, stream, rowlist):
    d = OUT/name; d.mkdir(exist_ok=True)
    p = d/(fam+'.jsonl')
    with open(p, 'w') as f:
        for r in rowlist: f.write(json.dumps(r)+'\n')
    m = mk.build(fam, p, stream, d)
    try:
        adm, rep = intake(m)
    except Exception as e:
        return dict(mutation=name, admitted=False, refusal='intake raised: '+str(e)[:150])
    return dict(mutation=name, admitted=len(adm) == len(rowlist), n=len(rowlist), admitted_n=len(adm),
                refusal=[r['reason'][:150] for r in rep['refusals']])
res = []
base = first_ok('d0_retrace_object_rel_distance', 'adapted')
q = base['student_input']['question']
# 1 answer-only targets
for tag, tgt in [('answer_only_bare', base['answer']), ('answer_only_empty_think', '<think>\n\n</think>\n\n'+base['answer']),
                 ('answer_only_think_restate', '<think>\nThe answer is '+base['answer']+'.\n</think>\n\n'+base['answer']),
                 ('answer_only_think_filler', '<think>\nLet me look at the video carefully.\n</think>\n\n'+base['answer']),
                 ('answer_only_seen_only', '<think>\nSeen: the stove in frame 3.\n</think>\n\n'+base['answer'])]:
    r = copy.deepcopy(base); r['target'] = tgt; res.append(run(tag, 'd0_retrace_object_rel_distance', 'vqa', [r]))
# 2 stated measurements
body = base['target'].split('</think>')[0]
for tag, line in [('meas_meters', 'The table is 2.5 meters from the sofa.'), ('meas_cm_glued', 'The table is 120cm wide.'),
                  ('meas_words', 'The table is about two meters from the sofa.'), ('meas_half_meter', 'The table is half a meter from the sofa.'),
                  ('meas_metre_word', 'The gap is roughly a metre and a half.'), ('meas_feet', 'It is 3 feet away.'),
                  ('meas_angle', 'The sofa is at 45 degrees to my left.'), ('meas_coord', 'The sofa centre is at (1.2, 0.4).')]:
    r = copy.deepcopy(base); r['target'] = body.rstrip('\n')+'\n'+line+'\n</think>'+base['target'].split('</think>')[1]
    res.append(run(tag, 'd0_retrace_object_rel_distance', 'vqa', [r]))
# 3 withheld room (row consistently relabelled into a withheld alias)
for tag, scene, canon in [('withheld_alias_token', 'v0e47a88934bd', None), ('withheld_native', 'scene0161_00', None),
                          ('withheld_canonical_only', base['scene'], 'scannet/scene0161_02')]:
    r = copy.deepcopy(base); r['dataset'] = 'd1'; r['scene'] = scene
    if canon: r.setdefault('provenance', {})['canonical'] = canon
    res.append(run(tag, 'd0_retrace_object_rel_distance', 'vqa', [r]))
# 4 benchmark scene
for tag, ds, sc in [('bench_native', 'd1', 'scene0000_00'), ('bench_token', 'd1', 'v076e9c179d80'), ('bench_arkit_venue', 'd3', 'venue381644')]:
    r = copy.deepcopy(base); r['dataset'] = ds; r['scene'] = sc
    res.append(run(tag, 'd0_retrace_object_rel_distance', 'vqa', [r]))
# 5 program row of a direct-only type
u = first_ok('a0_units', 'adapted4')
for tag, qt in [('program_room_size', 'room_size_estimation'), ('program_object_size', 'object_size_estimation'),
                ('program_route_planning', 'route_planning'), ('program_rel_distance', 'object_rel_distance')]:
    r = copy.deepcopy(u); r['question_type'] = qt; r['ground_record']['type'] = qt
    res.append(run(tag, 'a0_units', 'routing', [r]))
r = copy.deepcopy(u); res.append(run('program_in_vqa_stream', 'a0_units', 'vqa', [r]))
r = copy.deepcopy(base); r['target'] = body.rstrip('\n')+'\n<tool_response>\ndistance 2.10 m\n</tool_response>\n</think>'+base['target'].split('</think>')[1]
res.append(run('direct_with_tool_response', 'd0_retrace_object_rel_distance', 'vqa', [r]))
# 6 routed row from the old selector
for tag, f in [('selector_response_deployed', lambda r: r.update(response_source='deployed')),
               ('selector_response_missing', lambda r: r.pop('response_source')),
               ('selector_mask_source_deployed', lambda r: r['ground_record'].update(mask_source='deployed_selector_v3', geometry_source='deployed')),
               ('selector_label_gt_but_v311', lambda r: r['ground_record'].update(mask_source='sam3_fitted_selector', gt_authority='selector'))]:
    r = copy.deepcopy(u); f(r); res.append(run(tag, 'a0_units', 'routing', [r]))
# 7 duplicate qid
r2 = copy.deepcopy(base); r2['target'] = base['target']
res.append(run('dup_qid_same_family', 'd0_retrace_object_rel_distance', 'vqa', [base, r2]))
json.dump(res, open(OUT/'MUTATIONS.json', 'w'), indent=1)
for x in res: print(('ADMITTED ' if x['admitted'] else 'refused  ')+x['mutation'], '|', str(x.get('refusal'))[:160])
