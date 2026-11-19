"""Build a deterministic archive containing code/config/tests only; no data or weights."""
from pathlib import Path
import ast
import tarfile
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1]
files=[root/'README.md']
for name in ('REPORT.md','RL_ON_N_REPORT.md','RL_ON_N_SURVEY.md','TEST_RESULTS.json','TEST_RESULTS.log',
             'CPU_PROOF.json','CPU_PROOF.log','CPU_SYNTHETIC_SIDECAR.json','PARITY.json','GATE_CHECK.json',
             'REMOVE_CHECK.json','SERVING_CHECK.json','GPU_ESTIMATE.json','PROMPT_POOL.json','REPORT_INPUTS.json'):
    files.append(root/'out'/name)
for directory in ('overlay','configs','tests','scripts'):
    files.extend(p for p in (root/directory).rglob('*') if p.is_file() and p.suffix in ('.py','.sh','.json','.md'))
for p in sorted(files):
    if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
    P.sha(p)
output=root/'out/sb_rlfix.tar'
with tarfile.open(output,'w') as archive:
    for p in sorted(set(files)):
        info=archive.gettarinfo(str(p),arcname=str(p.relative_to(root)))
        info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
        with p.open('rb') as f:archive.addfile(info,f)
digest=P.sha(output)
(root/'out/SHA256SUMS').write_text(f'{digest}  sb_rlfix.tar\n')
P.write(root/'out/PACKAGE.json',dict(schema='rl-on-n-package-v1',archive=str(output),sha256=digest,
    bytes=output.stat().st_size,members=[str(p.relative_to(root)) for p in sorted(set(files))],
    scope='Code, unbound configs, tests, documentation and CPU evidence; no training data or model weights',command='PYTHONPATH=overlay python -B scripts/package.py'))
print(digest,output.stat().st_size,len(files))
