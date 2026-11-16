"""Reports from authenticated pass-5 merges, including both CP1 budget arms."""
import argparse
import collections
import importlib
import json
from pathlib import Path
import random
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter as A
from dev_scoring import DEV_ONLY, option_parse_failed
SCORERS = A.SCORERS


def aggregate(rows,field):
    values=[r['scores'][field] for r in rows if r['scores'][field] is not None]
    return dict(items=len(rows),scored=len(values),score_pct=100*sum(values)/len(values) if values else None,
                capped=sum(r['capped'] for r in rows),unanswered=sum(r['unanswered'] for r in rows),
                unparsed=sum(r['unparsed'] for r in rows))


def summarize(rows):
    result={}
    for st in ('primary','disagreement','unavailable'):
        rs=[r for r in rows if (r['stratum']==st if st!='unavailable' else r['stratum'] in ('missing_released','released_text_unavailable','missing_canonical','missing_both'))]
        fields=('released_answer',) if st=='primary' else ('released_answer','answer')
        result[st]={f:dict(overall=aggregate(rs,f),per_type={t:aggregate([r for r in rs if r['question_type']==t],f) for t in SCORERS}) for f in fields}
    result['disagreement_count_per_type']={t:sum(r['stratum']=='disagreement' and r['question_type']==t for r in rows) for t in SCORERS}
    result['unavailable_count_by_reason']=dict(collections.Counter(r['stratum'] for r in rows if r['stratum'] not in ('primary','disagreement')))
    return result


def paired(a,b,field,replicates=10000,seed=17):
    if replicates < 1:raise ValueError('Replicates must be positive')
    aa={r['key']:r for r in a};bb={r['key']:r for r in b}
    if set(aa)!=set(bb):raise ValueError('Paired keys differ')
    clusters=collections.defaultdict(list)
    for key,x in aa.items():
        y=bb[key]
        if (x['room'],x['stratum'],x['question_type'])!=(y['room'],y['stratum'],y['question_type']):raise ValueError('Paired metadata differs')
        v,w=x['scores'][field],y['scores'][field]
        if v is not None and w is not None:clusters[x['room']].append(v-w)
    if not clusters:return dict(items=0,rooms=0,delta_pp=None,ci95_pp=None)
    grouped=[(sum(ds),len(ds)) for _,ds in sorted(clusters.items())]
    n=sum(v[1] for v in grouped);delta=sum(v[0] for v in grouped)/n
    rng=random.Random(seed);samples=[]
    for _ in range(replicates):
        draw=rng.choices(grouped,k=len(grouped));samples.append(sum(v[0] for v in draw)/sum(v[1] for v in draw))
    samples.sort()
    def quantile(p):
        k=(len(samples)-1)*p;i=int(k);j=min(i+1,len(samples)-1)
        return 100*(samples[i]+(samples[j]-samples[i])*(k-i))
    return dict(items=n,rooms=len(grouped),delta_pp=100*delta,ci95_pp=[quantile(.025),quantile(.975)],
                replicates=replicates,seed=seed,estimator='item-weighted mean; resample whole physical rooms with replacement, retain all paired items')


def check_frames(row, task, cell, authority):
    if row.get('layout') != cell['layout'] or row.get('status') != 'complete':
        raise ValueError('Incomplete row or wrong layout')
    anchors = task['source_frame_indices']
    expanded = [i for i in anchors for _ in range(2)] if cell['layout']=='duplicate' else anchors
    media = row['media']; meta = media['metadata']; capture = authority[task['native']]
    if (media.get('anchor_indices') != anchors or meta.get('frames_indices') != expanded or
        media.get('timing_version') != A.R3.TIMING_VERSION or
        meta.get('fps') != capture['fps'] or meta.get('total_num_frames') != capture['total_num_frames'] or
        media.get('total_num_frames_lower_bound') != capture['total_num_frames_lower_bound'] or
        media.get('timestamps') != [i/capture['fps'] for i in expanded]):
        raise ValueError('Journal frames/timing differ from pinned payload')


