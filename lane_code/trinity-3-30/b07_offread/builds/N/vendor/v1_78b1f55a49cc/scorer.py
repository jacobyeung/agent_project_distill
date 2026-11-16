"""Unmodified authority functions with explicit final-answer extraction."""
import s0 as official
from adapter import load,rows,pin,dump

GROUPS=official.VSTI_PRIMARY_GROUPS
TYPES=tuple(t for ts in GROUPS.values() for t in ts)

def final_text(decoded):
    if 'script_answer' in decoded:return decoded['script_answer'] or ''
    text=decoded.get('text','')
    if '</think>' not in text:return ''
    text=text.rsplit('</think>',1)[1].strip()
    return text.replace('<|im_end|>','').replace('<|endoftext|>','').strip()

def score(answer,item):
    answer_type=item.get('answer_type') or ('multiple_choice' if item.get('options') else 'numeric')
    parsed=official.parse_answer_v1(answer,answer_type,item.get('options'))
    gt=str(item['ground_truth']).strip()
    def metric(pred):
        return (official.official_exact_match(pred,gt) if answer_type=='multiple_choice' else
                official.official_mra(official.official_to_float(pred),official.official_to_float(gt),.5,.95,.05))
    value=metric(parsed['parsed_answer']) if parsed['parse_status']=='ok' and parsed['parsed_answer'] is not None else 0.
    return dict(score=value,official_fuzzy_score=metric(official.official_fuzzy_matching(answer)),
                answer=answer,parsed=parsed,no_final_answer=not bool(answer))

def collapse(values,require_all=True):
    if require_all and set(values)!=set(TYPES):return None
    groups={g:sum(values[t] for t in ts)/len(ts) for g,ts in GROUPS.items() if all(t in values for t in ts)}
    return dict(subtasks=groups,primary=sum(groups.values())/5 if len(groups)==5 else None)

def comparator_check(paths,output):
    result={}
    for path,expected in zip(paths,(66.95,68.71),strict=True):
        data=rows(path);mismatches=[];kit_by_type={}
        doc,computed=official.score_our_cell(data,'cell','vstibench_repr450_v3',450)
        by_id={r['example_id']:r for r in computed}
        for row in data:
            r=by_id[row['example_id']]
            own=score(final_text(dict(text='</think>'+row['response_text'])),row)
            kit_by_type.setdefault(row['question_type'],[]).append(own['score'])
            for field in ('score','official_fuzzy_score'):
                if r[field]!=row[field]:mismatches.append([row['example_id'],field,r[field],row[field]])
                if own[field]!=row[field]:mismatches.append([row['example_id'],'kit.'+field,own[field],row[field]])
        val=round(doc['primary_score']*100,2)
        valf=round(doc['fuzzy_primary_score']*100,2)
        collapsed=collapse(doc['category_scores'])
        kit=collapse({t:sum(v)/len(v) for t,v in kit_by_type.items()})
        if mismatches or val!=expected or round(kit['primary']*100,2)!=expected or abs(collapsed['primary']-doc['primary_score'])>1e-12:
            raise ValueError('comparator scoring differs: '+str((val,mismatches[:3])))
        result[PathName(path)]=dict(source=pin(path),items=len(data),mismatches=mismatches,
                                  primary_pct=val,kit_primary_pct=round(kit['primary']*100,2),kit_items=len(data),official_fuzzy_primary_pct=valf,collapse=collapsed)
    dump(output,result);return result

def PathName(path):
    from pathlib import Path
    return Path(path).name.split('.')[0]
