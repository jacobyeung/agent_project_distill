"""Check generated shell/Python compatibility, submit guards and operator completion."""
import ast
import copy
import hashlib
import io
import json
import os
import re
import runpy
import subprocess
import sys
import tarfile
import types
from pathlib import Path

H=Path(__file__).resolve().parent
W=H/'rehearsal';V=W/'verify';V.mkdir()
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
P=Path(read(W/'RESULT.json')['package']);pub=read(P/'0.json')
pyfiles=[]
def source(name,raw):
    p=V/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw if isinstance(raw,bytes) else raw.encode());pyfiles.append(p)
for n in ('build_r11.py','gen600c.py','dry2_c600.py','make_read_plan_c600.py','in/dryres2.py'):
    source(n,(H/n).read_bytes())
scripts=['o_%s_c600.sh'%n for n in ('build','place_pull_fill','cpu','sub','fetch')]
for n in scripts:
    subprocess.run(['bash','-n',str(H/n)],check=True)
    text=(H/n).read_text()
    for i,block in enumerate(re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE",text,re.S)):
        source(n+'.%d.py'%i,block)
    for i,block in enumerate(re.findall(r'-c "([^"\n]*)"',text)):
        source(n+'.inline%d.py'%i,block.replace('\\\"','"').replace('\\$','$'))
    if n=='o_build_c600.sh':
        for filename,block in re.findall(r'cat > "\$S/([^"\n]+)" <<\x27C600_EOF\x27\n(.*?)\nC600_EOF',text,re.S):
            if filename.endswith('.py'):source('embedded/'+filename,block)
fill=(H/'o_place_pull_fill_c600.sh').read_text().split('<<SHELLCODE\n',1)[1].split('\nSHELLCODE',1)[0]
(V/'fill.sh').write_text(fill.replace('\\$','$'))
subprocess.run(['bash','-n',str(V/'fill.sh')],check=True)
for n in ('3.py','a/4.py','a/5.py','a/6.py','a/7.py'):
    source('package/'+n,(P/n).read_bytes())
with tarfile.open(str(P/'0.tgz')) as t:
    for n in ('8.py','orchard_h10/common.py','orchard_h10/export_pins.py','orchard_h10/job.py'):
        source('payload/'+n,t.extractfile(n).read())
batch=(P/'BATCH.sh').read_text()
subprocess.run(['bash','-n',str(P/'BATCH.sh')],check=True)
source('batch_bootstrap.py',batch.split("<<'A' &\n",1)[1].split('\nA\n',1)[0])
line=next(x for x in batch.splitlines() if x.startswith('b=bytes.fromhex('))
raw=bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0]))
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    for n in ('0.py','7.py'):source('bundle/'+n,t.extractfile(n).read())
# py_compile is the real local Python 3.6.8, with explicit cache destinations inside V.
compile_code='import py_compile,sys;[(py_compile.compile(p,cfile=p+".py36c",doraise=True)) for p in sys.argv[1:]]'
subprocess.run(['/usr/bin/python3','-B','-c',compile_code]+[str(p) for p in pyfiles],check=True)

# Preserve every original submission assertion and the empty-general queue guard.
old=(H/'in/ref/o_sub_A10b.sh').read_text();new=(H/'o_sub_c600.sh').read_text()
for line in old.splitlines():
    if line.lstrip().startswith('assert '):assert line in new,line
for line in ('test ! -e "$P/a/8.txt"','squeue -u jjyeung -p general -h > "$P/a/9.txt"','test ! -s "$P/a/9.txt"'):
    assert line in new,line
guard=new.split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0]
source('submit_guard.py',guard)
subprocess.run(['/usr/bin/python3','-B','-c',compile_code,str(V/'submit_guard.py')],check=True)
# Use a visibly separate fixture package for a synthetic CPU receipt; never claim a real CPU run.
G=V/'guard_package';G.mkdir();(G/'a/c').mkdir(parents=True)
for p in P.iterdir():
    if p.name!='a':(G/p.name).symlink_to(p)
for p in (P/'a').iterdir():
    if p.name not in ('c','0.json','1.json','6.py'):(G/'a'/p.name).symlink_to(p)
