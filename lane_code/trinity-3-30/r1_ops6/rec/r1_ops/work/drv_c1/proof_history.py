"""Only the failed C proof is an allocated predecessor; bootstrap had no ID."""
import os, subprocess
from pathlib import Path
b=Path('/project/community/jjyeung/okh7/i_7f1589c1.f172180')
rows=subprocess.run(['sacct','-X','-n','-P','-S','2026-11-17','--name','a15_cot_ap05b8ac69','-o','JobIDRaw,JobName%64,State,ExitCode'],check=True,capture_output=True,text=True,timeout=60).stdout
seen=[]
for line in rows.splitlines():
 if not line.strip():continue
 r=line.strip().rstrip('|').split('|')
 if r!=['172180','a15_cot_ap05b8ac69','FAILED','1:0']:raise SystemExit('REFUSED: unexpected C accounting history: '+line)
 seen.append(r)
if len(seen)!=1:raise SystemExit('REFUSED: FAILED 172180 accounting missing or ambiguous')
if (b/'job.id').read_text().strip()!='172180':raise SystemExit('REFUSED: moved proof ID differs')
for name in ('sbatch.out.a1_bootstrap','submission.started.a1_bootstrap','a.json.a1_bootstrap'):
 p=b/name
 if p.is_symlink() or not p.is_file():raise SystemExit('REFUSED: rejected bootstrap provenance missing')
if (b/'sbatch.out.a1_bootstrap').stat().st_size:raise SystemExit('REFUSED: bootstrap attempt has a submission receipt')
print('PASS history: FAILED 172180 and rejected bootstrap only')
