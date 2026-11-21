import sys,os,json,glob
OUT='/tmp/q_22c714e1_174134'; IN='/tmp/q_22c714e1'
def m(p): p=str(p); return OUT+p[len(IN):] if (p==IN or p.startswith(IN+'/')) else p
T=OUT+'/p/s'; sys.path.insert(0,T)
from student_pilot.p3_provenance import load,pinned
from student_pilot import r1_persisted
from student_pilot.ground_target_filter import TargetFilter
R=json.load(open(OUT+'/p/q/RESULT.json')); paths={e['sha256']:m(e['path']) for e in R['staged']}
with r1_persisted.scope(paths):
    q=load(OUT+'/p/q/c.json'); k=load('/tmp/a15_f8_174134/t/c1.json')
    prep=sorted(glob.glob(OUT+'/p/q/p/prepare_*'))[0]; pr=json.load(open(prep+'/pointing/receipt.json'))
    got=pr.get('target_filter',{}).get('settings')
    for tag,cfg in (('prepared config p/q/c.json (what prepare() reads)',q),('kit k/c.json before staging',k)):
        exp=TargetFilter(cfg.get('remove_files',()),shape_filter=True).settings()
        diff=sorted(x for x in set(exp)|set(got) if exp.get(x)!=got.get(x))
        print(tag,'| ground_target_filter',cfg.get('ground_target_filter'),'| settings equal',exp==got,'| differing keys',diff)
        if 'removals' in diff: print('   removals[0] expected',json.dumps(exp['removals'][0])[:200],'| receipt',json.dumps(got['removals'][0])[:200])
    print('remove_files sha256 equal (prepared vs kit):',[p['sha256'] for p in q['remove_files']]==[p['sha256'] for p in k['remove_files']])
    print('prepared config streams.vqa',json.dumps(q['streams']['vqa'])[:160])
print('DONE')
