"""Check one build before it is placed: seals, minimal diff against A4, scripts and Python 3.6 helpers.

usage: check_build.py BUILD_DIR [--a4 A4_DIR]
"""
import argparse,difflib,hashlib,json,re,subprocess,sys
from pathlib import Path

KIT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(KIT))
import build_ownread as B

A4=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4')
PY36='/usr/bin/python3'
HELPERS=['src/8.py','src/orchard_h10/common.py','src/orchard_h10/export_pins.py','src/orchard_h10/job.py','src/orchard_h10/vendor/export_stage.py',
         'src/orchard_h10/vendor/orchard_job.py','src/orchard_h10/vendor/orchard_launcher.py','src/orchard_h10/vendor/orchard_results.py',
         'package/a/4.py','package/a/5.py','tower_sequence.py','package/3.py','fetch_return.py','unpack_return.py']

def sha(b):return hashlib.sha256(b).hexdigest()
def changed(a,b):return [l for l in difflib.unified_diff(a.decode().splitlines(),b.decode().splitlines(),n=0) if l[:1] in '+-' and l[:3] not in ('+++','---')]

def check(build,a4=A4):
 build=Path(build);raw=(build/'1.tgz').read_bytes();operator=(build/'tower_sequence.py').read_bytes()
 a4d,a4p,_=B.load_a4(a4)
 record=B.verify(raw,a4d,operator)
 d=B.unpack(raw);p=B.unpack(d['0.tgz']);cfg=json.loads(p['9.json']);old=json.loads(a4p['9.json'])
 repinned=d['a/4.py']!=a4d['a/4.py']
 allowed={'0.json','0.tgz','BATCH.sh','CONFIG.json','PACKAGE.json','a/6.py'}|({'a/4.py'} if repinned else set())
 assert set(record['changed_delivery'])<=allowed,record['changed_delivery']
 assert operator==(KIT/'ownread_sequence.py').read_bytes(),'operator is not the kit operator'
 assert {k for k in cfg if cfg[k]!=old[k]}<={'token','export_binding'}
 moved={k for k in cfg['export_binding'] if cfg['export_binding'][k]!=old['export_binding'][k]}
 assert moved<=B.PIN_KEYS and (not moved or {'step','member_directory','object'}<=moved),moved
 assert repinned==bool(moved),'fill pins and export binding must move together'
 assert all(l[1:].split(' = ')[0] in B.FILL_PINS for l in changed(a4d['a/4.py'],d['a/4.py']))
 for n,v in d.items():assert (build/'package'/n).read_bytes()==v,n
 assert (build/'0.tgz').read_bytes()==d['0.tgz'] and (build/'PACKAGE.json').read_bytes()==d['PACKAGE.json'] and (build/'src/9.json').read_bytes()==p['9.json']
 text=d['a/4.py'].decode()
 size=int(re.search(r'(?m)^REVIEWED_ARCHIVE_BYTES = (\d+)$',text)[1]);digest=re.search(r"(?m)^REVIEWED_ARCHIVE_SHA256 = '([0-9a-f]{64})'$",text)[1]
 obj=re.search(r"(?m)^REVIEWED_OBJECT = '([^']+)'$",text)[1];binding=cfg['export_binding']
 assert obj==binding['object']
 plan=json.loads((build/'READ_PLAN.json').read_text())
 assert plan['token']==cfg['token']==(build/'TOKEN').read_text().strip() and plan['plan_sha256']==record['plan_sha256']
 assert plan['operator_sha256']==sha(operator) and plan['export_binding']==dict(binding,archive_bytes=size,archive_sha256=digest)
 manifest=json.loads(p['items/devs1_routed.json']);types=[cfg['order'][i] for i in plan['read_settings'][0]['types']]
 assert plan['item_ids_in_execution_order']==[it['id'] for t in types for it in sorted(manifest['items'],key=lambda x:x['id']) if it['question_type']==t]
 assert plan['expected']==[900] and len(plan['item_ids_in_execution_order'])==450
 scripts=sorted(build.glob('o_*.sh'))
 assert {s.name for s in scripts}>={'o_place.sh','o_pullfill.sh','o_cpucheck.sh','o_sub.sh','o_fetch.sh'}
 for s in scripts:
  subprocess.run(['bash','-n',str(s)],check=True);t=s.read_text()
  assert cfg['token'] in t and 'd72cdcff1e22a' not in t
  for code in re.findall(r"<<'PYCODE'\n(.*?)\nPYCODE\n",t,re.S):subprocess.run([PY36,'-c',f'compile({code!r},"x","exec")'],check=True)
 place=(build/'o_place.sh').read_text();fill=(build/'o_pullfill.sh').read_text()
 assert f"printf '%s  %s\\n' {sha(raw)} " in place
 assert f"b['run']=={binding['run']!r} and b['step']=={binding['step']} and b['member_directory']=={binding['member_directory']!r}" in place
 assert f"OBJECT={binding['object']}\n" in fill and f"--step {binding['step']} " in fill and f"int(f[1])=={size} and f[2]=={digest!r}" in fill
 assert re.search(r'(?m)^DONE=/project/community/jjyeung/okh7/x_69d2930d/o/gcs_%s_m%d\.done$'%(binding['run'],binding['step']),fill)
 code='import sys\nfrom pathlib import Path\nfor p in sys.argv[1:]:compile(Path(p).read_bytes(),p,"exec")\nprint(sys.version.split()[0])'
 r=subprocess.run([PY36,'-I','-s','-B','-c',code]+[str(build/n) for n in HELPERS],capture_output=True,text=True)
 assert r.returncode==0 and r.stdout.strip().startswith('3.6'),r.stderr
 return dict(passed=True,build=str(build),token=cfg['token'],step=binding['step'],delivery_sha256=sha(raw),plan_sha256=record['plan_sha256'],
             changed_delivery=record['changed_delivery'],changed_payload=record['changed_payload'],binding_changed=sorted(moved),
             fill_pins_changed=repinned,scripts=[s.name for s in scripts],python36_helpers=len(HELPERS))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('build');a.add_argument('--a4',default=str(A4));a=a.parse_args()
 print(json.dumps(check(a.build,Path(a.a4)),indent=1))
