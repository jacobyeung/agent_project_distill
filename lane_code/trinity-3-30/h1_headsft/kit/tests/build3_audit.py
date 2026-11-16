"""Small, bounded checks of relocatable inputs and H1-0 refusal paths."""
import ast
import json
from pathlib import Path
import subprocess
from h1eval.items import K, load_manifest, sha

report={}
for name in ('revsi999','devs1_routed','devs1_direct_main'):
    m=load_manifest(K/'items'/f'{name}.json')
    report[name]={k:m[k] for k in ('count','per_type','item_set_sha256','r0_check')}
report['camera_parse']=load_manifest(K/'items/devs1_routed.json')['camera_parse']
for entry in json.loads((K/'BUILD3_INPUT_SHA256.json').read_text()):
    assert sha(K/entry['destination'])==entry['sha256']
report['input_pins']=8
files=[*K.joinpath('h1eval').rglob('*.py'),K/'rows/mix_h1.py',K/'tree/student_pilot/h1_r0.py']
for file in files:ast.parse(file.read_text())
report['syntax_files']=len(files)
report['operator_note_lines']=len((K/'h1eval/h10/RUN_H10.md').read_text().splitlines())
assert report['operator_note_lines']<=40
root='/scratch/jjyeung/orch_n30/b04_e2ehook'
missing=str(K/'tmp/b3/not-staged')
commands=[['-m','h1eval.h10.launch','--items',str(K/'items/devs1_routed.json'),'--reader-root',root,
           '--export',missing,'--artifact-manifest',missing,'--out',str(K/'tmp/b3/refusal'),'--device','cpu'],
          ['-m','h1eval.h10.cpu_first_batch','--reader-root',root,'--export',missing,'--heads',missing,'--artifact-manifest',missing]]
report['unpublished_reader_refusals']=[]
for args in commands:
    result=subprocess.run(['bash',str(K/'cpu.sh'),*args],capture_output=True,text=True)
    assert result.returncode==2 and 'make_real is unavailable' in result.stderr,result.stderr
    report['unpublished_reader_refusals'].append(dict(command=args,exit=result.returncode,message=result.stderr.strip()))
# Load ready sets from the relocated code at an unrelated working directory.
relocated=K/'tmp/b3/relocated'
code="from pathlib import Path; import h1eval.items as m; assert str(m.K)=="+repr(str(relocated))+"; print([(n,m.load_manifest(m.K/'items'/ (n+'.json'))['count']) for n in ('revsi999','devs1_routed','devs1_direct_main')])"
result=subprocess.run(['bash',str(relocated/'cpu.sh'),'-c',code],cwd=K/'tmp/b3',capture_output=True,text=True)
assert result.returncode==0,result.stderr
report['relocated_manifests']=result.stdout.strip()
(K/'logs/b3/audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
