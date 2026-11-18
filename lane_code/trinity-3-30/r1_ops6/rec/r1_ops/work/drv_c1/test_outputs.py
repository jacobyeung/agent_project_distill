"""Check every shipped shell and embedded body without operator actions."""
import hashlib,re,subprocess
from pathlib import Path
from packet_config import PINS, MEMBERS, pending_script, render
W=Path(__file__).resolve().parent
scripts=sorted(W.glob('*.sh'));count=0
for path in scripts:
 text=path.read_text()
 subprocess.run(['bash','-n',str(path)],check=True)
 assert not re.search(r'@[A-Z_]+@',text),path.name
 if path.name != 'rv1.sh':assert not re.search(r'i_c5f3847d|x_c5f3847d|26cc98b7|d8b03fd1|i_6f8ed106|x_6f8ed106|78d0a06c|2c67f1f2|082d2d90|07297df8|8246a4dd|drv_p3|drv_p2|work/drv(?:[\s/]|$)',text),path.name
 for body in re.findall(r"<<'PYCODE'\n(.*?)^PYCODE$",text,re.M|re.S):
  compile(body,path.name,'exec');count+=1
 for body in re.findall(r"<<'SHCODE'\n(.*?)^SHCODE$",text,re.M|re.S):
  subprocess.run(['bash','-n'],input=body,text=True,check=True)
for path in W.glob('*.py'):compile(path.read_text(),path.name,'exec')
assert (W/'e.txt').read_bytes()==MEMBERS['e.txt']
assert PINS['deriver'] in (W/'dv1.sh').read_text()
assert render((W/'review_policy.py').read_text()) in (W/'ev1.sh').read_text()
assert (W/'evidence_embedded.py').read_text() in (W/'ev1.sh').read_text()
assert render((W/'derive_body.py').read_text()) in (W/'dv1.sh').read_text()
q=(W/'q1.sh').read_text()
assert '/project/community/jjyeung/latency/envs/fit/bin/python3' in q
assert "'--unit-binding',str(B/'u.json'),'--config',str(B/'config.json')" in q
assert "p['native_unit_regeneration_executed'] is True" in q
assert (W/'pr2.sh').read_bytes()==(W/'pr1.sh').read_bytes()
assert 'job2.id' not in (W/'pm1.sh').read_text()
mint=(W/'L1_mint.sh').read_text()
for value in ('drv_c1','sess_05b8ac69_08f3a7b2.json','mint_05b8ac69_08f3a7b2.started','mint_05b8ac69_08f3a7b2.private.log'):
 assert value in mint,value
for name in ('sc1.sh','si1.sh'):
 assert (W/name).read_text()==pending_script(name), 'Do not claim real approval/session data in the build fixture'
 r=subprocess.run(['bash',str(W/name)],capture_output=True,text=True)
 assert r.returncode==4 and 'PENDING' in r.stderr
review=(W/'rv1.sh').read_text()
assert review==pending_script('rv1.sh') or ('final review_r1c3 accepted' in review and PINS['outer'] in review and "'review_r1p8'" in review)
if (W/'ANON_OK.json').exists():
 import json
 assert json.loads((W/'ANON_OK.json').read_text()).get('operator_archive_sha256') != PINS['outer'], 'New certificate requires independent validation'
print('PASS '+str(len(scripts))+' shell scripts; '+str(count)+' embedded Python bodies; nested workers; all builder Python syntax')
print('PASS packet-C names and export destinations; native unit flags and H1 CPU environment; fresh mint markers')
print('PASS eleven-review evidence validator and deriver SHA; review installer pins; inert certificate/session installers; matching submission entry points')
