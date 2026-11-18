"""Real local bwrap, real f.py and trainer, tiny SQLite receipt; no remote calls."""
import copy, hashlib, io, json, os, sqlite3, subprocess, sys, tarfile, uuid
from pathlib import Path

H=Path(__file__).resolve().parents[1]
OUT=H/'evidence/fix5_gate';OUT.mkdir(mode=0o700)
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
AS0='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
AL0='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'
ABS='/c8absent_'+uuid.uuid4().hex
assert not Path(ABS).exists()
RH='9a7f33103ee6faa9d44bfb7f02b6166ef6fc9f8e1bc5bac8681c697dce8a8851'
DH='3d1d2d05bc8d3fed3048618da0c25b330f693e6394c6e2564c3007d64c050001'
REL='ap/5e1d07a4/f/h/r16/'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(H/'build/tree'))
from generator.derivgen_v7.derivgen.materialize import materialize, _render
from student_pilot.h1_faithful import identity_check
row=dict(question_type='camera_rotation',trace_revision='3.11',frame_pair_rule='frame_gap',
         frame_pair_turn=[],options=[],answer='30',events=[
    dict(kind='tool_call',call_id='a',name='turn',arguments={'from':1,'to':32},token='<turn>'),
    dict(kind='tool_response',call_id='a',name='turn',values={'a.turn':{'value':30,'unit':'degree'}},text='turn = +30 deg'),
    dict(kind='canonical_text',text='The camera rotation is 30 degrees; positive yaw means left.'),
    dict(kind='decision',family='camera_rotation',binding={},call_ids=['a'],mode='numeric',unit={'factor':1,'decimals':0},result='30')])
row['target']=_render(row['events'],row['answer'])
assert identity_check([row])['passes'] is True
results={}
def fixture(name, *, prior=False, passes=True, roots=None, fcode=None):
    b=OUT/name;b.mkdir(mode=0o700)
    top=b/'o';top.mkdir(mode=0o700);bun=top/'i_1be16f28';bun.mkdir(mode=0o700)
    AS,AL=roots or (ABS+'/s/users/a',ABS+'/l/users/a')
    db=b/'rows.sqlite'
    with sqlite3.connect(db) as c:
        c.execute('CREATE TABLE rows(i INTEGER, row TEXT)')
        value=copy.deepcopy(row)
        if not passes:value['target']+=' altered'
        c.execute('INSERT INTO rows VALUES(0,?)',(json.dumps(value),))
    receipt=json.dumps({'database':{'path':AL+'/'+REL+'rows.sqlite','sha256':sha(db)}}).encode()
    rh=hashlib.sha256(receipt).hexdigest()
    arc=bun/'a_b8b60bce.tar'
    with tarfile.open(arc,'w') as tf:
        m=tarfile.TarInfo('.');m.type=tarfile.DIRTYPE;m.mode=0o700;tf.addfile(m)
        for name,data in [(REL+'receipt.json',receipt),(REL+'rows.sqlite',db.read_bytes())]:
            m=tarfile.TarInfo(name);m.size=len(data);tf.addfile(m,io.BytesIO(data))
    (bun/'a.json').write_text(json.dumps({'file':arc.name,'sha256':sha(arc)}))
    trainer=json.loads((H/'ids.json').read_text())['trainer']['file']
    os.link(H/'payload'/trainer,bun/trainer)
    (bun/'f.py').write_text(fcode or (H/'payload/f.py').read_text())
    (bun/'r.py').write_text('raise SystemExit(0)\n') # copy already authenticated by this fixture
    src=H/('evidence/fix5_before/payload/g.sh' if prior else 'payload/g.sh')
    script=src.read_text().replace('/project/community/jjyeung/okh7',str(top))
    script=script.replace(AS0,AS).replace(AL0,AL).replace(RH,rh).replace(DH,sha(db))
    (bun/'g.sh').write_text(script)
    (bun/'sums.txt').write_text(''.join(sha(bun/n)+'  '+n+'\n' for n in ['g.sh','f.py','r.py',trainer]))
    return bun

