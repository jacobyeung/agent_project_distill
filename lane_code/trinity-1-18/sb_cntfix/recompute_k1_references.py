"""Diagnostic reference table with the pinned metric; cannot change the training freeze."""
import collections,gzip,json,sys
from pathlib import Path
sys.path.insert(0,'kit/files');import count_guard as G;import score_count_pricing as S
R=Path.cwd();meta=R/'kit/work/K1_LIFT_META.json';cfg=G.HERE/'FROZEN_CONFIG.json';sealed=G.sha(cfg)
inputs={str(meta):G.sha(meta),str(cfg):sealed,str(__file__):G.sha(__file__),**G.pins()};groups=collections.defaultdict(lambda:collections.defaultdict(list))
rules={'selected_train_rule':G.config()['rule'],'NMS_035_diagnostic':dict(nms=True,kind='max',joint=.35,iou=.5,contain=.8,stride=2)}
for c in G.read(meta)['captures']:
 key=c['capture'].replace('/','__');lp=R/'k1/labels_k1'/(key+'.labels.json.gz');tp=R/'k1/teacher_k1_full/teacher_k1'/key/'teacher.json.gz'
 with gzip.open(lp,'rt') as f:lab=json.load(f)
 with gzip.open(tp,'rt') as f:teacher=json.load(f)
 inputs[str(lp)]=G.sha(lp);inputs[str(tp)]=G.sha(tp)
 assert lab['teacher_sha256']==inputs[str(tp)]
 for cat,role in lab['roles'].items():
  if role!='gt':continue
  visible=set().union(*(set(lab['frames'][str(k)].get(cat,{}).get('gt_visible',[])) for k in range(32)))
  if not visible:continue
  truth=len(visible);binname=str(truth) if truth<=4 else '5+'
  for name,rule in rules.items():groups[name][binname].append(S.mra(S.tool_count(teacher,cat,rule)[0],truth))
assert G.sha(cfg)==sealed
result={name:{b:dict(n=len(v),MRA=100*sum(v)/len(v)) for b,v in bins.items()} for name,bins in groups.items()}
G.write('out/K1_REFERENCE_RECOMPUTE.json',dict(diagnostic_only=True,groups=result,freeze_unchanged=True,inputs_sha256=inputs));print(json.dumps(result,indent=2))
