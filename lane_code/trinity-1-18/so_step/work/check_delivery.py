"""Bounded integrity, syntax and installed-framework source checks; no GPU calls."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'out/patches/manifest.json').read_text())
count=0
for name,item in manifest.items():
    if not name.endswith('.diff'):
        continue
    payload=(ROOT/'out/patches'/name).read_bytes()
    assert len(payload)==item['bytes']
    assert hashlib.sha256(payload).hexdigest()==item['sha256']
    for relative in item['paths']:
        path=ROOT/'work/verified_delivery/combined'/relative
        assert path.read_bytes()==(ROOT/'work/tree'/relative).read_bytes()
        if path.suffix=='.py':
            ast.parse(path.read_text(),filename=str(path))
            count+=1
    print(f'{name}: {len(payload)} bytes; SHA256 {item["sha256"]}; clean-copy contents match')
for folder in ('out/kit_profile','out/kit_timing'):
    for path in sorted((ROOT/folder).glob('*.py')):
        ast.parse(path.read_text(),filename=str(path));count+=1
    for path in sorted((ROOT/folder).glob('*.sh')):
        subprocess.run(['bash','-n',str(path)],check=True)
        print('SHELL_SYNTAX_PASS: '+str(path.relative_to(ROOT)))
print(f'PYTHON_SYNTAX_PASS: {count} patch/kit file checks')

environment=Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages')
excerpts={
    'transformers/models/qwen3_5/modeling_qwen3_5.py':[(66,76),(187,219),(246,324),(406,430),(480,560)],
    'transformers/utils/import_utils.py':[(208,213),(845,853)],
    'torch/distributed/fsdp/api.py':[(33,41),(73,105)],
    'torch/distributed/fsdp/fully_sharded_data_parallel.py':[(345,359)],
    'torch/distributed/fsdp/_runtime_utils.py':[(277,307),(748,778),(831,886)],
    'torch/utils/checkpoint.py':[(389,399),(441,474),(490,496)],
    'torch/optim/adam.py':[(934,948)],
    'torch/cuda/__init__.py':[(1152,1163)],
    'torch/_tensor.py':[(806,825)],
    'torch/_torch_docs.py':[(4066,4085),(9815,9825)],
}
lines=[]
for relative,ranges in excerpts.items():
    path=environment/relative
    payload=path.read_bytes()
    source=payload.decode().splitlines()
    lines.append(f'FILE: {path}\nSHA256: {hashlib.sha256(payload).hexdigest()}')
    for first,last in ranges:
        lines.extend(f'{number}: {source[number-1]}' for number in range(first,last+1))
(ROOT/'out/evidence/framework_source_audit.txt').write_text('\n'.join(lines)+'\n')
print(f'SOURCE_AUDIT_PASS: {len(excerpts)} installed files; numbered excerpts and SHA256 retained')
