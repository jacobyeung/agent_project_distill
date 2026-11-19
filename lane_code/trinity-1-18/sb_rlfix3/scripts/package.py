"""Package the runnable overlay, sealed reader payload and current CPU evidence."""
from pathlib import Path
import ast
import tarfile
from rl_on_n import provenance as P
root=Path(__file__).resolve().parents[1];P.sha(__file__)
files=[root/'README.md',root/'STATUS.md',root/'runs/mut/mutate.py',root/'runs/mut/mutants.json',root/'runs/mut/mutate.log']
for name in ('REPORT.md','RL_ON_N_REPORT.md','TEST_RESULTS.json','TEST_RESULTS.log','CPU_PROOF.json','CPU_PROOF.log',
             'CPU_SYNTHETIC_SIDECAR.json','PARITY.json','GATE_CHECK.json','REMOVE_CHECK.json',
             'SERVING_CHECK.json','N_EXPORT_CHECK.json','GPU_ESTIMATE.json','PROMPT_POOL.json','REPORT_INPUTS.json',
             'STEP_LOOP.json','REPLAY_SELECTION.json'):
    files.append(root/'out'/name)
for directory in ('overlay','configs','tests','scripts','in/claimed_reader'):
    files.extend(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for p in sorted(set(files)):
    if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
    P.sha(p)
output=root/'out/sb_rlfix3.tar'
with tarfile.open(output,'w') as archive:
    for p in sorted(set(files)):
        info=archive.gettarinfo(str(p),arcname=str(p.relative_to(root)))
        info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';info.mode=0o644
        with p.open('rb') as f:archive.addfile(info,f)
digest=P.sha(output)
(root/'out/SHA256SUMS').write_text(f'{digest}  sb_rlfix3.tar\n')
P.write(root/'out/PACKAGE.json',dict(schema='rl-on-n-package-v2',archive=str(output),sha256=digest,
    bytes=output.stat().st_size,members=[str(p.relative_to(root)) for p in sorted(set(files))],
    scope='Overlay, sealed A4 source payload, unbound configs, tests, mutant rerun and CPU evidence; no model weights',
    command='PYTHONPATH=overlay python -B scripts/package.py'))
print(digest,output.stat().st_size,len(set(files)))
