"""Local H build tests: no networking, GPU, placement or deletion."""
import argparse
import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path
import build_h
from build_support import read_tar,write_tar,bundle_of
HERE=Path(__file__).resolve().parent
A4=Path(os.environ.get('H_TEST_SOURCE',str(HERE.parent/'validation/A4.tgz')))
SOURCE_SHA='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'
def sha(b):return hashlib.sha256(b).hexdigest()
def extract(raw,root):
    for m,d in read_tar(raw):
        assert not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)
def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);a=p.parse_args();w=Path(a.work)
    assert str(w.resolve()).startswith(str(HERE.parent)+'/');w.mkdir(parents=True,exist_ok=False)
    os.environ['KROOT']=str(w/'K')
    raw=A4.read_bytes();assert sha(raw)==SOURCE_SHA
    before=dict((m.name,d) for m,d in read_tar(raw));oldpf=dict((m.name,d) for m,d in read_tar(before['0.tgz']))
    results={}
    for step in (200,400,544):
        sw=w/str(step);sw.mkdir()
        report=build_h.build(sw/'stage',A4,SOURCE_SHA,HERE/('bind_H%d.json'%step),HERE/'TIMING_H.json','04:00:00')
        raw=(Path(report['delivery_dir'])/'1.tgz').read_bytes();extract(raw,sw/'package')
        after=dict((m.name,d) for m,d in read_tar(raw));extract(after['0.tgz'],sw/'src');pf=dict((m.name,d) for m,d in read_tar(after['0.tgz']))
        (sw/'original_scorers.py').write_bytes(oldpf['h1eval/scorers.py'])
        plan=json.loads(pf['9.json']);assert report['budget_fits'] and report['budget_gpu_seconds']==11038
        if step==200:
            assert before['a/4.py']==after['a/4.py']
            assert plan['export_binding']==json.loads(oldpf['9.json'])['export_binding']
        for n in oldpf:
            if n.startswith(('b/','tree/','rows/','auth/')):assert pf[n]==oldpf[n],n
        assert before['a/7.py']==after['a/7.py']
        assert json.loads(before['a/0.json'])['archives']==json.loads(after['a/0.json'])['archives']
        batch=after['BATCH.sh'];assert batch.count(b'trap fin EXIT')==1 and batch.count(b"trap 'kill -USR1")==1
        bundle=dict((m.name,d) for m,d in read_tar(bundle_of(batch)[1]));assert bundle['7.py']==after['a/6.py'] and bundle['0.json']==after['0.json']
        for n in ['3.py','a/4.py','a/5.py','a/6.py','a/7.py']:ast.parse(after[n].decode())
        subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-B',str(HERE/'plan_h.py'),str(sw)],check=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',XDG_CACHE_HOME=str(w/'cache')))
        results[str(step)]=dict(passed=True,build=report,planning=json.loads((sw/'PLANNING.json').read_text()))
    (w/'TEST_RESULTS.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n')
    print('All H builds passed')
if __name__=='__main__':main()