def run(bun,name,want,bw='/usr/bin/bwrap'):
    env=dict(os.environ,PY_GATE=PY,BW_GATE=bw,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    p=subprocess.run(['/bin/bash',str(bun/'g.sh')],env=env,capture_output=True,text=True)
    (OUT/(name+'.log')).write_text(p.stdout+p.stderr)
    assert p.returncode==want,(name,p.returncode,p.stdout,p.stderr)
    results[name]={'exit':p.returncode,'gate_exists':(bun/'gate.json').exists()}
    return p

old=fixture('old',prior=True)
p=run(old,'round4_absent_parent',1)
assert 'Read-only file system' in p.stderr and not (old/'gate.json').exists()
assert (old/'t').is_dir() and (old/'u').is_dir()
# Patch the failed bundle in place: identical fixture pins, keep its extracted bytes.
s=(old/'g.sh').read_text();new=(H/'payload/g.sh').read_text()
for oldval,newval in [(AS0,ABS+'/s/users/a'),(AL0,ABS+'/l/users/a'),('/project/community/jjyeung/okh7',str(old.parent)),(RH,sha(old/'u'/REL/'receipt.json')),(DH,sha(old/'u'/REL/'rows.sqlite'))]:
    new=new.replace(oldval,newval)
(old/'g.sh').write_text(new)
lines=(old/'sums.txt').read_text().splitlines();(old/'sums.txt').write_text('\n'.join(sha(old/'g.sh')+'  g.sh' if x.endswith('  g.sh') else x for x in lines)+'\n')
before={n:(old/n).stat().st_ino for n in ['t/student_pilot/h1_faithful.py','u/'+REL+'receipt.json']}
run(old,'round4_extractions_reused_pass',0)
assert all((old/n).stat().st_ino==i for n,i in before.items())
gate=(old/'gate.json').read_bytes();run(old,'existing_gate_refused',2);assert (old/'gate.json').read_bytes()==gate
run(fixture('below',passes=False),'below_threshold',1)
assert json.loads((OUT/'below/o/i_1be16f28/gate.json').read_text())['passes'] is False
broken=OUT/'bw_failure';broken.write_text('#!/bin/bash\necho "fixture bwrap setup failure" >&2\nexit 1\n');broken.chmod(0o700)
b=fixture('rerun');run(b,'bwrap_failure',2,str(broken));assert not (b/'gate.json').exists()
run(b,'rerun_after_bwrap_failure',0)
run(fixture('missing',fcode='raise SystemExit(0)\n'),'missing_report_even_status_zero',2)
run(fixture('import',fcode='import absent_module_for_gate_test\n'),'import_error',2)
for label,report,status in [('bad_json',None,0),('bad_sha',{'passes':True,'source_receipt_sha256':'bad'},0),('nonbool',{'passes':'yes','source_receipt_sha256':RH},0),('pass_bad_exit',{'passes':True,'source_receipt_sha256':RH},1)]:
    code="import pathlib,sys,hashlib,json\np=pathlib.Path(sys.argv[-1])\n"
    if report is None:code+="p.write_text('{')\n"
    else:
        code+='r='+repr(report)+"\n"
        if label!='bad_sha':code+="r['source_receipt_sha256']=hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()\n"
        code+="p.write_text(json.dumps(r))\n"
    code+='raise SystemExit('+str(status)+')\n'
    run(fixture(label,fcode=code),label,2)
# Existing read-only top-level /scratch also needs a synthetic ancestor skeleton.
run(fixture('existing_top',roots=('/scratch/c8absent_'+uuid.uuid4().hex+'/s',ABS+'/l')),'existing_top_missing_parent',0)
# Confirm mount aliases, read-only host/receipt views, venv startup, caches and priority.
checks='''import os,pathlib,sys
assert os.getpriority(os.PRIO_PROCESS,0)==19
assert os.environ['HF_HUB_OFFLINE']==os.environ['TRANSFORMERS_OFFLINE']=='1'
assert not os.environ['CUDA_VISIBLE_DEVICES']
assert pathlib.Path(os.environ['TMPDIR']).parent==pathlib.Path(__file__).parent
assert pathlib.Path('/proc/self/status').is_file() and pathlib.Path('/dev/null').exists()
assert pathlib.Path('/bin').is_symlink()==HOST_BIN_LINK
for name in [sys.argv[1],'/etc/c8_write_probe']:
    try:
        with open(name,'ab'):pass
    except OSError:pass
    else:raise AssertionError('writable host or receipt')
'''.replace('HOST_BIN_LINK',repr(Path('/bin').is_symlink()))
run(fixture('properties',fcode=checks+(H/'payload/f.py').read_text()),'sandbox_properties',0)
for label,rel in [('trainer','t/student_pilot/h1_faithful.py'),('receipt','u/'+REL+'receipt.json'),('database','u/'+REL+'rows.sqlite'),('extra','t/extra.py')]:
    b=fixture('tamper_'+label);run(b,'before_tamper_'+label,2,str(broken))
    (b/rel).write_bytes(b'altered')
    run(b,'tampered_'+label,2)
assert not Path(ABS).exists()
(OUT/'results.json').write_text(json.dumps({'status':'PASS','bwrap_version':subprocess.check_output(['/usr/bin/bwrap','--version'],text=True).strip(),'cases':results,'real_fpy_and_trainer':True,'test_only_relocations':'bundle, logical roots and receipt/sqlite pins; production constants unchanged'},indent=2)+'\n')
print(json.dumps(results,indent=2))
