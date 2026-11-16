import json, collections, sys, importlib.util
sys.argv=['x']
spec=importlib.util.spec_from_file_location('nvd','out/native_vs_direct.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows=[json.loads(l) for f in ('main','camera') for l in open(f'in/direct_raw/items_leg_m544_{f}.jsonl')]
keep={'camera_displacement','camera_movement_direction','camera_rotation','object_abs_distance','room_size_estimation'}
rows=[r for r in rows if r['question_type'] in keep]
print(len(rows))
C=collections.Counter(); bad=[]
for r in rows:
    s=m.answer_states(r,True); pe=m.producer_error(r)
    t=r['question_type']
    C[(t,'bfc')]+=s['budget_forced_close']; C[(t,'nfa')]+=s['no_final_answer']; C[(t,'pe')]+=pe
    C[(t,'fc')]+=bool(r['forced_close']); C[(t,'htc')]+=bool(r['hit_token_cap']); C[(t,'su')]+=bool(r['stopped_unclosed']); C[(t,'pf')]+=bool(r['parse_failed'])
    C[(t,'bfc_nonzero')]+=s['budget_forced_close'] and r['score']>0
    if (s['no_final_answer'] or pe) and r['score']!=0: bad.append((r['key'],t,r['score'],r['hit_token_cap'],r['stopped_unclosed'],r['parse_failed'],r['finish_reason'],r['derivation_error']))
    # combos
    C[(t,'combo',r['forced_close'],r['hit_token_cap'],r['stopped_unclosed'],r['parse_failed'],r['finish_reason'],r['score']>0)]+=1
for k,v in sorted(C.items(),key=str): print(k,v)
print('CONFLICTS',len(bad)); [print(b) for b in bad[:20]]
