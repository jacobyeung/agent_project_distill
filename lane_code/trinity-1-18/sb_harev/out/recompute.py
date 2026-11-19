"""Read-only CPU audit. Run from the sb_harev workspace; writes out/RECOMPUTE.json only."""
import collections, hashlib, json, math, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {}
RESULTS = []
CMD = 'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/python3 out/recompute.py'

def read(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    b = p.read_bytes()
    INPUTS[str(p)] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
    return b.decode()

def js(path):
    return json.loads(read(path))

def jl(path):
    return [json.loads(s) for s in read(path).splitlines() if s.strip()]

def result(name, status, values, evidence, method, missing=None):
    RESULTS.append(dict(claim=name, status=status, values=values, evidence=evidence,
                        method=method, command=CMD, missing=missing or []))

def mra(pred, truth):
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    relative = abs(pred-truth)/abs(truth)
    return sum(relative < (100-theta)/100 for theta in range(50,100,5))/10

# Hash the review snapshots. Their source is recorded without re-reading NFS.
for p in sorted((ROOT/'inputs').glob('*.md')):
    read(p)
    prefix = '/data2/jjyeung/agent_project_data/'
    folder = 'distillation_orchestrator_20260918/orch_n30/events/sb_headacc/' if p.name.startswith(('KIT_SPEC_', '20261119T')) else 'distill_design/'
    INPUTS[str(p)]['source_path'] = prefix+folder+p.name
read('out/local_files.txt')

base = Path('/scratch/jjyeung/n30_mirror/tower_redecide/work')
label_path = '/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl'
labs = {r['id']:r for r in jl(label_path)}
rows=[]
for p in sorted((base/'reprice/caps_corrected').glob('*.json')):
    rows.extend(js(p)['items'])
gd_path='/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/PER_ITEM.jsonl'
gd=jl(gd_path)
for r in gd:
    if r['arm'].startswith('GD_') and r['type']=='object_abs_distance':
        r=dict(r)
        lab=labs[r['row_id']]
        if lab['convention']=='half': r['gt']=lab['corrected']
        rows.append(r)
scores={}
for split in ['train','heldout']:
    by=collections.defaultdict(dict)
    for r in rows:
        if r['type']=='object_abs_distance' and r['split']==split:
            by[r['arm']][r['row_id']]=r
    ids=sorted(by['GT'])
    arms={}
    for arm in ['GT','GD_reviewed','S4+G1','pi3x_native','da3_native']:
        vals=[mra(by[arm][i]['pred'],by[arm][i]['gt']) if i in by[arm] else 0. for i in ids]
        arms[arm]=100*statistics.mean(vals)
    both={}
    for arm in ['pi3x_native','da3_native']:
        keep=[i for i in ids if all(i in by[a] and by[a][i]['pred'] is not None and by[a][i]['refusal_code'] is None for a in [arm,'GD_reviewed'])]
        both[arm]={'n':len(keep),'gain':100*statistics.mean(mra(by[arm][i]['pred'],by[arm][i]['gt'])-mra(by['GD_reviewed'][i]['pred'],by['GD_reviewed'][i]['gt']) for i in keep)}
    scores[split]={'n':len(ids),'rooms':len({by['GT'][i]['room'] for i in ids}),'arms':arms,'both_answered':both}
result('K1 corrected GT-mask distance: 75.05 deployed, 91.99 GT; Pi3X 73.38, DA3 71.02','VERIFIED',scores,
       [str(base/'reprice/caps_corrected')+'/*.json:1',gd_path+': per row',label_path+': per row','HEAD:25,37'],
       'Recompute strict-threshold MRA from predictions and corrected labels; use every GT row, missing/refusals zero, then item-weighted mean. No stored MRA used.')
result('About 17 type points of geometry gap','VERIFIED',{'GT_minus_GD':scores['heldout']['arms']['GT']-scores['heldout']['arms']['GD_reviewed']},['HEAD:25'],
       'Subtract recomputed corrected held-out means. This contrast changes geometry; it does not isolate the single-view loss.')

manifest_path='/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
man=js(manifest_path)
mc={}
for split in ['train','heldout']:
    cs=[c for c in man['captures'] if c['k1_split']==split]
    ds=[(c,r) for c in cs for r in c['rows'] if r['type']=='object_abs_distance']
    mc[split]={'captures':len(cs),'distance_rows':len(ds),'distance_rooms':len({c['room'] for c,r in ds})}
result('Named K1 manifest has 296 captures','WRONG',{'captures':len(man['captures']),'splits':mc,'corrected_distance_rows':len(labs)},
       [manifest_path+': captures','tower_frames:9,17','box_ladder:18'],
       'Count captures and distance rows by k1_split in the exact named manifest. Use the registered PRIMARY_296 whitelist before pricing; do not invent exclusions.')

pres_path='/scratch/jjyeung/orch_n30/b11_presence/out/analysis/ANALYSIS_heldout.items.jsonl'
pres=jl(pres_path)
pv={}
for typ in ['obj_appearance_order','object_counting']:
    rr=[r for r in pres if r['type']==typ]
    keys=['I:head','direct','gt_program']+(['V:head_optlik'] if typ=='obj_appearance_order' else [])
    pv[typ]={'n':len(rr),'rooms':len({r['room'] for r in rr}),**{a:statistics.mean(r[a] for r in rr) for a in keys}}
result('Presence 32.9 vs 71.3; GT-presence counting 24.8','VERIFIED',pv,[pres_path+': each JSONL row','PRESENCE_PROBE_K1:7','HEAD:19,57'],
       'Reaggregate per-item scores by type. Appearance: 47/143 vs 102/143. GT-presence 24.8 belongs to counting, not appearance.')
read('/scratch/jjyeung/orch_n30/b11_presence/out/PRESENCE_PROBE.md')

rep_path='/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses/primary_296/REPORT.json'
rep=js(rep_path)
reprice=js(base/'reprice/REPRICE_TABLES.json')
result('Stored-label 60.4 predicted masks vs 68.0 GT masks','VERIFIED',
       {'predicted_answered_mra':100*rep['answered_mra'],'predicted_n':rep['answered_items'],'all_n':rep['heldout_items'],
        'GT_mask_reported_mra':reprice['stored/all/heldout']['arms']['GD_reviewed']['mean'],
        'difference_of_reported_means':reprice['stored/all/heldout']['arms']['GD_reviewed']['mean']-100*rep['answered_mra']},
       [rep_path, str(base/'reprice/REPRICE_TABLES.json'),'HEAD:26'],
       'Verify source-summary values and their denominators; this is not a paired instance-choice effect. Predicted uses 214 answered rows; GT uses 216.')
pose_path=base/'pose_k1/POSE_K1.json'
pose=js(pose_path)
pc=[r for r in pose['captures'] if all(a in r for a in ['GD','pi3x_native','da3_native'])]
pose_values={a:{m:100*statistics.mean(r[a][m] for r in pc if r[a][m] is not None) for m in ['turn_mra','move_mra','dir_acc']} for a in ['GD','pi3x_native','da3_native']}
pose_values['n_captures']=len(pc)
pose_values['reported_pair_medians']={a:v['rot_median_pairs'] for a,v in pose['summary']['all/all'].items()}
result('K1 camera DA3 1.78 vs G3T 2.72 degrees','VERIFIED',pose_values,[str(pose_path),'TOWER_REDECISION:54-61'],
       'Read exact saved pair medians and independently aggregate capture-level turn/move scores. Pair-level rotation arrays are not in this summary; pair medians are source-summary verification only.')

result('Fragment bucket arithmetic: fewer than 3 frames 55.4 vs 73.9; 142 gaps 61.8','VERIFIED',
       {'low_n':65+28,'low_mean_from_rounded_buckets':(65*54.2+28*58.2)/93,
        'high_n':28+21,'high_mean_from_rounded_buckets':(28*70.7+21*78.1)/49,
        'all_mean_from_rounded_buckets':(65*54.2+28*58.2+28*70.7+21*78.1)/142,
        'operand_count':2*142,'candidate_count_sum':23+57+204},['HEAD:26,34'],
       'Weighted means from cited rounded buckets only; independent per-item verification remains UNVERIFIABLE below.')
result('Camera loss shares 55% and 52%','VERIFIED',
       {'displacement_loss_percent':100*33*(100-55.5)/(150*(100-82.3)),
        'rotation_loss_percent':100*25*(100-23.6)/(150*(100-75.6))},['HEAD:29,39'],
       'Recompute shares from rounded counts and means; this verifies arithmetic only, not the absent camera predictions or a causal noise floor.')
result('Projected totals arithmetic','VERIFIED',
       {'VSI_distance_plus_frames':[.4+.25,1+.6],'ReVSI_room_distance_frames':[.7+.4+.3,2.1+1.1+.7],
        'object_ceiling_sum':[.5+1.5+2.5,.9+2.2], 'distance_3_to_8_type_VSI':[3/8,8/8],'distance_3_to_8_type_ReVSI':[3/7,8/7]},
       ['HEAD:15-22,31'],'Arithmetic only. Totals assume independent incremental gains, which the kits do not measure.')
result('Historical selector-mask route contrast','VERIFIED',{'relative_distance':59.1-61.0,'counting':54.4-71.1,'size':62.3-68.1},
       ['GT_CEILING_DECOMPOSITION:98-106'],'Subtract cited table cells; source-summary verification, not raw replay. Statistical tie for relative distance does not mean exact equality.')

missing_claims=[
 ('Selector margin <1: 50.0 (60) vs 70.4 (82); 204/284 candidates; chosen/proposed frames 3/9; 76 singleton operands; 19% boxes <0.3m; short gaps 39.5, 17/21 overestimates; step-200 repeats; 227/227 box rule',
  ['/scratch/jjyeung/orch_n30/sb_headacc/work/gapdiag.py','/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases/b1','/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/ret']),
 ('Camera raw noise-floor numbers: 6cm; 4.2%; 4cm on 16cm; ratios 1.00-1.02; 82.3/75.6; error-halving 91.7/83.2; every truth/frame-gap band',
  ['/scratch/jjyeung/orch_n30/sb_headacc/work/camdiag.py','/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/bases/b1']),
 ('Size 0.79 ratio and 50.7 vs 73.6 (58 name-within-room joins, not guaranteed same instance)',
  ['/scratch/jjyeung/orch_n30/swarm_an/work/verify/SIZE_BOXHEAD_JOIN.json']),
 ('GT-mask appearance 92.6, counting 98.1 and 37-to-98 oracle, single-view 8.8, fusion 1.6, scale 0.077/0.021/0.044, direction 81-83 vs 88, never-proposed 74/224 and +8.8',
  ['/scratch/jjyeung/orch_cd/gt_ceiling/work/out/DENSE_CB_013.json','/scratch/jjyeung/orch_cd/gt_ceiling/work/tp/prog_v2.py']),
 ('Predicted-mask relative distance -28.0, counting -14.2; 55.5 vs 46.5 route; ceilings +0.5/+0.9 size, +1.5/+2.2 relative, +1.0-to-2.5 appearance; 62/131 recoverable errors',
  ['/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py']),
]
for claim,paths in missing_claims:
    absent=[p for p in paths if not Path(p).exists()]
    result(claim,'UNVERIFIABLE',{'input_status':'MISSING'},['HEAD:9,17-29,34-40','R1_M200_TRACE_ANALYSIS:149,245'],
           'Named local files are absent; copied summary claims are not raw recomputation. The cited DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT record states the predicted pass is pending and supplies no -28.0 ROUTE result. The 2026-10-27 oracle has no exact filename in HEAD.',absent)

# Explicit source anchors for the review's implementation findings.
for p in [
 '/scratch/jjyeung/orch_n30/geo_k1/k1towers/decide.py',
 '/scratch/jjyeung/orch_n30/b04host3/reader_bs/e2e_reader/grounding.py',
 '/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_candidates.py',
 '/scratch/jjyeung/orch_n30/b04host3/lift_price/harness/lift_price.py',
 '/scratch/jjyeung/n30_mirror/tower_redecide/work/pose_k1.py']:
    read(p)
result('Gather uses the linker\'s own overlap rule','WRONG',{'linker_denominator':'min(len(a),len(b))','proposed_gather_denominator':'len(proposal)','counterexample':{'proposal_voxels':100,'seed_voxels':10,'intersection':10,'linker_overlap':1.,'gather_overlap':.1}},
       ['HEAD:45','box_ladder:34','/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/routed_candidates.py:141-149'],
       'Read overlap implementation; compare denominators. The linker also accepts a centre-distance condition that gather omits.')
result('G64 proxy reproduces own-depth scale','WRONG',
       {},['tower_frames:28'],
       'median(own/d32)*median(d32/d64) need not equal median(own/d64).')
# Find and record a minimal concrete counterexample (synthetic algebra, not benchmark data).
import itertools
for own in itertools.product([1,2,4],repeat=3):
    d32=(1,2,4)
    for d64 in itertools.product([1,2,4],repeat=3):
        a=statistics.median(o/d for o,d in zip(own,d32))
        b=statistics.median(x/y for x,y in zip(d32,d64))
        exact=statistics.median(o/d for o,d in zip(own,d64))
        if a*b!=exact:
            RESULTS[-1]['values']={'own_depth':own,'depth32':d32,'depth64':d64,'stored_scale':a,'median_depth32_over_depth64':b,'proxy_scale':a*b,'true_scale64':exact}
            break
    else: continue
    break

liftroot=Path('/scratch/jjyeung/orch_n30/b04host3/lift_price/harness')
liftvalues={}
for folder in ['out_lift_train','out_lift_train_v2']:
    pp=sorted((liftroot/folder).glob('*.json'))
    if not pp: continue
    byarm=collections.defaultdict(list)
    for p in pp:
        for r in js(p)['items']:
            if r['type']=='object_abs_distance': byarm[r['arm']].append(r)
    liftvalues[folder]={arm:{'n':len(rs),'rooms':len({r['room'] for r in rs}),
                            'mra':100*statistics.mean(mra(r['pred'],r['gt']) for r in rs)} for arm,rs in sorted(byarm.items())}
result('K1 lift variants: plain 28.6 and hull 39.1','WRONG',liftvalues,
       [str(liftroot)+'/out_lift_train*/: items','HEAD:36'],
       'Recompute MRA from saved predictions and stored labels: S4+G1 plain=28.001998, hull=38.781219 on 1001 rows. Correct rounded values are 28.0 and 38.8. Best=61.448551, bestspread=69.650350 and dep=69.780220 verify the other three values. Arm and item counts are explicit; these are S4+G1 GT-mask arms, not the deployed GD reference.')
read(liftroot/'AGG_TRAIN.txt')
read(liftroot/'AGG_TRAIN_v2.txt')
read(liftroot/'agg.py')
r0path='/scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl'
r0=jl(r0path)
result('R0-dev item counts','VERIFIED',{'items':len(r0),'scenes':len({r['scene'] for r in r0}),
       'types':dict(collections.Counter(r.get('question_type') for r in r0))},[r0path+': each JSONL row','object_route:9'],
       'Count exact input items by question_type and scene; no inference and no choice on item outcomes.')

selection=[
 ('box_ladder:6,25-30,35,48,51-52','Fusion-rule winner; gathered winner replaces A0','K1 train, followed by positive held-out gate','BLOCKING: held-out outcome affects adoption'),
 ('box_ladder:23,27','Oracle seed candidate and member-count tie break','K1 GT diagnostic labels, train and held-out','Oracle only; cannot deploy or select an oracle rung'),
 ('box_ladder:34,53','Gather acceptance, score/overlap constants and >=0.90 precision gate','Constants claimed inherited; precision evaluated on K1 train','Allowed train decision; inherited overlap formula differs'),
 ('box_ladder:39,54','Non-null selector fit; five room folds; A1-A0 >=4 work gate; adoption','K1 train and held-out sign','BLOCKING: held-out gate; also training contradicts no-training headline'),
 ('box_ladder:48','Replay agreement >=95%','Two train plus five held-out captures','Move actionable preflight/debugging to train-only'),
 ('box_ladder:55','Size >=63.3 screen','Held-out K1 ScanNet++ vs R0-dev 58.3 +5','BLOCKING: protected-set screening and cross-set comparator'),
 ('box_ladder:56','First-seen >=75% exact and >=90% within one screen','K1 train','Allowed train decision; not proof of item-level order accuracy'),
 ('box_ladder:57','Tower challenger under fusion','K1 train rows both answer','Allowed train decision; secondary denominator must not replace all-row score'),
 ('tower_frames:12,23','Use kit-1 winner; F32/F64/F64_fused/F64_flagged','K1 train; inherited kit-1 held-out gate','BLOCKING inherited selection; F64_fused overlaps rank-2 treatment'),
 ('tower_frames:19','Keep 64 poses/depth; stop B/C 64 arms otherwise','K1 train and held-out sign (lifting split unspecified)','BLOCKING held-out gate; geometry gate does not test SAM recall'),
 ('tower_frames:24','Select grounding frame arm','K1 train and one held-out sign','BLOCKING held-out gate'),
 ('tower_frames:27-29','Camera parity >=440/450; G64/DA3 native/DA3 ownscale replacement','dev-S1 routed 450 items, only locally available 64-frame captures','No new official item explicitly requested; scale proxy and unpinned subset block decision'),
 ('object_route:3,19,23','Use kit-1 rule/screens; run T64 if tower kit passes','K1 decisions including held-out gates','BLOCKING inherited protected-set selection'),
 ('object_route:26-27','Trace nearest-two candidates; fallback; appearance tie by proposal order','Per-item direct trace and predictions on R0-dev','Fixed inference choice, not a GT oracle; parser/tie semantics must freeze on train'),
 ('object_route:33-35,38','Route size, relative distance, appearance; license row build','R0-dev head-minus-direct intervals','BLOCKING: route selection on protected R0-dev; one look still selects'),
 ('object_route:36','Confirm object box or withdraw kit-1 PASS','R0-dev absolute-distance interval','BLOCKING: protected-set adoption/withdrawal'),
 ('object_route:37','T64 and DA3 secondary columns','R0-dev','Report-only explicitly; no selection intended'),
 ('object_route:41','Join/parsing >=250/279 and synthetic GT-order smoke','R0-dev traces and two K1 captures (split unspecified)','Freeze parsing on K1 train; GT-constructed order smoke is not an accuracy bar'),
 ('ROOM_HEAD_DESIGN:60,65-66,72-73,86-92','Reuse room kit PASS; row build; route redecision; label audit after FAIL/NEAR','K1 train plus R0-dev repeated gating; official ReVSI report-only','BLOCKING R0-dev selection; room event spec itself was outside this review'),
 ('GT_CEILING_DECOMPOSITION:93-96; DEVS1_PREDICTED_MASKS_ROUTE_TABLE_KIT:41','Historical fusion choice','Benchmark test scenes, then development rederivation; VSTI overlaps ScanNet val dev','Official-informed lineage must be disclosed; no new official read in these three kits'),
]
paths_to_check=[
 '/scratch/jjyeung/n30_mirror/gt_audit/K1_LABELS_CORRECTED.jsonl',
 '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449',
 '/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src',
 '/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py',
 '/scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl',
 '/scratch/jjyeung/orch_n30/b10_reserve/out/FRAMES_MANIFEST.json',
 '/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/data/caps_raw',
]
path_status={p:('PRESENT' if Path(p).exists() else 'MISSING') for p in paths_to_check}

result('Remaining unsupported headlines','UNVERIFIABLE',{
 'claims':['selector top-1 58.6 (record-supported only)','null 4.7%','scale oracle <=3 and global scale +0.8 to +1.8',
           'perfect dev-S1 gap 96.7 and universal calls 59.4 to 59.6','88/88 responses changed','room +0.7 to +2.1 probability about even',
           'first-seen 80% implies appearance +1.0 to +2.5','94 frames priced in object kit','GPU/CPU-hour forecasts'],
 'input_status':'MISSING; estimates have no measured pricing output'},['HEAD:14-31,38,65'],
 'The supplied design contains estimates and citations; no new pricing run exists. Object kit specifies 32/64, not 94 frames. No invented oracle filename or route output.',
 ['/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py'])

out={'verdict':'REJECT','command':CMD,'scope':'Read-only review; no GPU, network, Git, or source mutation. VERIFIED states its verification level in method; raw-unavailable claims are separately UNVERIFIABLE.',
     'inputs':INPUTS,'results':RESULTS,
     'selection_inventory':[dict(evidence=a,choice=b,items=c,assessment=d) for a,b,c,d in selection],
     'required_path_checks':path_status}
out['review_code']={'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(ROOT/'out/RECOMPUTE.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
for r in RESULTS:
    print(r['status'],r['claim'],json.dumps(r['values'])[:400])
