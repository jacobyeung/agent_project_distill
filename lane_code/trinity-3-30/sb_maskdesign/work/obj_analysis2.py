import json,collections,sys
import numpy as np
D='/scratch/jjyeung/orch_n30/sb_maskfail/out/'
recs=json.load(open(D+'MASKFAIL.json'))['records']
ops=collections.defaultdict(list)
for r in recs: ops[(r['row'],r['object'])].append(r)
thr=np.linspace(.5,.95,10)
def mra(p,l): return 0. if p is None else float(np.mean(abs(p-l)/l<=1-thr+1e-12))
sc={}
with open('/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl') as f:
    for line in f:
        if '"A0_deployed"' in line or '"A2_gt_masks"' in line:
            r=json.loads(line)
            if r['arm'] in('A0_deployed','A2_gt_masks'): sc[(r['arm'],r['row_id'])]=mra(r['prediction'],r['label'])
ORDER=['refused','never_visible','wrong_object','weak_overlap','right_obj_bad_pricing_frame','good_pricing_frame']
O={}
for key,rs in ops.items():
    rs=sorted(rs,key=lambda r:r['frame']);vis=[r for r in rs if r['visible'] and r['valid']];served=[r for r in rs if r['served_area']>0]
    pf=rs[0].get('pricing_best_frame');pr=rs[pf-1] if pf else None
    g=max(vis,key=lambda r:r['share']) if vis else None
    mx=max([r['iou'] for r in vis],default=0.);mp=max([r['precision'] for r in served],default=0.)
    if not served: cat='refused'
    elif not vis: cat='never_visible'
    elif pr is not None and pr['visible'] and (pr['iou'] or 0)>=.5: cat='good_pricing_frame'
    elif mx>=.5: cat='right_obj_bad_pricing_frame'
    elif mx<.1 and mp<.2: cat='wrong_object'
    else: cat='weak_overlap'
    fv=[r['frame'] for r in vis];fv1=[r['frame'] for r in vis if r['share']>=.001]
    fs=[r['frame'] for r in vis if (r['iou'] or 0)>=.3];fp=[r['frame'] for r in vis if max(r['iou'] or 0,r['deployed_best_iou'])>=.3]
    O[key]=dict(cat=cat,cls=rs[0]['class'],ds=rs[0]['dataset'],cap=rs[0]['capture'],pool_any=any(r['deployed_best_iou']>=.5 for r in vis),
        max_pool=max([r['deployed_best_iou'] for r in vis],default=0.),g_share=g['share'] if g else 0.,nvis=len(vis),
        zero_cand_all=all(r['deployed_candidate_count']==0 for r in vis) if vis else True,
        first_vis=min(fv) if fv else None,first_vis1=min(fv1) if fv1 else None,first_served=min(fs) if fs else None,first_pool=min(fp) if fp else None,
        nserved_ok=len(fs),npool_ok=len(fp),nvis1=len(fv1))
byrow=collections.defaultdict(list)
for (row,obj),o in O.items(): byrow[row].append(o)
N=len(byrow)
g=collections.defaultdict(list)
for row,os_ in byrow.items():
    w=min(os_,key=lambda o:ORDER.index(o['cat']))
    if w['cat'] in('wrong_object','refused'): g[(w['cls'],)].append((row,w))
print('GAP SHARE BY CLASS of the worst operand (rows whose worst operand is wrong_object/refused); total rows',sum(len(v) for v in g.values()))
tot=0
for k,v in sorted(g.items(),key=lambda kv:-sum(sc[('A2_gt_masks',r)]-sc[('A0_deployed',r)] for r,_ in kv[1]))[:28]:
    s=100*sum(sc[('A2_gt_masks',r)]-sc[('A0_deployed',r)] for r,_ in v)/N;tot+=s
    print('   %-16s rows=%3d A0=%.1f A2=%.1f gap_pts=%.2f cum=%.2f pool_any_false=%d zero_cand_all=%d ds=%s'%(k[0],len(v),100*np.mean([sc[('A0_deployed',r)] for r,_ in v]),100*np.mean([sc[('A2_gt_masks',r)] for r,_ in v]),s,tot,sum(not o['pool_any'] for _,o in v),sum(o['zero_cand_all'] for _,o in v),dict(collections.Counter(o['ds'] for _,o in v))))
def gap(rows): return 100*sum(sc[('A2_gt_masks',r)]-sc[('A0_deployed',r)] for r in rows)/N
sel=[row for row,os_ in byrow.items() if min(os_,key=lambda o:ORDER.index(o['cat']))['cat'] in('wrong_object','refused')]
a=[row for row in sel if all(o['pool_any'] for o in byrow[row] if o['cat'] in('wrong_object','refused'))]
b=[row for row in sel if not all(o['pool_any'] for o in byrow[row] if o['cat'] in('wrong_object','refused'))]
print('wrong_object/refused rows: selection-fixable (pool has every bad operand at IoU>=.5 somewhere) rows=%d gap=%.2f | proposal-missing rows=%d gap=%.2f'%(len(a),gap(a),len(b),gap(b)))
bad=[o for o in O.values() if o['cat'] in('wrong_object','refused')]
print('bad operands',len(bad),'pool_any False',sum(not o['pool_any'] for o in bad),'max_pool bands',collections.Counter('0' if o['max_pool']==0 else '<.3' if o['max_pool']<.3 else '.3-.5' if o['max_pool']<.5 else '>=.5' for o in bad))
print('  bad & pool_any False: g_share quantiles',np.round(np.quantile([o['g_share'] for o in bad if not o['pool_any']],[.1,.25,.5,.75,.9]),4),'nvis q',np.quantile([o['nvis'] for o in bad if not o['pool_any']],[.1,.5,.9]),'classes',collections.Counter(o['cls'] for o in bad if not o['pool_any']).most_common(25))
print('  bad & pool_any True: g_share quantiles',np.round(np.quantile([o['g_share'] for o in bad if o['pool_any']],[.1,.25,.5,.75,.9]),4),'classes',collections.Counter(o['cls'] for o in bad if o['pool_any']).most_common(25))
print('distinct names',len({o['cls'] for o in O.values()}),'names with any pool_any False operand',len({o['cls'] for o in O.values() if not o['pool_any']}))
al=list(O.values())
def rate(f,items): 
    v=[f(o) for o in items if f(o) is not None];return '%.3f (n=%d)'%(np.mean(v),len(v))
print('FIRST-SEEN (operand level, IoU>=.3 as seen): served first frame == GT first visible frame',rate(lambda o:None if o['first_vis'] is None else float(o['first_served']==o['first_vis']),al),'| vs GT first frame with share>=0.1%',rate(lambda o:None if o['first_vis1'] is None else float(o['first_served']==o['first_vis1']),al),'| pool oracle',rate(lambda o:None if o['first_vis1'] is None else float(o['first_pool']==o['first_vis1']),al),'| served within +-1',rate(lambda o:None if o['first_vis1'] is None else float(o['first_served'] is not None and abs(o['first_served']-o['first_vis1'])<=1),al),'| pool within +-1',rate(lambda o:None if o['first_vis1'] is None else float(o['first_pool'] is not None and abs(o['first_pool']-o['first_vis1'])<=1),al))
print('FRAME RECALL (visible share>=0.1%): served IoU>=.3 frames / visible frames %.3f ; pool %.3f'%(sum(o['nserved_ok'] for o in al)/sum(o['nvis1'] for o in al),sum(o['npool_ok'] for o in al)/sum(o['nvis1'] for o in al)))
