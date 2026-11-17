import json, sys, sqlite3, collections, gzip
sys.path.insert(0, '/scratch/jjyeung/orch_n30/r1_pkt/work/tree')
from student_pilot.type_mix import family, allocate
off={o['qid'] for o in json.load(open('my_offenders.json'))}
div=json.load(open('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json'))
hq=set(div['heldout_qids']); hg=set(div['heldout_group_ids']); print('heldout lists', div['heldout_scenes'], div['heldout_group_ids'], len(hq))
from student_pilot.division import physical_group
conn=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1',uri=True)
new=collections.Counter(); old=collections.Counter(); bad=0; offheld=collections.Counter()
for (t,) in conn.execute('SELECT row FROM rows ORDER BY i'):
    r=json.loads(t); f=family(r,'vqa'); old[f]+=1
    g=physical_group(r['dataset'],r['scene'])
    if r['qid'] in off:
        offheld['grp_in_heldout']+= g in hg; offheld['grp_in_train_ids']+= g in set(div['train_group_ids']); continue
    new[f]+=1
    if r['qid'] in hq or g in hg: bad+=1
print('admitted rows checked vs heldout_qids/group_ids violations', bad, 'offenders group membership', dict(offheld))
cfg=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/config.json'))
pol=cfg['type_mix']['streams']['vqa']; cells=json.load(open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/FIX10_CELLS.json'))
for c in cells:
    fam=c['family']; e=new.get(fam,0)
    ok = pol['cells'][fam]['cents'] <= e*400//1000
    print(f"{fam:28s} old {old.get(fam,0):6d}/{c['old_eligible']:6d} new {e:6d}/{c['eligible']:6d} cell {pol['cells'][fam]['cents']:5d} cap {e*400//1000:6d} {'OK' if ok else 'VIOLATION'} match={old.get(fam,0)==c['old_eligible'] and e==c['eligible']}")
print('other families', {k:v for k,v in new.items() if k not in pol['cells']})
print('sum cents', sum(v['cents'] for v in pol['cells'].values()))
oldpol=json.loads(json.dumps(pol)); oldpol['cells']['room']['cents']=172; oldpol['cells']['direction']['cents']=3117
eff,tab=allocate(oldpol,dict(new),1000,4); print('sealed allocate(old cells,new counts):', {n:eff.get(n,{}).get('cents',0) for n in ('room','direction')}, 'equals config cells:', all(eff.get(n,{}).get('cents',0)==pol['cells'][n]['cents'] for n in pol['cells']))
eff2,tab2=allocate(pol,dict(new),1000,4); print('allocate(new cells): cuts', {n:v['cut_cents'] for n,v in tab2.items() if v['cut_cents']}, 'refill', {n:v['refill_cents'] for n,v in tab2.items() if v['refill_cents']})
keys={json.loads(l)['row_key'] for l in open('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/records/n.json')}
from student_pilot.row_removals import row_keys
up='/scratch/jjyeung/orch_n30/r1_pkt/out/units/packed.jsonl'
n=0; hit=0
for l in open(up):
    if l.strip(): n+=1; hit+= bool(row_keys(json.loads(l)) & keys)
print('unit rows', n, 'matching new list', hit)
