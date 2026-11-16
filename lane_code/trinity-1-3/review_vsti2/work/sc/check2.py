import sys,json,copy
sys.path.insert(0,'/scratch/jjyeung/orch_n30/review_vsti2/work/c')
import scorer, s0
from adapter import rows
W='/scratch/jjyeung/orch_n30/review_vsti2/work/sc/'
out={}
# 1. kit comparator check (own function)
out['comparator_check']={k:dict(primary=v['primary_pct'],kit=v['kit_primary_pct'],mismatches=len(v['mismatches'])) for k,v in scorer.comparator_check([W+'f17.per_question_scores.jsonl',W+'p1m200.per_question_scores.jsonl'],W+'SCORER_CHECK_mine.json').items()}
# 2. answer type inference equal
S=json.load(open('/scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c/work/input_full/SCORES.json'))
out['answer_type_diff']=sum((('multiple_choice' if v.get('options') else 'numeric')!=s0.infer_answer_type(v)) for v in S.values())
# 3. variant forms: kit score(final_text(raw)) vs authority score_our_cell strict on same raw
def variants(ans):
    return {'bare':'<think>\nr\n</think>\n'+ans,
            'tag':'<think>\nr\n</think>\n<answer>'+ans+'</answer><|im_end|>',
            'tag_upper':'<think>r</think><ANSWER>'+ans+'</ANSWER>',
            'answer_colon':'<think>r</think>\nAnswer: '+ans,
            'tag_ws':'<think>r</think>\n\n<answer> '+ans+' </answer>\n<|im_end|><|endoftext|>',
            'prose':'<think>r</think>\nThe answer is '+ans+'.',
            'two_tags':'<think>r</think><answer>Z</answer> <answer>'+ans+'</answer>',
            'unclosed':'<think>r '+ans,
            'empty':'<think>r</think>',
            'think_case':'<think>r</THINK>\n<answer>'+ans+'</answer>'}
tot=0;diff=[];by={}
for name in ('f17','p1m200'):
    data=rows(W+name+'.per_question_scores.jsonl')
    for form in variants('X'):
        recs=[]
        for r in data:
            ans=(r['parsed_answer'] or s0.official_fuzzy_matching(r['response_text']) or '0')
            raw=variants(ans)[form]
            rr=copy.deepcopy(r);rr['response_text']=raw;recs.append(rr)
        doc,computed=s0.score_our_cell(recs,'c','vstibench_repr450_v3',450)
        auth={c['example_id']:c for c in computed}
        kit=[]
        for rr in recs:
            k=scorer.score(scorer.final_text(dict(text=rr['response_text'])),rr)
            a=auth[rr['example_id']];tot+=1;kit.append((rr['question_type'],k['score']))
            if k['score']!=a['score'] or k['parsed']['parsed_answer']!=a['parsed_answer']:
                diff.append([name,form,rr['example_id'],k['score'],a['score'],k['parsed']['parsed_answer'],a['parsed_answer']])
        bt={}
        for t,v in kit:bt.setdefault(t,[]).append(v)
        by[name+':'+form]=dict(auth=round(doc['primary_score']*100,2),kit=round(scorer.collapse({t:sum(v)/len(v) for t,v in bt.items()})['primary']*100,2))
out['variant_checks']=tot;out['variant_diffs']=len(diff);out['diff_sample']=diff[:10];out['primaries']=by
json.dump(out,open(W+'CHECK2.json','w'),indent=1);print(json.dumps(out,indent=1))
