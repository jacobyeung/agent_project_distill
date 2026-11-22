import json, collections, numpy as np, sys
O='/scratch/jjyeung/orch_n30/lever8/j1/out/'
recs=[json.loads(l) for l in open(O+'ITEMS_J1.jsonl')]
R=json.load(open(O+'RELIFT_J1.json'))
arms=['a','e','h1','h0','k']
print('records',len(recs), collections.Counter(r['arm'] for r in recs))
items=sorted({r['item_id'] for r in recs}); print('items',len(items))
by={(r['item_id'],r['arm']):r for r in recs}
assert len(by)==len(recs)
rows={r['item_id']:r for r in R['rows']}
mism=0
for (iid,arm),r in by.items():
    if rows[iid][arm]!=r['score'] or rows[iid]['gaps'][arm]!=r['printed_gap_m'] or rows[iid]['room']!=r['room'] or rows[iid]['dataset3']!=r['dataset']: mism+=1
print('json-vs-items mismatches',mism)
def mean(v): return float(np.mean(v))
for ds in ['all','ARKit','ScanNet','ScanNet++']:
    ii=[i for i in items if ds=='all' or by[(i,'a')]['dataset']==ds]
    rooms={by[(i,'a')]['room'] for i in ii}
    m={k:mean([by[(i,k)]['score'] for i in ii]) for k in arms}
    print(ds,len(ii),len(rooms),{k:round(m[k],3) for k in arms},{k+'-a':round(m[k]-m['a'],2) for k in arms[1:]},
          {k:round((m[k]-m['a'])/(m['e']-m['a']),3) for k in ['h1','h0','k']})
# no-lift items
for k in arms:
    nolift=[i for i in items if by[(i,k)]['printed_gap_m'] is None]
    zero=[i for i in items if by[(i,k)]['score']==0]
    print(k,'nolift',len(nolift),'score0',len(zero), 'nolift&score>0', sum(1 for i in nolift if by[(i,k)]['score']>0))
# h0 items with an operand with no mask on any anchor
c=0
for i in items:
    r=by[(i,'h0')]
    if any(len(o['frames_with_mask'])==0 for o in r['operands']): c+=1
print('h0 items with an operand empty on all anchors',c)
for k in arms:
    c=sum(1 for i in items if any(len(o['frames_with_mask'])==0 for o in by[(i,k)]['operands']))
    c2=sum(1 for i in items if any(o['lift_best'] is None for o in by[(i,k)]['operands']))
    print(k,'items w/ operand all-empty',c,'items w/ operand lift_best None',c2)
lift=[i for i in items if by[(i,'h0')]['printed_gap_m'] is not None]
print('h0 lifts on',len(lift), 'h0-a',round(mean([by[(i,'h0')]['score']-by[(i,'a')]['score'] for i in lift]),2),
      'e-a',round(mean([by[(i,'e')]['score']-by[(i,'a')]['score'] for i in lift]),2),
      'k-a', round(mean([by[(i,'k')]['score']-by[(i,'a')]['score'] for i in lift]),2),
      'h1-a', round(mean([by[(i,'h1')]['score']-by[(i,'a')]['score'] for i in lift]),2))
nl=[i for i in items if by[(i,'h0')]['printed_gap_m'] is None]
print('h0 nolift items: a mean',round(mean([by[(i,'a')]['score'] for i in nl]),2),'e mean',round(mean([by[(i,'e')]['score'] for i in nl]),2),'k',round(mean([by[(i,'k')]['score'] for i in nl]),2),
  'a nolift among them',sum(by[(i,'a')]['printed_gap_m'] is None for i in nl))
# P/R recompute from operand pr? anchors with mask GT empty
for k in arms:
    pe=sum(o['pr']['pred_on_empty_gt'] for i in items for o in by[(i,k)]['operands'])
    gf=sum(o['pr']['gt_frames'] for i in items for o in by[(i,k)]['operands'])
    pf=sum(o['pr']['pred_frames'] for i in items for o in by[(i,k)]['operands'])
    print(k,'pred_on_empty_gt',pe,'gt_frames',gf,'pred_frames',pf)
# operands count
print('operands total',sum(len(by[(i,'a')]['operands']) for i in items), 'no served call',sum(1 for i in items for o in by[(i,'a')]['operands'] if not o['served_call']))
# k: frames with mask == frames with gt?
bad=sum(1 for i in items for o in by[(i,'k')]['operands'] if o['frames_with_mask']!=o['frames_with_gt'])
print('k operands where mask frames != gt frames',bad)
bad=sum(1 for i in items for o in by[(i,'h0')]['operands'] if not set(o['frames_with_mask'])<=set(o['frames_with_gt']))
print('h0 operands with mask outside gt frames',bad)
