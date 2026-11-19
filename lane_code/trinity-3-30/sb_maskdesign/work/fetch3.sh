D=/scratch/jjyeung/orch_n30/sb_maskfail; K=/scratch/jjyeung/orch_n30/sb_kbox4
echo "=== NOW $(date -u)"; ls -la $D/out | head -30; cat $D/STATUS.md
echo "=== ANALYSIS"
cat > /tmp/sb_maskdesign_obj_analysis.py <<'PYEOF'
import json,collections,sys,gzip
import numpy as np
D='/scratch/jjyeung/orch_n30/sb_maskfail/out/'
recs=json.load(open(D+'MASKFAIL.json'))['records']
ops=collections.defaultdict(list)
for r in recs: ops[(r['row'],r['object'])].append(r)
thr=np.linspace(.5,.95,10)
def mra(p,l):
    if p is None: return 0.
    return float(np.mean(abs(p-l)/l<=1-thr+1e-12))
sc={}
with open('/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/PER_ITEM.jsonl') as f:
    for line in f:
        if '"A0_deployed"' in line or '"A2_gt_masks"' in line or '"fused_cf"' in line:
            r=json.loads(line)
            if r['arm'] in('A0_deployed','A2_gt_masks','fused_cf'): sc[(r['arm'],r['row_id'])]=(mra(r['prediction'],r['label']),r['prediction'] is None,r['label'])
rows=sorted({k[0] for k in ops})
a0=np.mean([sc[('A0_deployed',i)][0] for i in rows]);a2=np.mean([sc[('A2_gt_masks',i)][0] for i in rows])
print('PARITY rows',len(rows),'A0 %.2f A2 %.2f'%(100*a0,100*a2),'fused_cf n',sum(1 for k in sc if k[0]=='fused_cf'))
O={}
for key,rs in ops.items():
    rs=sorted(rs,key=lambda r:r['frame']);vis=[r for r in rs if r['visible'] and r['valid']]
    served=[r for r in rs if r['served_area']>0]
    pf=rs[0].get('pricing_best_frame');pr=rs[pf-1] if pf else None
    g=max(vis,key=lambda r:r['share']) if vis else None
    mx=max([r['iou'] for r in vis],default=0.);mp=max([r['precision'] for r in served],default=0.)
    if not served: cat='refused'
    elif not vis: cat='never_visible'
    elif pr is not None and pr['visible'] and (pr['iou'] or 0)>=.5: cat='good_pricing_frame'
    elif mx>=.5: cat='right_obj_bad_pricing_frame'
    elif mx<.1 and mp<.2: cat='wrong_object'
    else: cat='weak_overlap'
    O[key]=dict(cat=cat,nvis=len(vis),nserved=len(served),mx=mx,cls=rs[0]['class'],ds=rs[0]['dataset'],cap=rs[0]['capture'],
        pool_any=any(r['deployed_best_iou']>=.5 for r in vis),npool=sum(r['deployed_best_iou']>=.5 for r in vis),
        pool_g=(g['deployed_best_iou']>=.5) if g else False,g_share=g['share'] if g else 0.,g_iou=(g['iou'] or 0.) if g else 0.,g_kind=g['failure_kind'] if g else None,
        p_share=pr['share'] if pr else 0.,p_iou=(pr['iou'] or 0.) if pr and pr['visible'] else 0.,p_kind=pr['failure_kind'] if pr else None,p_is_g=(pr is not None and g is not None and pr['frame']==g['frame']),
        ncorrect=sum((r['iou'] or 0)>=.5 for r in vis),zero_pool=all(r['deployed_best_iou']==0 for r in vis) if vis else True,
        max_pool=max([r['deployed_best_iou'] for r in vis],default=0.),sel=rs[0]['selected_candidate_id'] is not None)
print('OPERANDS',len(O),'unique',len({(o['cap'],k[1]) for k,o in O.items()}))
def tab(title,keyf,items):
    c=collections.Counter(keyf(o) for o in items);n=len(items)
    print('--',title,' '.join('%s=%d(%.1f%%)'%(k,v,100*v/n) for k,v in sorted(c.items(),key=lambda kv:-kv[1])))
