import importlib.util,json,resource,time
from pathlib import Path
p=Path(__file__).with_name('test_jn7.py')
spec=importlib.util.spec_from_file_location('checks',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
for _ in range(5):
    if (m.W/'source.after.json').exists(): break
    time.sleep(60)
else: raise RuntimeError('main tests did not finish')
m.RESULTS.extend(json.loads((m.W/'results.json').read_text()))
root=m.W/'x/n';bad=m.W/'x/s/n';good=m.W/'x/c/n'
for v in ('6','7'):
    m.run_one('seal_pfail',v,bad,4,'seal',1,'v.py refusal',pfail='fail')
    m.run_one('g2_pfail',v,root,2,'gpu',3,'fewer than 4 H100; stop before staging',pfail='fail')
    m.run_one('normal_pfail',v,good,4,'child',23,'job.sh exit',pfail='fail')
    m.run_one('term_pfail',v,good,4,'child',37,'job.sh exit',pfail='fail',sig='TERM')
    m.run_one('usr1_pfail',v,good,4,'child',38,'job.sh exit',pfail='fail',sig='USR1')
    m.run_one('term_final_iofail',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',pfail='iofail',finalsig='TERM')
    m.run_one('usr1_final_iofail',v,root,0,'gpu',3,'fewer than 4 H100; stop before staging',pfail='iofail',finalsig='USR1')
print('PASS: '+str(len(m.RESULTS))+' total cases',flush=True)
