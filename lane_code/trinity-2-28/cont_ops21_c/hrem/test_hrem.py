"""CPU-only synthetic authentication, remainder, merge and hardlink regression tests."""
import copy
import hashlib
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch
import return_tools_h as rt
from build_support import read_tar
from build_remainder_h import build
from make_items_remainder_h import select
from place_fill_hrem import link_parts
from score_h_merge import score, merged

HERE=Path(__file__).resolve().parent
ROOT=Path(tempfile.mkdtemp(prefix='hrem-',dir=str(HERE/'validation')))
PARENT=HERE/'in/H544/package'
checks=[]

def put(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')

def refusal(name,fn):
    try:fn()
    except (ValueError,AssertionError,KeyError,OSError,EOFError,json.JSONDecodeError):checks.append(name);return
    raise AssertionError('Accepted '+name)

def publish(name,files,package,complete,job=999):
    d=ROOT/name;d.mkdir();archive=d/'0.tgz'
    with tarfile.open(str(archive),'w:gz') as t:
        for n,b in sorted(files.items()):
            m=tarfile.TarInfo(n);m.size=len(b);t.addfile(m,io.BytesIO(b))
    info=rt.package_info(package);token=info['token']+'%08x'%job
    ex=dict(token=token,job=str(job),plan_sha256=info['plan'],synthetic=False,complete=complete,
            status='COMPLETE' if complete else 'FAILED',archive_complete=True,conflicting_terminal_markers=False,
            archive_sha256=rt.digest(archive),archive_bytes=archive.stat().st_size)
    put(d/'EXIT.json',ex)
    receipt=dict(token=token,job=str(job),plan_sha256=info['plan'],returned=True,channels={'pool':dict(verified=True,files={n:dict(bytes=p.stat().st_size,sha256=rt.digest(p)) for n,p in [('EXIT.json',d/'EXIT.json'),('result.tar.gz',archive)]})})
    put(d/'RETURN_RECEIPT.json',receipt)
    return dict(package=str(package),archive=str(archive),exit=str(d/'EXIT.json'),receipt=str(d/'RETURN_RECEIPT.json'))

def encoded(v):return (json.dumps(v,sort_keys=True)+'\n').encode()

with tarfile.open(str(PARENT/'a/f/0.tgz')) as t:original={m.name:t.extractfile(m).read() for m in t.getmembers()}
real=dict(package=str(PARENT),archive=str(PARENT/'a/f/0.tgz'),exit=str(PARENT/'a/f/EXIT.json'),receipt=str(PARENT/'a/f/RETURN_RECEIPT.json'))
m,rows,meta,info=select(real,ROOT/'selected')
assert m['per_type']=={'camera_rotation':118,'camera_movement_direction':300} and len(rows)==482
checks.append('real_selection_482_plus_418')
put(ROOT/'items.json',m)
os.environ['KROOT']=str(ROOT/'packages')
r=build(PARENT,real['archive'],real['exit'],real['receipt'],ROOT/'build',ROOT/'items.json')
package=Path(r['package']);package.mkdir(parents=True)
for member,data in read_tar((ROOT/'build/1.tgz').read_bytes()):
    p=package/member.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
# Simulate filled metadata without opening any model archives.
for n in ('a/1.json','a/export.json'):(package/n).write_bytes((PARENT/n).read_bytes())
ri=rt.package_info(package)
assert ri['serving_pins']==info['serving_pins']
assert ri['manifest']==m and r['counts']==(0,118,300,0,0) and r['schedule']==((0,1),(0,2))
assert all(data==info['payload'][n] for n,data in ri['payload'].items() if n.startswith(('h1eval/','b/')))
checks.append('fresh_build_preserves_serving_and_exact_subset')
files={k:v for k,v in original.items() if '/journals/' not in k and not k.endswith('SUMMARY.json') and k!='metadata/STOP'}
identity=json.loads(files['metadata/IDENTITY.json']);identity['plan']=ri['plan'];identity['operator_sha256']=ri['operator_sha256']
identity['schedule']=[[0,1],[0,2]];identity['reads'][0]['types']=[1,2];identity['reads'][0]['expected']=418
files['metadata/IDENTITY.json']=encoded(identity)
for n in ('metadata/reads/0/metadata/READ_IDENTITY.json','metadata/reads/0/metadata/IDENTITY.json'):
    value=json.loads(files[n]);value.update({k:v for k,v in identity.items() if k in value});files[n]=encoded(value)
files['metadata/RETURN_ID.json']=encoded(dict(token=ri['token']+'%08x'%999,job='999'))
files['SUMMARY.json']=encoded(dict(expected=418,completed=418,complete=True))
seed=copy.deepcopy(next(iter(rows.values())))
for t,k in enumerate(rt.TYPES):
    ids=[i['id'] for i in m['items'] if i['question_type']==k]
    if not ids:continue
    prefix='metadata/reads/0/metadata/journals/%d/0/'%t
    env=json.loads(original['metadata/reads/0/metadata/journals/1/0/environment.json'])
    env['binding'].update(ids=ids,count=418,items_sha256=ri['items_sha256'],item_set_sha256=m['item_set_sha256'],mapping_sha256=rt.canonical([i["id"] for i in m["items"]]))
    files[prefix+'environment.json']=encoded(env)
    lines=[]
    for item in m['items']:
        if item['question_type']!=k:continue
        row=copy.deepcopy(seed);row.update(id=item['id'],room_key=item['room_key'],type=k)
        row['output']['scores']['answer']=float(len(lines)%2)
        lines.append(encoded(row))
    files[prefix+'items.jsonl']=b''.join(lines)
rest=publish('remainder',files,package,True)
spec=dict(parent=real,remainder=rest);put(ROOT/'SCORE_SPEC.json',spec)
result=score(spec,ROOT/'score')
assert sum(c['completed'] for c in result['cells'].values())==900
assert sum(v['answer']['n'] for v in result['reworded_minus_original'].values())==450
put(ROOT/'SCORES.json',result);checks.append('synthetic_merge_900_rows_450_pairs_room_bootstrap')
# Exercise the public CLI as well as the API.
import subprocess
subprocess.run(['/usr/bin/python3',str(HERE/'score_h_merge.py'),'--spec',str(ROOT/'SCORE_SPEC.json'),'--work',str(ROOT/'cli_score'),'--out',str(ROOT/'CLI_SCORES.json')],check=True)
checks.append('python36_scoring_cli')
for name,key,value in [('wrong_token','token','d00000000000000000000'),('wrong_plan','plan_sha256','f'*64)]:
    ex=rt.read(real['exit']);ex[key]=value;put(ROOT/(name+'.json'),ex)
    refusal(name,lambda key=name:rt.unpack(real['archive'],ROOT/(key+'.json'),real['receipt'],PARENT,ROOT/key))
changed=copy.deepcopy(m);changed['items'][0]['answer']='edited';changed['item_set_sha256']=rt.canonical(changed['items']);put(ROOT/'edited.json',changed)
refusal('edited_subset_build',lambda:build(PARENT,real['archive'],real['exit'],real['receipt'],ROOT/'bad_build',ROOT/'edited.json'))
journal='metadata/reads/0/metadata/journals/1/0/items.jsonl'
for name,mutate in [
 ('duplicate_ids',lambda f:f.update({journal:f[journal]+f[journal].splitlines(True)[0]})),
 ('truncated_journal',lambda f:f.update({journal:f[journal][:-1]})),
 ('mixed_export',lambda f:f.update({'metadata/EXPORT_PIN.json':encoded(dict(json.loads(f['metadata/EXPORT_PIN.json']),step=200))})),
 ('mixed_settings',lambda f:f.update({'metadata/reads/0/metadata/journals/1/0/environment.json':encoded(dict(json.loads(f['metadata/reads/0/metadata/journals/1/0/environment.json']),settings={}))})),
 ('wrong_inner_token',lambda f:f.update({'metadata/RETURN_ID.json':encoded(dict(token='bad',job='999'))})),
 ('unexpected_journal',lambda f:f.update({'metadata/reads/0/metadata/journals/4/0/items.jsonl':b''})),
 ('wrong_summary',lambda f:f.update({'SUMMARY.json':encoded(dict(expected=418,completed=417,complete=False))}))]:
    altered=dict(files);mutate(altered);bad=publish(name,altered,package,True)
    refusal(name,lambda bad=bad,name=name:merged(dict(parent=real,remainder=bad),ROOT/('reject_'+name)))
refusal('overlapping_full_returns',lambda:merged(dict(parent=real,remainder=real),ROOT/'overlap'))
# Small hardlink fixtures exercise the exact production verifier without heavy IO.
def parts(name):
    d=ROOT/name;d.mkdir();chunks=[b'a'*123,b'b'*321,b'c'*67,b'd'*99]
    b=dict(object='fixture',archive_bytes=sum(map(len,chunks)),archive_sha256=hashlib.sha256(b''.join(chunks)).hexdigest(),parts=[])
    for i,raw in enumerate(chunks):
        (d/str(i)).write_bytes(raw);b['parts'].append(dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    (d/'5').write_text('%s %s %s\n'%(b['object'],b['archive_bytes'],b['archive_sha256']))
    out=ROOT/(name+'-out');out.mkdir();return d,out,b
src,dst,b=parts('links');identities=link_parts(src,dst,b)
assert all(os.stat(str(src/str(i))).st_ino==os.stat(str(dst/str(i))).st_ino for i in range(4));checks.append('four_verified_hardlinks')
for name,mutate in [('bad_marker',lambda s,b:(s/'5').write_text('wrong')),('bad_part',lambda s,b:(s/'0').write_bytes(b'x'*123)),('bad_size',lambda s,b:b['parts'][0].update(bytes=1)),('bad_concat',lambda s,b:b.update(archive_sha256='f'*64))]:
    src,dst,b=parts(name);mutate(src,b)
    refusal(name,lambda:link_parts(src,dst,b));assert not list(dst.iterdir())
src,dst,b=parts('link_failure')
with patch('place_fill_hrem.os.link',side_effect=OSError('EXDEV')):
    refusal('link_failure_no_copy',lambda:link_parts(src,dst,b))
assert not list(dst.iterdir())
src,dst,b=parts('race');real_link=os.link
def race(*args,**kwargs):
    (src/'1').write_bytes(b'z'*321)
    return real_link(*args,**kwargs)
with patch('place_fill_hrem.os.link',side_effect=race):refusal('retained_fstat_identity_race',lambda:link_parts(src,dst,b))
report=dict(passed=True,checks=checks,synthetic=True,real_parent_completed=482,remainder=418,merged=900,pairs=450,walltime=r['walltime'],timing=r['timing'],evidence=str(ROOT))
put(ROOT/'TEST_RESULTS.json',report);put(HERE/'TEST_RESULTS.json',report)
print(json.dumps(report,sort_keys=True))