allo=list(O.values())
tab('operand category',lambda o:o['cat'],allo)
for ds in ['arkitscenes','scannet','scannetpp']: tab('  '+ds,lambda o:o['cat'],[o for o in allo if o['ds']==ds])
tab('pool has IoU>=.5 cand in any visible frame',lambda o:o['pool_any'],allo)
tab('pool has IoU>=.5 cand at largest-GT frame',lambda o:o['pool_g'],allo)
tab('pool zero-overlap in every visible frame',lambda o:o['zero_pool'],allo)
for c in ['refused','wrong_object','weak_overlap','right_obj_bad_pricing_frame','good_pricing_frame']:
    it=[o for o in allo if o['cat']==c]
    if it:
        tab(c+' | pool_any',lambda o:o['pool_any'],it);tab(c+' | pool_at_g',lambda o:o['pool_g'],it);tab(c+' | pricing frame kind',lambda o:o['p_kind'],it);tab(c+' | pricing is largest-GT frame',lambda o:o['p_is_g'],it)
        print('   median nvis %.0f nserved %.0f ncorrect %.0f g_share %.4f p_share %.4f max_pool %.2f'%tuple(np.median([o[k] for o in it]) for k in['nvis','nserved','ncorrect','g_share','p_share','max_pool']))
print('share ratio pricing/largest-GT frame, good_pricing_frame ops: quantiles',np.round(np.quantile([o['p_share']/max(o['g_share'],1e-9) for o in allo if o['cat']=='good_pricing_frame'],[.1,.25,.5,.75,.9]),3))
print('nvis quantiles',np.quantile([o['nvis'] for o in allo],[0,.1,.25,.5,.75,.9,1]),'nserved quantiles',np.quantile([o['nserved'] for o in allo],[0,.1,.25,.5,.75,.9,1]),'ncorrect q',np.quantile([o['ncorrect'] for o in allo],[0,.1,.25,.5,.75,.9,1]),'npool q',np.quantile([o['npool'] for o in allo],[0,.1,.25,.5,.75,.9,1]))
# row level
byrow=collections.defaultdict(list)
for (row,obj),o in O.items(): byrow[row].append(o)
def rowtab(title,keyf):
    g=collections.defaultdict(list)
    for row,os_ in byrow.items(): g[keyf(os_)].append(row)
    print('==',title)
    for k,v in sorted(g.items(),key=lambda kv:-len(kv[1])):
        x0=np.mean([sc[('A0_deployed',i)][0] for i in v]);x2=np.mean([sc[('A2_gt_masks',i)][0] for i in v]);xf=np.mean([sc[('fused_cf',i)][0] for i in v]) if ('fused_cf',v[0]) in sc else float('nan')
        print('   %-45s rows=%4d A0=%.1f A2=%.1f fusedGT=%.1f gap_share=%.2f pts (A2-A0)*n/N, refusalsA0=%d'%(str(k),len(v),100*x0,100*x2,100*xf,100*(x2-x0)*len(v)/len(byrow),sum(sc[('A0_deployed',i)][1] for i in v)))
