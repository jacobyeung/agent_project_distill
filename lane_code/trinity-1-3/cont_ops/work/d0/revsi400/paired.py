"""Strict paired ranking report; scores and differences are fractions, not percentages."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'kit/reader'))
import official_score as O

ARMS = {'B2048': 'budget_2048.jsonl', 'ON16k': 'items_a0.jsonl', 'B4096': 'budget_4096.jsonl'}
META = ('source_frame_indices', 'revsi_tier', 'revsi_set', 'video_sha256', 'sidecar_verified',
        'key', 'thinking', 'decoding', 'frames', 'layout', 'anchor_indices', 'prompt_text',
        'processed_height_width', 'visual_tokens_per_frame')
PROTOCOL = ('cells', 'gpus', 'max_tokens', 'temperature', 'thinking', 'max_model_len',
            'max_seqs', 'inflight', 'smoke_items', 'engine_version', 'mode')
SCORER_SHA = 'b279ddc18acd3e019b8343214d963a60d3bafcd929f2a3e4d965a0aa1b88d409'


def identity(row):
    if not isinstance(row, dict) or 'example_id' not in row or 'id' not in row:
        raise ValueError('Missing item identity')
    if str(row['example_id']) != str(row['id']):
        raise ValueError('Conflicting item identity')
    return str(row['id'])


def indexed(rows):
    result = {}
    for row in rows:
        key = identity(row)
        if key in result:
            raise ValueError('Duplicate item: '+key)
        result[key] = row
    return result


def equal_field(a, b, field):
    if field not in a or field not in b or a[field] != b[field]:
        raise ValueError('Metadata differs: '+field)


def validate(tasks, current, reference, *, partial=False):
    expected = indexed(tasks)
    if not partial and (len(expected) != 679 or len({(r['dataset'],r['scene_name']) for r in tasks}) != 261):
        raise ValueError('Require 679 items and 261 scenes')
    kinds = {t for group in O.GROUPS.values() for t in group}
    if any(r['question_type'] not in kinds for r in tasks):
        raise ValueError('Foreign subtype')
    all_indices = []
    for packet in (current, reference):
        if set(packet) != set(ARMS):
            raise ValueError('Require exactly three arms')
        for arm in ARMS:
            observed = indexed(packet[arm])
            if set(observed) != set(expected):
                raise ValueError('Membership differs: '+arm)
            for key, task in expected.items():
                row = observed[key]
                for field in task:
                    equal_field(task, row, field)
                if row.get('status') not in ('complete', 'error'):
                    raise ValueError('Invalid status')
                score = row.get('score')
                if row['status']=='complete' and (type(score) not in (float,int) or not math.isfinite(score) or not 0<=score<=1):
                    raise ValueError('Invalid score')
                for field in META:
                    if field not in row:
                        raise ValueError('Missing metadata: '+field)
                if not isinstance(row.get('media'),dict):
                    raise ValueError('Missing media metadata')
            all_indices.append(observed)
    # Every arm has the same task, prompt, media and processor identity on both reads.
    for a,b in zip([indexed(current['ON16k'])],[indexed(reference['ON16k'])]):
        for key in a:equal_field(a[key],b[key],'prompt_tokens')
    anchor = all_indices[0]
    for rows in all_indices[1:]:
        for key, a in anchor.items():
            b = rows[key]
            for field in META:
                equal_field(a,b,field)
            # Receipt paths and hashes include job-local paths; the realized layout/pixels do not.
            media_a={k:v for k,v in a['media'].items() if k!='frame_receipt'}
            media_b={k:v for k,v in b['media'].items() if k!='frame_receipt'}
            if media_a != media_b:
                raise ValueError('Media metadata differs')
    return expected


def interval(values):
    import numpy as np
    valid = values[np.isfinite(values)]
    return dict(percentile_95=np.percentile(valid,[2.5,97.5]).tolist() if len(valid) else None,
                valid_replicates=len(valid))


def subtype_comparisons(tasks, current, reference, repetitions, seed):
    """Use aggregate()'s identical sorted scenes, multinomial weights and undefined draws."""
    import numpy as np
    scenes=sorted({(r['dataset'],r['scene_name']) for r in tasks})
    scene_index={s:i for i,s in enumerate(scenes)}
    kinds=sorted({r['question_type'] for r in tasks}); type_index={t:i for i,t in enumerate(kinds)}
    counts=np.zeros((len(scenes),len(kinds))); totals=[np.zeros_like(counts),np.zeros_like(counts)]
    indices=[indexed(current),indexed(reference)]
    for task in tasks:
        i=scene_index[(task['dataset'],task['scene_name'])];j=type_index[task['question_type']]
        counts[i,j]+=1
        for total, rows in zip(totals,indices):
            r=rows[identity(task)]
            total[i,j]+=0 if r['status']!='complete' or r.get('derivation_error') else r['score']
    weights=np.random.default_rng(seed).multinomial(len(scenes),np.full(len(scenes),1/len(scenes)),size=repetitions)
    den=weights@counts
    draws=[np.divide(weights@total,den,out=np.full_like(den,np.nan),where=den>0) for total in totals]
    points=[total.sum(0)/counts.sum(0) for total in totals]
    return {typ:dict(items=int(counts[:,j].sum()),current=float(points[0][j]),parent=float(points[1][j]),
                     delta=float(points[0][j]-points[1][j]),**interval(draws[0][:,j]-draws[1][:,j]),
                     current_interval=interval(draws[0][:,j]),parent_interval=interval(draws[1][:,j]))
            for typ,j in type_index.items()}


