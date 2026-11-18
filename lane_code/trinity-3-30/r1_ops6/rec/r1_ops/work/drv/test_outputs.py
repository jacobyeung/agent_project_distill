"""Check generated scripts and embedded code without executing operator actions."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
from packet_config import PINS, MEMBERS, render
from review_policy import build_chain
W=Path(__file__).resolve().parent
names=['u1.sh','u3.sh','q1.sh','ev1.sh','evp1.sh','dv1.sh','dvp1.sh','scan1.sh','L1_mint.sh','pr1.sh','pm1.sh','rv1.sh']
count=0
for name in names:
 text=(W/name).read_text()
 subprocess.run(['bash','-n',str(W/name)],check=True)
 assert not re.search(r'@[A-Z_]+@',text),name
 for body in re.findall(r"<<'PYCODE'\n(.*?)^PYCODE$",text,re.M|re.S):
  compile(body,name,'exec');count+=1
 for body in re.findall(r"<<'SHCODE'\n(.*?)^SHCODE$",text,re.M|re.S):
  subprocess.run(['bash','-n'],input=body,text=True,check=True)
 if name!='rv1.sh':
  assert not re.search('1130b378|125c4c87|782f303d|42bbcbb218|BLOCKED_PACKET',text),name
 if name not in ('L1_mint.sh','rv1.sh'):
  assert 'i_'+PINS['store'] in text and 'x_'+PINS['store'] in text,name
for name in ('packet_config.py','build_drivers.py','review_policy.py','review_build.py','session_build.py','cert_build.py','evidence_body.py','evidence_embedded.py','derive_body.py','scan_body.py','q_check.py','test_local.py','test_builders.py','test_guards.py','test_outputs.py'):
 compile((W/name).read_text(),name,'exec')
assert (W/'e.txt').read_bytes()==MEMBERS['e.txt']
assert PINS['deriver'] in (W/'dv1.sh').read_text()
assert 'g.check(out' not in MEMBERS['d.py'].decode()
assert render((W/'review_policy.py').read_text()) in (W/'ev1.sh').read_text()
assert (W/'evidence_embedded.py').read_text() in (W/'ev1.sh').read_text()
assert render((W/'derive_body.py').read_text()) in (W/'dv1.sh').read_text()
body=re.search(r"<<'PYCODE'\n(.*?)^PYCODE$",(W/'rv1.sh').read_text(),re.M|re.S).group(1)
values={}
for node in ast.parse(body).body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('record','texts'):
  values[node.targets[0].id]=ast.literal_eval(node.value)
assert values['record']==build_chain(values['texts'],PINS['identity'],PINS['tree'],PINS['outer'])
assert values['record']['final_verdict']=='GO'
print('PASS 12 shell scripts; '+str(count)+' embedded Python bodies; nested worker shells; builder Python syntax')
print('PASS all active driver pins and export destinations match final packet; no unresolved placeholders or stale executable pins')
print('PASS ev1 embeds current chain validator; dv1 embeds exact deriver guard; rv1 preserves actual three-review chain with final GO')
