"""Configure the reader core, preserve its generated text, and write measurements."""
import argparse
import importlib
import json
from pathlib import Path
from collections import defaultdict
from . import scorers
from .modes import mode_key, applies
from e2e_reader.core import E2EGenerator


class H1Generator:
    def __init__(self,*args,**kwargs):
        self.core=E2EGenerator(*args,**kwargs)
    def __call__(self,item):
        out=self.core(item);tok=self.core.processor.tokenizer
        for r in scorers.records(out):
            end=r['at_token'];prefix=tok.decode(out['tokens'][:end],skip_special_tokens=False)
            start=prefix.rfind(r['call'])
            if start>=0:
                # First token that overlaps the call's first character.
                for i in range(max(0,end-96),end):
                    if len(tok.decode(out['tokens'][:i+1],skip_special_tokens=False))>start:r['start_token']=i;break
        perception=self.core.perception
        if hasattr(perception,'last') and 'heads' in perception.last:
            h=perception.last['heads'];out['heads']=dict(pose9=h.pose9.tolist(),gravity=h.gravity.tolist())
            if 'geometry' in perception.last:out['heads']['depth_grid']=perception.last['geometry'].depth_grid.tolist()
            out['intervention']=perception.last['intervention']
        return out


def measure(output,item,baseline=None):
    result=dict(M1=scorers.placement(output,item),M2=scorers.accuracy(output,item))
    result['M1']['non_terminating'] = int(output.get('finish') == 'max_calls')
    if baseline is not None:result['M3']=scorers.usage(baseline,output,item)
    if 'benchmark_item' in item or 'ground_truth' in item:result['M4']=scorers.benchmark(output,item)
    return result


def table(rows, constants=None):
    groups=defaultdict(list)
    for row in rows:groups[(row['type'],row['arm'],row['mode'])].append(row)
    lines=['| Type | Arm | Mode | N | Calls | Exact route | Follow | Stick | Other | Head distance MAE (m) | Turn MAE (deg) | Direction accuracy | M4 | Seconds/item | Task accuracy/MRA | No-information f32 | Unserved calls | Error calls | Non-terminating count | Non-terminating rate |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for key,rs in sorted(groups.items()):
        def mean(values):
            v=[x for x in values if x is not None];return f'{sum(v)/len(v):.4f}' if v else '—'
        m=[r['measurements'] for r in rs];usage=[v.get('M3',{}) for v in m if v.get('M3',{}).get('eligible')]
        values=[mean(v['M1'].get(k) for v in m) for k in ('call_rate','exact')]
        values += [mean(v.get(k) for v in usage) for k in ('follow','stick','other')]
        head_calls=[c for v in m for c in v['M2']['calls']]
        values += [mean(c.get(k) for c in head_calls) for k in ('absolute_error_m','error_deg','correct')]
        values += [mean(v.get('M4',{}).get('score') for v in m),mean(r['output'].get('seconds') for r in rs)]
        c=(constants or {}).get(key[0],{})
        constant=c.get('dev_mra_f32',c.get('dev_acc'))
        total=sum(v['M2'].get('call_count',0) for v in m)
        values += [mean(v['M2'].get('task_accuracy') for v in m),
                   '—' if constant is None else f'{constant/100:.4f}']
        values += ['—' if not total else f"{sum(v['M2'].get(k+'_calls',0) for v in m)/total:.4f}" for k in ('unserved','error')]
        non_terminating = sum(v['M1'].get('non_terminating', 0) for v in m)
        values += [str(non_terminating), f'{non_terminating/len(rs):.4f}']
        lines.append('| '+' | '.join([*key,str(len(rs)),*values])+' |')
    return '\n'.join(lines)+'\n'


def run(items,factory,arms,modes,output):
    """factory(arm, mode, item) returns an H1Generator with artifact-owned heads."""
    rows=[];output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with (output/'items.jsonl').open('w') as f:
        for item in items:
            item=dict(item)
            for arm in arms:
                base=factory(arm,{'name':'none'},item)(item)
                for mode in [{'name':'none'},*(m for m in modes if applies(m,item))] if arm=='own' else [{'name':'none'}]:
                    value=base if mode['name']=='none' else factory(arm,mode,item)(item)
                    measurements=measure(value,item,None if mode['name']=='none' else base)
                    # Keep text and pose readouts; depth grids are reduced by M2 before journaling.
                    saved={**value}
                    if 'heads' in saved:saved['heads']={k:v for k,v in saved['heads'].items() if k!='depth_grid'}
                    row=dict(id=item['id'],room_key=item.get('room_key'),type=scorers.metadata(item)['question_type'],arm=arm,mode=mode_key(mode),
                             item_set=item.get('item_set'),intervention=mode,output=saved,measurements=measurements)
                    f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();rows.append(row)
    (output/'report.md').write_text(table(rows));return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--items',required=True);p.add_argument('--factory',required=True,help='module:function; loads the checkpoint and returns H1Generator')
    p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    module,name=a.factory.split(':');factory=getattr(importlib.import_module(module),name)
    cfg=json.loads(Path(a.config).read_text());items=[json.loads(s) for s in Path(a.items).read_text().splitlines() if s.strip()]
    run(items,factory,cfg['arms'],cfg['modes'],a.output)
