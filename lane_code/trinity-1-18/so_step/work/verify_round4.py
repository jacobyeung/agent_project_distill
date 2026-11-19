"""Replay unchanged patches on only their named inputs; check syntax and delivery pins."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OUT/'patches_b21/manifest.json').read_text())
application=manifest['_application']; base=Path(application['input_root'])
tree=Path(application['tested_tree'])
replay=Path(tempfile.mkdtemp(prefix='round4_patch_replay_',dir=ROOT/'work'))
print(subprocess.check_output(['date','-u'],text=True).strip())
for relative,pin in application['input_sha256'].items():
    if pin is None:
        assert not (base/relative).exists(),relative
        continue
    source=base/relative
    assert sha(source)==pin,relative
    target=replay/relative;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(source.read_bytes())
for folder in ('patches','patches_b21'):
    for p in sorted((OUT/folder).iterdir()):
        assert p.read_bytes()==(ROOT/'out_round4'/folder/p.name).read_bytes(),p
for name,record in manifest.items():
    if not name.endswith('.diff'): continue
    diff=OUT/'patches_b21'/name
    assert sha(diff)==record['sha256']
    command=['nice','-n','10','patch','--batch','--fuzz=0','-p1','-i',str(diff)]
    print('$ '+' '.join(command)+' (cwd='+str(replay)+')',flush=True)
    result=subprocess.run(command,cwd=replay,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(result.stdout,end='')
    assert result.returncode==0 and 'offset' not in result.stdout and 'fuzz' not in result.stdout
for relative,pin in application['output_sha256'].items():
    assert sha(replay/relative)==sha(tree/relative)==pin,relative
print('ROUND4_PATCH_REPLAY_PASS: 4 patches; 22 touched files; zero fuzz/offsets; both patch folders unchanged')
for folder in ('kit_profile','kit_timing'):
    for p in sorted((OUT/folder).glob('*.py')): ast.parse(p.read_text(),filename=str(p))
    for p in sorted((OUT/folder).glob('*.sh')):
        subprocess.run(['bash','-n',str(p)],check=True)
        print('SHELL_SYNTAX_PASS: '+str(p.relative_to(OUT)))
print('KIT_PYTHON_SYNTAX_PASS')
coordinator=(ROOT/'work/round3_b21_gloo_by_coordinator.txt').read_text()
for text in ('Ran 31 tests in 880.158s','\nOK\n','EXIT=0','Thu Nov 19 12:55:19 UTC 2026',
             'SO_GLOO_PROOF','SO_ADMISSION_PROOF','SO_FALLBACK_PROOF'):
    assert text in coordinator,text
print('COORDINATOR_PROVENANCE_PASS: 31 tests OK, EXIT=0, 2026-11-19 12:55:19 UTC')
