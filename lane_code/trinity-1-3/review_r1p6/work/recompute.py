import json, sys, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/r1_pkt/work/tree')
from student_pilot.p3_provenance import file_pin, pinned
from student_pilot.carrier_c1_data import _source_lines
from student_pilot.row_removals import Removals, row_keys
from student_pilot.s1_exclusions import Exclusions
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx/k/'
src=file_pin('/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json')
div=json.load(open(pinned(dict(path='/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json',sha256='0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad'))))
train,held=set(div['train_scenes']),set(div['heldout_scenes'])
cfg=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json'))
inh=[]
for v in cfg['remove_files'][:6]:
    name=v['path'].rsplit('/',1)[1]; p=dict(v); p['path']=K+name; inh.append(p)
newpin=dict(path='/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json',sha256='02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411')
newkeys={json.loads(l)['row_key'] for l in open(newpin['path']) if l.strip()}
print('cfg remove_files', len(cfg['remove_files']), 'newkeys', len(newkeys))
def ex(): return Exclusions(file_pin(K+'dev_scene_exclusions.json'), file_pin(K+'benchmark_scene_exclusions.json'))
print('cfg exclusion pins', cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
sf=ex()
with _source_lines(src, True, 'vqa') as h:
    sf.expect('vqa', (json.loads(l) for l in h), dict(source=src, source_receipt=True))
rem=Removals(inh); rem2=Removals(inh+[newpin])
seen=set(); off=[]; total=0; filt=0; inh_removed=0
seen2=set(); viol2=0; kept2=0; new_hits=[]; any_new_match=[]; heldhits=collections.Counter()
with _source_lines(src, True, 'vqa') as h:
    for i,l in enumerate(h):
        row=json.loads(l); total+=1
        if newkeys & row_keys(row): any_new_match.append((i,row['qid']))
        if not sf.keep(row,'vqa'): filt+=1; continue
        if rem.keep(row):
            sc=row['dataset']+'/'+row['scene']
            if sc not in train or sc in held or row['qid'] in seen:
                off.append(dict(i=i,qid=row['qid'],row_key=row.get('row_key'),scene=sc,dup=row['qid'] in seen,inheld=sc in held,inheldq=row['qid'] in set(div['heldout_qids']),pool=row.get('pool'),type=row.get('question_type')))
            seen.add(row['qid'])
        else: inh_removed+=1
        if rem2.keep(row):
            sc=row['dataset']+'/'+row['scene']
            if sc not in train or sc in held or row['qid'] in seen2: viol2+=1
            seen2.add(row['qid']); kept2+=1
print(dict(total=total, scene_filtered=filt, inherited_removed=inh_removed, offenders=len(off), dups=sum(o['dup'] for o in off), in_heldout_scene=sum(o['inheld'] for o in off), in_heldout_qid=sum(o['inheldq'] for o in off)))
offkeys=set()
for o in off: offkeys|={o['qid']} | ({o['row_key']} if o['row_key'] else set())
print('offender qid==row_key all:', all(o['qid']==o['row_key'] for o in off))
print('newkeys == offender qids:', newkeys=={o['qid'] for o in off}, 'newkeys-off', len(newkeys-{o['qid'] for o in off}), 'off-new', len({o['qid'] for o in off}-newkeys))
print('rows in full store matching new list (pre-filter):', len(any_new_match), 'distinct qids', len({q for _,q in any_new_match}))
print('with new list: kept', kept2, 'violations', viol2, 'new list removed', rem2.removed[-1], 'matches', rem2.matches[-1])
print('by pool/type', collections.Counter(f"{o['pool']}::{o['type']}" for o in off))
print('scenes', len({o['scene'] for o in off}), 'datasets', collections.Counter(o['scene'].split('/')[0] for o in off))
b=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/FIX10_OFFENDERS.json'))
print('builder rows match mine:', sorted((r['i'],r['qid']) for r in b['rows'])==sorted((o['i'],o['qid']) for o in off))
json.dump(off, open('my_offenders.json','w'))