def export_merged(cfg, attempt, output):
    """Only called after both original mergers have authenticated all journal rows."""
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    origin = A.original_adapter(cfg)
    origin.payload(cfg['devs1']['payload'])
    authority = origin.timing_authority()
    data = importlib.import_module('data')
    scoring = importlib.import_module('scoring')
    tasks = data.tasks_for(cfg['datasets'][0], cfg['roots'])
    by_key = {'devrows:'+t['example_id']:t for t in tasks}
    arms = ['ON16k'] + (['B2048','B4096'] if cfg['cells'][0]['model']=='cp1m200' else [])
    paths = {}
    for arm in arms:
        folder = Path(cfg['output']) / ('0' if arm=='ON16k' else 'budget_'+arm[1:]+'/0')
        summary = json.loads((folder/f'summary_{attempt}.json').read_text())
        dev = summary['benchmarks']['devrows']
        if not summary['parity_pass'] or dev['numbers_status'] != 'eligible' or dev['missing']:
            raise ValueError('Incomplete merge or parity gate failed')
        rows = A.jsonl(folder/f'items_{attempt}.jsonl')
        if len(rows)!=len(by_key) or {r['key'] for r in rows}!=set(by_key):
            raise ValueError('Report membership differs')
        results = []
        for row in rows:
            task = by_key[row['key']]
            check_frames(row, task, cfg['cells'][0], authority)
            visible = '</think>\n'+row['response_text'] if row['response_text'] else ''
            scores = {}
            for field in ('released_answer','answer'):
                value = A.scoring_label(task, field)
                if value is None:
                    scores[field] = None
                    continue
                again = scoring.score_item(dict(task,ground_truth=value,thinking=True), visible,
                    row['output_tokens'], cap=row['max_new_tokens'], finish=row['finish_reason'])
                scores[field] = again['score']
                if value==task['ground_truth'] and again['score']!=row['score']:
                    raise ValueError('Report rescore differs from authenticated row')
            unparsed = (option_parse_failed(row, scoring.official) if task['question_type'] in DEV_ONLY
                        else bool(row['parse_failed']))
            results.append(dict(key=row['key'],question_type=task['question_type'],room=task['room'],
                stratum=task['stratum'], scores=scores, capped=bool(row['hit_token_cap']),
                unanswered=not bool(row['response_text'].strip()),unparsed=unparsed))
        result = dict(model=cfg['cells'][0]['model'],arm=arm,request_binding=cfg['binding'],
                      source_sha256=cfg['source_sha256'],strata_sha256=cfg['devs1']['pins']['STRATA.jsonl'],
                      rows=results,summary=summarize(results))
        result['own_gt_by_stratum'] = {st:dict(overall=aggregate([r for r in results if r['stratum']==st], 'answer'),
            per_type={t:aggregate([r for r in results if r['stratum']==st and r['question_type']==t], 'answer')
                      for t in sorted({r['question_type'] for r in results if r['stratum']==st})})
            for st in sorted({r['stratum'] for r in results})}
        name = arm+'.json'; A.dump(output/name, result); paths[arm] = name
    return paths


def load_exports(path):
    path = Path(path)
    complete = json.loads((path/'MERGE_COMPLETE.json').read_text())
    if A.sha(path/'MERGE_INPUTS.json') != complete['receipt_sha256']:
        raise ValueError('Merge receipt differs')
    exports = {arm:json.loads((path/'report'/name).read_text()) for arm,name in complete['exports'].items()}
    for arm, value in exports.items():
        if A.sha(path/'report'/complete['exports'][arm]) != complete['export_sha256'][arm]:
            raise ValueError('Export digest differs')
        if value['arm'] != arm:raise ValueError('Export arm differs')
    return exports


def compare(cp1, f17, output, replicates=10000):
    left, right = load_exports(cp1), load_exports(f17)
    if set(left)!= {'ON16k','B2048','B4096'} or set(right)!= {'ON16k'}:
        raise ValueError('Comparison requires all CP1 arms and f17 ON16k')
    base = right['ON16k']
    if base['model'] != 'f17' or any(x['model']!='cp1m200' for x in left.values()):
        raise ValueError('Comparison checkpoint differs')
    if any(x['strata_sha256']!=base['strata_sha256'] for x in left.values()):
        raise ValueError('Comparison strata pins differ')
    comparisons = {}
    for arm, value in left.items():
        strata = sorted({r['stratum'] for r in value['rows']} | {r['stratum'] for r in base['rows']})
        comparisons[arm] = {}
        for st in strata:
            a = [r for r in value['rows'] if r['stratum']==st]
            b = [r for r in base['rows'] if r['stratum']==st]
            fields = ('released_answer',) if st=='primary' else ('released_answer','answer')
            comparisons[arm][st] = {f:dict(overall=paired(a,b,f,replicates),per_type={t:paired(
                [r for r in a if r['question_type']==t], [r for r in b if r['question_type']==t], f,replicates)
                for t in sorted({r['question_type'] for r in a+b})}) for f in fields}
    result = dict(aggregation='Item-weighted mean; paired physical-room bootstrap',
                  comparisons=comparisons, strata_sha256=base['strata_sha256'],
                  models={**{'CP1_'+k:v['summary'] for k,v in left.items()},'f17':base['summary']})
    A.dump(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cp1','f17','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--replicates',type=int,default=10000)
    args = parser.parse_args()
    compare(args.cp1,args.f17,args.output,args.replicates)
    print(args.output)


if __name__=='__main__':main()
