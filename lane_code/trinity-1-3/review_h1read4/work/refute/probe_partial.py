import sys, json, os, tarfile, random, string, hashlib
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_h1read4/work/h1read')
sys.path[:0]=[str(K/'kit/launcher')]
import chain_save as A, orchard_results as R
cfg=json.load(open('p4d/CONFIG.json'))
src=Path('psrc'); res=src/'a7/a0/results/0'; res.mkdir(parents=True); (src/'metadata').mkdir()
rnd=random.Random(1)
types=list(cfg['spec']['population']['a7']['types'])
with open(res/'g0.jsonl','wb') as f:
    for i in range(300):
        row=dict(key='devrows:x%d'%i,status='complete',question_type=types[i%len(types)],
                 raw_generation=''.join(rnd.choice(string.ascii_letters) for _ in range(20000)))
        f.write((json.dumps(row)+'\n').encode())
    f.write(json.dumps(dict(key='devrows:x1',status='complete',question_type=types[1])).encode()+b'\n')  # duplicate
    f.write(b'{"key":"devrows:torn","status":"compl')  # torn tail
(res/'summary_a0.json').write_text('{"parity_pass": tru')  # torn summary
out=Path('pout'); out.mkdir()
limit=19900000-1
info=A.pack_partial(src,out/'p.tar.gz',cfg,limit)
size=(out/'p.tar.gz').stat().st_size
j=info['journals']['a7/a0/results/0/g0.jsonl']
print('size',size,'<cap',size<limit,'truncated',info['truncated'],'lines',j['lines'],'retained',j['retained_lines'],'invalid',j['invalid_lines'],'finished',j['finished_items'],'fam',info['families']['a7']['finished_items'])
with tarfile.open(out/'p.tar.gz') as t:
    names=t.getnames(); print(sorted(n for n in names if not n.startswith('metadata')))
    g=t.extractfile('a7/a0/results/0/g0.jsonl').read(); print('retained ends newline',g.endswith(b'\n'),'all parse',all(json.loads(l) for l in g.splitlines()))
    p=json.load(t.extractfile('PARTIAL.json')); print('complete',p['complete'],'excluded',p.get('excluded'),'types0', 'object_abs_distance' in p['families']['a7']['types'])
arch=out/'p.tar.gz'
h=hashlib.sha256(arch.read_bytes()).hexdigest()
rec=dict(schema='a3',synthetic=False,plan_sha256=cfg['plan_sha256'],status='PARTIAL',complete=False,returncode=1,
         conflicting_terminal_markers=False,archive=dict(name='result.tar.gz',bytes=size,sha256=h),archive_bytes=size,archive_sha256=h)
try: R.verify(rec,arch,cfg['plan_sha256']); print('DEFAULT VERIFY ACCEPTED PARTIAL (bad)')
except Exception as e: print('default verify rejects:',e)
try: R.verify(rec,arch,cfg['plan_sha256'],allow_partial=True); print('partial verify ok')
except Exception as e: print('partial verify error:',e)
rec2=dict(rec,status='COMPLETE',complete=True,returncode=0)
try: R.verify(rec2,arch,cfg['plan_sha256'],allow_partial=True); print('PARTIAL ARCHIVE PASSED AS COMPLETE (bad)')
except Exception as e: print('relabelled complete rejects:',e)
