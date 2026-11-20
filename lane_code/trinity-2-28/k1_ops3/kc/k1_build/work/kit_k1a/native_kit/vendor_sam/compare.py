"""Pair each experiment with the baseline, and audit proposal recall and precision."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import route_table as R,analyze as A,price_masks as P
import argparse,collections

def metrics(records,frames):
 result=[]
 for ds in ['All']+sorted({r['dataset'] for r in records}):
  rr=[r for r in records if ds=='All' or r['dataset']==ds];fs=[r for r in frames if ds=='All' or r['dataset']==ds]
  den=sum(f['gt_usable'] for f in fs);pd=sum(f['proposals'] for f in fs)
  result.append(dict(dataset=ds,operand_instances=len(rr),ever_proposed=sum(r['ever_proposed'] for r in rr),ever_recall=sum(r['ever_proposed'] for r in rr)/max(1,len(rr)),usable_frame_recall=sum(f['matched_usable'] for f in fs)/max(1,den),usable_frame_denominator=den,proposal_precision=sum(f['matched_proposals'] for f in fs)/max(1,pd),proposal_denominator=pd,accepted_unique=sum(r['accepted_unique'] for r in rr),accepted_count=sum(r['accepted_count'] for r in rr)))
 return result

def run(a):
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True);items=rows(a.items);direct=json.loads(Path(a.direct).read_text());base=R.build(items,direct,rows(a.baseline_program));new=R.build(items,direct,rows(Path(a.priced)/'PER_ITEM.jsonl'));dump(out/'ROUTE.json',new);(out/'ROUTE.md').write_text(R.markdown(new));bp={r['qid']:r for r in base['paired']};contrasts=[];lines=['Paired variant versus baseline; raw program scores, no-answer = 0.','', '| Dataset | Type | Baseline % | Variant % | Variant − baseline pp [95% room CI] | Variant − direct pp [95% CI] |','|---|---|---:|---:|---|---|']
 for r in new['table']:
  ps=[x for x in new['paired'] if x['type']==r['type'] and (r['dataset']=='All' or x['dataset']==r['dataset'])];ci=R.interval([(x['room'],bp[x['qid']]['program'],x['program']) for x in ps]);bb=next(b for b in base['table'] if (b['dataset'],b['type'])==(r['dataset'],r['type']));contrasts.append(dict(dataset=r['dataset'],type=r['type'],**ci));lines.append(f"| {r['dataset']} | {r['type']} | {bb['program_pct']:.2f} | {r['program_pct']:.2f} | {ci['difference_pp']:+.2f} [{ci['low_pp']:+.2f}, {ci['high_pp']:+.2f}] | {r['difference_pp']:+.2f} [{r['low_pp']:+.2f}, {r['high_pp']:+.2f}] |")
 dump(out/'PAIRED_BASELINE.json',contrasts)
 m=json.loads(Path(a.manifest).read_text());gtmap={r['scene']:r for r in rows(a.gt_captures)};by=collections.defaultdict(list)
 for q in items:by[q['scene']].append(q)
 records=[];frames=[]
 for c in m['captures']:
  if c['scene'] not in gtmap:continue
  sid=c['scene'].replace('/','__');raw=validate_cache(load_cache(Path(a.cache)/(sid+'.npz')),c,sha(a.manifest));gt,_=P.L.load_base(gtmap[c['scene']]['pricing_gt'],c['anchor_indices']);sel=load_cache(Path(a.priced)/(sid+'.selected.npz'));rr,_,_,ff,_=A.audit_capture(c,raw,gt,sel,by[c['scene']]);records+=rr;frames+=ff;print('recall',c['scene'],flush=True)
 write_rows(out/'PER_INSTANCE.jsonl',records);mm=metrics(records,frames);dump(out/'RECALL_PRECISION.json',mm)
 suspect={(r['scene'],r['name']) for r in records if r.get('prompt_relation')=='annotation_binding_suspect'};clean_records=[r for r in records if (r['scene'],r['name']) not in suspect];clean_frames=[f for f in frames if (f['scene'],f['name']) not in suspect];dump(out/'RECALL_PRECISION_BINDING_CLEAN.json',metrics(clean_records,clean_frames));lines+=['',f'GT-binding sensitivity: {len(suspect)} capture/phrase targets map ceiling light to ceiling. RECALL_PRECISION_BINDING_CLEAN.json excludes these targets; primary scores and recall retain the original baseline definition.']
 lines+=['','Precision means overlap with a queried annotated instance, not exhaustive semantic correctness.','', '| Dataset | Ever recall | Frame recall (≥154 pixels) | Proposal precision | Instances / proposals |','|---|---:|---:|---:|---:|']
 for r in mm:lines.append(f"| {r['dataset']} | {100*r['ever_recall']:.2f}% | {100*r['usable_frame_recall']:.2f}% | {100*r['proposal_precision']:.2f}% | {r['operand_instances']} / {r['proposal_denominator']} |")
 
 baseline_metrics=Path(a.baseline_metrics)
 if baseline_metrics.exists():
  bm={r['dataset']:r for r in json.loads(baseline_metrics.read_text())};lines+=['','| Dataset | Ever recall baseline / variant | Frame recall baseline / variant | Precision baseline / variant |','|---|---:|---:|---:|']
  for r in mm:
   b=bm[r['dataset']];lines.append('| '+r['dataset']+' | '+' | '.join(f"{100*b[k]:.2f}% / {100*r[k]:.2f}%" for k in ['ever_recall','usable_frame_recall','proposal_precision'])+' |')
 (out/'COMPARISON.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines));dump(out/'COMPLETE.json',dict(manifest_sha256=sha(a.manifest),paired_items=new['paired_items']))
if __name__=='__main__':
 p=argparse.ArgumentParser(__doc__)
 for n in ['manifest','items','direct','cache','priced','baseline-program','gt-captures','out']:p.add_argument('--'+n,required=True)
 p.add_argument('--baseline-metrics',default=str(HERE.parent/'out/BASELINE_RECALL_PRECISION.json'));run(p.parse_args())
