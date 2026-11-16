from rlkit import prompts as P, sampler as S, select as SEL, floor as F, headuse as H
row = dict(qid='vsibench_0001', scene='scene0011_00', question_type='object_counting', answer='3', source='vsibench', dataset='VSI-Bench',
           student_input=dict(question='How many chairs?', options=None, frame_indices=list(range(32))))
pool, refused = P.build([row], ['scene0011_00'], 32)
print('G built source', pool[0]['source'], 'refused', refused)
print('G sampler accepts', S.check_prompts(pool, {}))
for src in ('VSI_Bench', 'vsi_bench_test', 'dev-S1', 'devS1_holdout', 'arkit_vsibench'.replace('vsibench','vsi bench')):
    p = dict(pool[0], source=src, prompt_id=src)
    try: print('H', src, S.check_prompts([p], {}))
    except Exception as e: print('H', src, 'refused', e)
class V: pass
class Obj: pass
rec = dict(heads={}, calls=[dict(kind='ground')])
for kw in (dict(verify=V()), dict(reread=V()), dict(logits_processor=lambda i, l: l), dict(pose_source='tower', tower_state=Obj())):
    r = dict(rec, response_sources=S.response_sources(rec, kw))
    print('I', list(kw), '->', SEL.artifact_policy(r))
GroundV3 = type('GroundV3', (), {})
r = dict(rec, response_sources=S.response_sources(rec, dict(ground_backend=GroundV3(), mask_source='mdg')))
print('I fake GroundV3 class ->', SEL.artifact_policy(r))
own = dict(heads=dict(ground_queries=[dict(name='chair', prob=[0.9], uv=[[1,1]])]), calls=[dict(kind='ground')])
print('I own grounding head query ->', SEL.artifact_policy(dict(own, response_sources=S.response_sources(own, {}))))
try: print('J floor no pool', F.check_heldout([dict(prompt_id='x', scene_key='s')], []))
except Exception as e: print('J', e)
recs = [dict(calls=[dict(call='<ground obj="zebra">', kind='ground', response='zebra: not seen')]), dict(calls=[dict(call='<dist P1 P2>', kind='calculator')]), dict(calls=[dict(call='<gap a="x">', kind='error')])]
print('K openers', [H.openers(x) for x in recs])
print('K perturb', H.perturb_text('distance 3.22 m\nchair: f1 [500,500] 0.93\nB1: f1 centre (-2.09, -0.51, -1.07) m\nyaw 12 deg'))
