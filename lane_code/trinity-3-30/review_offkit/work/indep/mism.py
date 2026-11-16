import json,sys
sys.argv=['x']; exec(open('recompute.py').read().split('for b in (')[0])
for b in ('vsi','revsi'):
    R=rows(IN+f'ret_{b}/a0/results/0/budget_2048.jsonl'); M={m['source_key']:m for m in rows(IN+f'ret_{b}/a0/results/0/budget_2048.meta.jsonl')}
    for r in R:
        s,a=score(r,b)
        if abs(s-r['score'])>1e-12 or a!=r['extracted_answer']:
            m=M[r['key']]
            print(b,r['question_type'],'gt',r['ground_truth'],'mine',repr(a[:30]),s,'stored',repr(r['extracted_answer'][:30]),r['score'],'meta',m.get('forced_close'),repr(m.get('raw_answer'))[:30],m.get('score'),r.get('finish_reason'),r.get('output_tokens'))