rowtab('rows by #operands with good pricing frame',lambda os_:sum(o['cat']=='good_pricing_frame' for o in os_))
rowtab('rows by worst operand category',lambda os_:min((o['cat'] for o in os_),key=['refused','never_visible','wrong_object','weak_overlap','right_obj_bad_pricing_frame','good_pricing_frame'].index))
rowtab('rows by (both pool_any)',lambda os_:all(o['pool_any'] for o in os_))
rowtab('rows by (both pool at largest-GT frame)',lambda os_:all(o['pool_g'] for o in os_))
rowtab('rows by dataset',lambda os_:os_[0]['ds'])
rowtab('good-pricing rows: both pricing frames are the largest-GT frame',lambda os_:('goodboth',all(o['p_is_g'] for o in os_)) if all(o['cat']=='good_pricing_frame' for o in os_) else 'n/a')
rowtab('good-pricing rows by min pricing IoU band',lambda os_:('goodboth','iou>=.8' if min(o['p_iou'] for o in os_)>=.8 else 'iou .65-.8' if min(o['p_iou'] for o in os_)>=.65 else 'iou .5-.65') if all(o['cat']=='good_pricing_frame' for o in os_) else 'n/a')
# frame-level
vis=[r for r in recs if r['visible'] and r['valid']]
print('FRAMES visible',len(vis))
np_=[r for r in vis if r['failure_kind']=='no_proposal']
print('no_proposal frames',len(np_),'served nonempty',sum(r['served_area']>0 for r in np_),'zero candidates for the name in frame',sum(r['deployed_candidate_count']==0 for r in np_),'teacher zero cands',sum(r['teacher_candidate_count']==0 for r in np_ if r['teacher_best_iou'] is not None),'teacher overlap>0',sum((r['teacher_best_iou'] or 0)>0 for r in np_))
print('  no_proposal served-nonempty dominant classes',collections.Counter((r['class'],r['dominant_class']) for r in np_ if r['served_area']>0).most_common(12))
om=[r for r in vis if r['failure_kind']=='omitted_selection']
print('omitted frames',len(om),'by operand cat',collections.Counter(O[(r['row'],r['object'])]['cat'] for r in om).most_common(),'pool>=.5 in frame',sum(r['deployed_best_iou']>=.5 for r in om))
wc=[r for r in vis if r['failure_kind']=='wrong_class'];print('wrong_class pairs',collections.Counter((r['class'],r['dominant_class']) for r in wc).most_common(15))
ot=[r for r in vis if r['failure_kind']=='other_mask_error'];print('other: precision q',np.round(np.quantile([r['precision'] for r in ot],[.1,.25,.5,.75,.9]),2),'iou q',np.round(np.quantile([r['iou'] for r in ot],[.1,.25,.5,.75,.9]),2),'dominant is target',sum(r['dominant_id']==r['instance'] for r in ot),'dominant None',sum(r['dominant_id'] is None for r in ot))
orc=[max(r['iou'],r['deployed_best_iou']) for r in vis]
print('oracle per-frame pool IoU mean %.3f rate>=.5 %.3f | served mean %.3f rate %.3f'%(np.mean(orc),np.mean(np.array(orc)>=.5),np.mean([r['iou'] for r in vis]),np.mean([r['iou']>=.5 for r in vis])))
for b in ['<0.5%','0.5-1%','1-5%','5-20%','>20%']:
    v=[r for r in vis if r['share_bin']==b];print('   share',b,'n',len(v),'pool>=.5 %.3f'%np.mean([max(r['iou'],r['deployed_best_iou'])>=.5 for r in v]),'pool zero %.3f'%np.mean([r['deployed_best_iou']==0 for r in v]),'cand count mean %.2f'%np.mean([r['deployed_candidate_count'] for r in v]))
print('cand count over visible: mean %.2f zero-cand share %.3f max %d'%(np.mean([r['deployed_candidate_count'] for r in vis]),np.mean([r['deployed_candidate_count']==0 for r in vis]),max(r['deployed_candidate_count'] for r in vis)))
ab=[r for r in recs if r['valid'] and not r['visible']];print('absent frames',len(ab),'served nonempty (false mask on absent frame)',sum(r['served_area']>0 for r in ab),'cands present in absent frame',sum(r['deployed_candidate_count']>0 for r in ab))
# class-level operand table
cl=collections.defaultdict(list)
for o in allo: cl[o['cls']].append(o)
print('CLASS operand-level: n, good_pricing%, refused%, wrong_object%, pool_any%, zero_pool%')
for k,v in sorted(cl.items(),key=lambda kv:-len(kv[1]))[:40]:
    n=len(v);print('   %-18s n=%3d good=%.0f refused=%.0f wrongobj=%.0f weak=%.0f rightbad=%.0f pool_any=%.0f zero_pool=%.0f'%(k,n,*[100*np.mean([o['cat']==c for o in v]) for c in ['good_pricing_frame','refused','wrong_object','weak_overlap','right_obj_bad_pricing_frame']],100*np.mean([o['pool_any'] for o in v]),100*np.mean([o['zero_pool'] for o in v])))
names=collections.Counter((r['object'],r['class']) for r in recs if r['frame']==1)
print('name!=class examples',[(k,v) for k,v in names.most_common(400) if k[0]!=k[1]][:25],'n name==class',sum(v for k,v in names.items() if k[0]==k[1]),'n differ',sum(v for k,v in names.items() if k[0]!=k[1]))

PYEOF
OMP_NUM_THREADS=4 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python /tmp/sb_maskdesign_obj_analysis.py 2>&1 | head -c 60000
echo "=== LADDER"; head -c 7000 $K/out/box_ladder/LADDER_TRAIN.txt
echo "=== REPORT"; [ -f $D/out/MASKFAIL_REPORT.md ] && head -c 20000 $D/out/MASKFAIL_REPORT.md
[ -f $D/out/FIRST_TABLE.md ] && cat $D/out/FIRST_TABLE.md
