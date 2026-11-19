import json, os, subprocess, sys
from pathlib import Path
r=Path(__file__).resolve().parent;root=r.parents[2];applied=r.parent/'applied_final'
assert sys.version_info[:3]==(3,6,8)
print('login_python='+sys.version.split()[0])
files=sorted(applied.glob('*.py'))
for p in files:compile(p.read_bytes(),str(p),'exec')
print('compiled_delivered_sources='+str(len(files)))
for group in ('production_build','r10','routed_harness','pack_check','native_dry2','orchard'):
    command=['nice','-n','10','/usr/bin/python3','-I','-s','-B',str(applied/'check_required_inputs.py'),'--manifest',str(applied/'out/REQUIRED_INPUTS.json'),'--group',group]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output=result.stdout.decode();assert result.returncode==1 and 'REJECTED:' in output,output
    assert ('Required input missing:' in output) if group!='orchard' else ('read-only remote preflight' in output)
    print(json.dumps(dict(group=group,expected_refusal=True,returncode=result.returncode,output=output),sort_keys=True))
cfg=json.loads((applied/'out/config_step600.example.json').read_text());cfg['work']=str(r/'example_state')
config=r/'example_config.json';config.write_text(json.dumps(cfg))
command=['nice','-n','10','/usr/bin/python3','-I','-s','-B',str(applied/'pack.py'),'build','--enable','--config',str(config),'--token','a123456789ab']
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
output=result.stdout.decode();assert result.returncode==1 and 'Required input missing: reviewed source delivery' in output,output
print(json.dumps(dict(example_build=True,expected_refusal=True,returncode=result.returncode,output=output),sort_keys=True))
print('PASS: missing inputs refuse before a builder or remote call')
