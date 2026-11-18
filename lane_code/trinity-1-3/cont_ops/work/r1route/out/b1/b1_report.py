#!/usr/bin/env python3
"""Compare two B1 returns. Offline measurement only; never imported by the reader."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random
import re
import statistics

RULES = ('null_argmax', 'candidates_argmax')
SEED, DRAWS = 20261115, 10000


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def unit_factor(question):
    for pattern, value in [(r'centimeters?|centimetres?|cm', 100.), (r'feet|foot|ft', 1/.3048),
                           (r'inches|inch', 1/.0254), (r'meters?|metres?|m', 1.)]:
        if re.search(r'\b(?:' + pattern + r')\b', question.lower()):
            return value
    raise ValueError('Unknown question unit: ' + question)


def mra(prediction, truth):
    return sum(abs(prediction-truth)/abs(truth) < 1-(.5+.05*i) for i in range(10))/10


def task_score(row, item):
    # Use the return's sealed scorer when present; raw journals use its strict answer grammar.
    value = row.get('measurements', {}).get('M2', {}).get('task_accuracy')
    if value is not None:
        return float(value)
    if 'answer' in row['output'].get('scores', {}):
        return float(row['output']['scores']['answer'])
    text = row['output'].get('text', '')
    tagged = re.findall(r'<answer>\s*(.*?)\s*</answer>', text, re.S)
    answer = tagged[-1].strip() if tagged else text.rsplit('</think>', 1)[-1].split('<|', 1)[0].strip()
    if row['output'].get('finish') == 'max_calls':
        return 0.
    match = re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?(?:\s*[a-zA-Z°]+)?', answer)
    if not match:
        return 0.
    prediction = float(re.match(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', answer)[0])
    return mra(prediction, float(item['ground_truth'])) if math.isfinite(prediction) else 0.


def stage(record):
    d = record.get('stage1')
    if not d or 'sam3' not in d:
        return 'diagnostics missing'
    if not any(d['sam3']['kept_per_frame']):
        return 'SAM 3 none'
    if d['linked_candidates'] == 0:
        reasons = d.get('lift_reasons', {})
        return 'lift empty: ' + (','.join(sorted(reasons)) if reasons else 'below existing score floor')
    return 'selector null with candidates' if d['chosen_index'] < 0 else 'selected'


def paired_bootstrap(a, b, items):
    ids = sorted(set(a) & set(b))
    if not ids:
        return dict(n=0, rooms=0, delta=None, ci95=None)
    rooms = defaultdict(list)
    for key in ids:
        rooms[items[key]['room_key']].append(b[key]-a[key])
    groups = list(rooms.values())
    sums, sizes = [sum(g) for g in groups], [len(g) for g in groups]
    rng = random.Random(SEED); draws = []
    for _ in range(DRAWS):
        chosen = [rng.randrange(len(groups)) for _ in groups]
        draws.append(sum(sums[i] for i in chosen)/sum(sizes[i] for i in chosen))
    draws.sort()
    return dict(n=len(ids), rooms=len(groups), delta=statistics.mean(b[k]-a[k] for k in ids),
                ci95=[draws[int(.025*(DRAWS-1))], draws[int(.975*(DRAWS-1))]],
                draws=DRAWS, seed=SEED, weighting='item mean; resample paired rooms')


def analyse(files, items, pairs=()):
    result = {}; scores = {}; stage_d = {(p['id'],p['name']) for p in pairs
        if p['h1']=='not seen' and p['cls'].startswith('D')}
    stage_d_confirmed=set()
    for rule, file in zip(RULES, files):
        selected = [r for r in rows(file) if r.get('mode')=='none' and r.get('arm')=='own'
                    and items[r['id']]['question_type']=='object_abs_distance']
        if len({r['id'] for r in selected}) != len(selected):
            raise ValueError('Duplicate baseline item IDs')
        table=Counter(); names=defaultdict(Counter); datasets=defaultdict(Counter); errors=[]
        not_seen=0; missing=0; scores[rule]={}
        for row in selected:
            item=items[row['id']]; records=row['output'].get('calls',{}).get('records',[])
            scores[rule][row['id']]=task_score(row,item)
            not_seen += any('not seen' in c.get('response','') for c in records)
            for c in records:
                if c['family']=='ground':
                    label=stage(c);table[label]+=1;missing+=label=='diagnostics missing'
                    d=c.get('stage1',{})
                    if d.get('rule',rule)!=rule:raise ValueError('Return rule differs from argument order')
                    match=re.search(r'obj="([^"]*)"',c['call']);name=match[1] if match else '<unknown>'
                    ns=c.get('response','').strip().endswith(': not seen')
                    names[name]['calls']+=1;names[name]['not_seen']+=ns
                    datasets[item['dataset']]['calls']+=1;datasets[item['dataset']]['not_seen']+=ns
                    if rule=='null_argmax' and (row['id'],name) in stage_d and d.get('linked_candidates',0)>0 and d.get('null_would_win'):
                        stage_d_confirmed.add((row['id'],name))
                elif c['family']=='gap':
                    m=re.fullmatch(r'distance ([\d.]+) m',c.get('response','').strip())
                    gt=float(item['ground_truth'])/unit_factor(item['question'])
                    errors.append(dict(id=row['id'],call=c['call'],response=c.get('response'),gt_m=gt,
                                       absolute_error_m=abs(float(m[1])-gt) if m else None))
        result[rule]=dict(reads=len(selected),stage_table=dict(table),diagnostics_missing=missing,
             capped_reads=sum(r['output'].get('finish') in ('max_new_tokens','max_calls') for r in selected),
             not_seen_reads=not_seen,task_mra=statistics.mean(scores[rule].values()) if selected else None,
             per_name=dict(names),per_dataset=dict(datasets),gap_errors=errors)
        metres={k:v for k,v in scores[rule].items() if unit_factor(items[k]['question'])==1}
        result[rule]['metre_items']=len(metres)
        result[rule]['metre_mra']=statistics.mean(metres.values()) if metres else None
    a,b=(scores[r] for r in RULES)
    result['paired_all']=paired_bootstrap(a,b,items)
    result['paired_metres']=paired_bootstrap({k:v for k,v in a.items() if unit_factor(items[k]['question'])==1},
                                            {k:v for k,v in b.items() if unit_factor(items[k]['question'])==1},items)
    result['coverage']=dict(null_only=sorted(set(a)-set(b)),candidates_only=sorted(set(b)-set(a)),
                            expected_baseline=150,expected_metres=43)
    result['predictions']=dict(null_stage_D_nonempty_null=dict(prediction='at least 60 of 67',
        observed=len(stage_d_confirmed) if not result['null_argmax']['diagnostics_missing'] and pairs else None,
        evidence_pairs=len(stage_d)),candidates_not_seen=dict(prediction='at most 8 reads',observed=result[RULES[1]]['not_seen_reads']),
        candidates_capped=dict(prediction='at most 2 reads',observed=result[RULES[1]]['capped_reads']),
        mra_delta_all=dict(prediction='+2 to +4 percentage points',observed_points=None if result['paired_all']['delta'] is None else 100*result['paired_all']['delta']),
        mra_delta_metres=dict(prediction='at least +8 percentage points',observed_points=None if result['paired_metres']['delta'] is None else 100*result['paired_metres']['delta']))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('null_items');p.add_argument('candidates_items');p.add_argument('--items',required=True)
    p.add_argument('--pairs-cache');p.add_argument('--json')
    a=p.parse_args();items={i['id']:i for i in json.loads(Path(a.items).read_text())['items']}
    pairs=json.loads(Path(a.pairs_cache).read_text()) if a.pairs_cache else []
    result=analyse([a.null_items,a.candidates_items],items,pairs)
    rendered=json.dumps(result,indent=2,allow_nan=False);print(rendered)
    if a.json:Path(a.json).write_text(rendered+'\n')

if __name__=='__main__':main()
