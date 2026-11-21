import importlib.util,subprocess,sys,time,os,types
for _m in ('orchard_stage','orchard_results','chain_save'):sys.modules[_m]=types.ModuleType(_m)
from pathlib import Path
spec=importlib.util.spec_from_file_location('oj','/scratch/jjyeung/orch_n30/lever1_c/r1/out/review8_sources/orchard_job.py');J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
R=Path('/scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/real_cl2opr5g/j')
for case in ('without','with'):
    root=Path(f'/tmp/k5fix_{case}_{os.getpid()}');root.mkdir()
    (root/'bwrap').symlink_to('/usr/bin/bwrap');(root/'sj').symlink_to(R/'sj')
    if case=='with':
        for n in ('fsw','m/ap'):(root/n).mkdir(parents=True,exist_ok=True)
    argv=J.namespace(root)+['/scratch/jjyeung/b01ec87a6f29b/d/v/py','-I','-s','-B','-c','print(1)']
    t=time.time();p=subprocess.run(argv,capture_output=True,text=True,env=dict(PATH='/usr/bin:/bin'))
    print(case,'rc',p.returncode,'%.3fs'%(time.time()-t),'stderr:',p.stderr.strip()[:200].replace(str(root),'<root>'),'stdout:',p.stdout.strip())