def compare(tasks, current, reference, *, repetitions=10000, seed=544, partial=False):
    validate(tasks,current,reference,partial=partial)
    if repetitions <= 0 or type(repetitions) is not int or type(seed) is not int:
        raise ValueError('Invalid bootstrap parameters')
    if hashlib.sha256((ROOT/'kit/reader/official_score.py').read_bytes()).hexdigest()!=SCORER_SHA:
        raise ValueError('Accepted scorer differs')
    reports={}
    for arm in ARMS:
        a,b=current[arm],reference[arm]
        # This function is byte-identical to the one shipped for job 170037.
        pair=O.paired(tasks,a,b,repetitions=repetitions,seed=seed,allow_partial=partial)
        score_a=O.aggregate(tasks,a,current['ON16k'],repetitions=repetitions,seed=seed,allow_partial=partial)
        score_b=O.aggregate(tasks,b,reference['ON16k'],repetitions=repetitions,seed=seed,allow_partial=partial)
        subtypes=subtype_comparisons(tasks,a,b,repetitions,seed)
        reports[arm]=dict(role='primary' if arm=='B2048' else 'secondary',current=score_a,parent=score_b,
            paired=pair,subtypes=subtypes,
            facing={typ.removeprefix('object_rel_direction_'):value for typ,value in subtypes.items()
                    if typ in O.GROUPS['object_rel_direction']})
    return dict(schema=1,purpose='ranking only',decision=None,units='fraction',
        difference='current minus step 544',scorer=dict(path='kit/reader/official_score.py',function='paired',sha256=SCORER_SHA),arms=reports)


def load_packet(path, step):
    path=Path(path)
    marker=json.loads((path/'COMPLETE.json').read_text())
    spec=json.loads((path/'SPEC.json').read_text())
    request=json.loads((path/'a0/request.json').read_text())
    if (marker.get('mode')!='production' or marker.get('synthetic') is not False
        or marker.get('generation_synthetic') is not False or marker.get('items')!=679
        or (path/'FAILED.json').exists() or spec.get('step')!=step or request.get('mode')!='production'
        or request.get('reader',{}).get('step')!=step):
        raise ValueError('Incomplete, synthetic or wrong-step packet')
    artifact=spec.get('artifact',{})
    import re
    expected_path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/'+('469ddece' if step==544 else '359fcc3c')+'/m'+str(step)+'/artifact.json'
    if (artifact.get('path')!=expected_path or artifact.get('kind')!='c1_export'
        or not isinstance(artifact.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',artifact['sha256'])
        or artifact['sha256']=='0'*64
        or (step==544 and artifact['sha256']!='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef')
        or request.get('models',{}).get('cp1m200')!=artifact):
        raise ValueError('Checkpoint identity differs')
    verification=request['reader'].get('export_verification',{})
    if (verification.get('status')!='VERIFIED' or verification.get('step')!=step
        or verification.get('artifact')!={k:artifact[k] for k in ('path','sha256')}):
        raise ValueError('Export verification differs')
    rows={arm:O.read_rows(path/'a0/results/0'/name) for arm,name in ARMS.items()}
    return rows,request


def packet_comparison(current, reference, step):
    if type(step) is not int or step not in (200,400,600,800,1000):
        raise ValueError('Invalid current step')
    a,request_a=load_packet(current,step);b,request_b=load_packet(reference,544)
    for field in PROTOCOL:
        equal_field(request_a,request_b,field)
    equal_field(request_a['models'],request_b['models'],'base')
    def without_paths(value):
        if isinstance(value,dict):return {k:without_paths(v) for k,v in value.items() if k!='path'}
        if isinstance(value,list):return [without_paths(v) for v in value]
        return value
    if without_paths(request_a['datasets'])!=without_paths(request_b['datasets']):
        raise ValueError('Dataset protocol differs')
    # Pin the requested protocol independently of the two packets agreeing.
    required=dict(max_seqs=32,inflight=16,max_tokens=16384,max_model_len=49152,temperature=0,thinking=True,gpus=1,smoke_items=0,engine_version='0.32.0')
    if any(request_a.get(k)!=v for k,v in required.items()):raise ValueError('Protocol differs')
    tasks=O.read_rows(ROOT/'kit/cohort/c5.jsonl')
    report=compare(tasks,a,b)
    report.update(current_step=step,parent_step=544,inputs={label:{arm:hashlib.sha256((Path(path)/'a0/results/0'/name).read_bytes()).hexdigest()
        for arm,name in ARMS.items()} for label,path in [('current',current),('parent',reference)]})
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--current',required=True);p.add_argument('--reference',default=str(ROOT/'evidence/reference544'))
    p.add_argument('--step',type=int,choices=(200,400,600,800,1000),default=400);p.add_argument('--output',required=True)
    a=p.parse_args(argv);report=packet_comparison(a.current,a.reference,a.step)
    Path(a.output).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