for n in ('0.json','1.json','6.py'):(G/'a'/n).write_bytes((P/'a'/n).read_bytes())
c=read(H/'in/out4s/A/package/a/c/CPU.json')
c.update(payload=pub['payload_sha256'],plan=pub['plan_sha256'],operator_sha256=sha(G/'a/6.py'),inputs=sha(G/'a/1.json'))
for name in ('bundle_guard','entry_sequence'):
    e=c[name];e.update(operator_sha256=c['operator_sha256'],operator_sha256_before=c['operator_sha256'],
        operator_sha256_after=c['operator_sha256'],batch_sha256=sha(G/'BATCH.sh'),token=pub['token'])
write(G/'a/c/CPU.json',c);write(G/'a/c/MEMORY.json',c['memory'])
def guard_run(expected):
    r=subprocess.run(['/usr/bin/python3','-B',str(V/'submit_guard.py'),str(G)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert (r.returncode==0)==expected,r.stderr.decode()
guard_run(True)
for key,value in [('payload','0'*64),('operator_sha256','0'*64),('inputs','0'*64),('passed',False)]:
    bad=copy.deepcopy(c);bad[key]=value;write(G/'a/c/CPU.json',bad);guard_run(False)
write(G/'a/c/CPU.json',c)
original=(G/'a/0.json').read_bytes();bad=json.loads(original);bad['types'].append('object_abs_distance')
write(G/'a/0.json',bad);guard_run(False);(G/'a/0.json').write_bytes(original)
operator=(G/'a/6.py').read_bytes()
(G/'a/6.py').write_bytes(operator.replace(b'COUNTS=(150,150,150,0,0)',b'COUNTS=(150,150,150,150,36)'))
guard_run(False);(G/'a/6.py').write_bytes(operator)

# Run the actual operator's prepare/worker arguments/completion using a deterministic CPU runner.
sys.path[:0]=[str(H/'in/out4s/A/src'),str(H/'in/out4s/A/src/b')]
op=runpy.run_path(str(P/'a/6.py'),run_name='operator_verify')
settings=read(H/'in/out3/A10b/ret/metadata/reads/0/metadata/0.json')
write(V/'settings.json',settings)
from orchard_h10.runner import control,worker_args
def case(name,count,stopped=False):
    root=V/name;root.mkdir()
    cfg=dict(output=str(root),settings=str(V/'settings.json'),package=str(H/'in/out4s/A/src'),
        plan_sha256=pub['plan_sha256'],inputs_sha256=sha(P/'a/1.json'),operator_sha256=sha(P/'a/6.py'),
        prefix='test',export_pin='pin',export='export',binding='binding',python=sys.executable)
    calls=[]
    def runner(config,cards,end,prefix):
        assert config['types']==['camera_displacement','camera_rotation','camera_movement_direction']
        assert config['arms']==['tower'] and config['modes']==['none']
        assert config['perception_memo']=='on' and config['perception_memo_modules']==('g3t',)
        control(config)
        args=worker_args(dict(config=config,type=0,index=0,cards=1,stop_at=10,finish_by=20))
        assert args[args.index('--types')+1]==','.join(config['types'])
        calls.append(config)
        return dict(completed=count,expected=450,complete=count==450,failure=None)
    result=op['run'](cfg,10000,['fake'],runner=runner,clock=lambda:9000 if stopped else 0)
    assert result['expected']==450 and result['completed']==(0 if stopped else count)
    assert result['complete']==(not stopped and count==450)
    assert len(calls)==(0 if stopped else 1)
    return result
results={n:case(n,c,s) for n,c,s in [('full',450,False),('partial',300,False),('stop_margin',0,True)]}
from make_read_plan_c600 import make
assert make(P,read(H/'in/BIND600.json'),read(H/'in/out4s/A/READ_PLAN.json'))==read(H/'READ_PLAN_C600.json')
write(V/'RESULT.json',dict(passed=True,python36_files=len(pyfiles),python36='/usr/bin/python3 3.6.8',
    shell_scripts=7,original_submit_assertions_preserved=True,synthetic_submit_guard_positive=True,
    submit_negative_tests=6,operator_cases=results,production_read_plan_matches=True))
print('PASS: Python 3.6 compile, shell syntax, original guards, six rejection cases, operator full/partial/stop cases.')
