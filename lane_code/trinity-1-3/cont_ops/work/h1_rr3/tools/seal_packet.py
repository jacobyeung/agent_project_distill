import ast,hashlib,json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ids=json.loads((H/'ids.json').read_text());upload=json.loads((H/'UPLOAD.json').read_text());tok=ids['tokens']
assert len((H/'EXPORT_OBJECTS.txt').read_text().splitlines())==44
assert len(set((H/'EXPORT_OBJECTS.txt').read_text().splitlines()))==44
assert json.loads((H/'payload/4.json').read_text())['production_go_granted'] is False
assert json.loads((H/'payload/over.json').read_text())['status']=='BLOCKED'
assert json.loads((H/'payload/review.json').read_text())['verdict']=='PENDING'
assert json.loads((H/'payload/staging.json').read_text())['status']=='PENDING'
assert '/scratch/jjyeung' not in (H/'payload/over.json').read_text()
for n in ('d.py','v.py','r.py'):
 src={'d.py':'derive_kit_h1.py','v.py':'staging_check.py','r.py':'orchard_records.py'}[n]
 assert sha(H/'payload'/n)==sha(H/'tools'/src)
for row in upload['files']:assert sha(H/'payload'/row['name'])==row['sha256']
assert sha(H/'build'/upload['archive'])==upload['sha256']
for p in list((H/'tools').glob('*.py'))+list((H/'tests').rglob('*.py'))+list((H/'payload').glob('*.py')):ast.parse(p.read_text(),filename=str(p))
for p in list((H/'payload').glob('*.sh'))+[H/'orch_h1.sh',H/'fin_h1.sh',H/'runtime/jb.sh',H/'tests/RERUN_CHAIN.sh']:subprocess.run(['/bin/bash','-n',str(p)],check=True)
# Check every present fixture byte against its own inventory; preserve missing source payload pins.
missing=[]
for line in (H/'build/fx/SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1);p=H/'build/fx'/n
 if p.is_file():assert sha(p)==h,n
 else:missing.append(n)
assert len(missing)==2
proof=json.loads((H/'evidence/cpu/fallback_fix2/result.json').read_text());assert proof['exit']==0 and proof['slot']['verified'] is True and proof['slot']['step']==200
# Size accounting includes retained test payloads; hashes below cover the primary packet and evidence records.
size=sum(p.stat().st_size for p in H.rglob('*') if p.is_file() and not any(n in p.relative_to(H).parts for n in ('.git','.aws','.codex','.agents')))

summary=dict(status='PASS',workspace_bytes_including_retained_outputs=size,fixture_missing_payloads=missing,identity=ids['identity'],contract=ids['contract'],cpu_step200_slot='PASS',four_rank_usr1='NOT RUN: operator rerun prepared; syntax checked only',production_go_granted=False)
(H/'evidence/final_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
files=[H/n for n in ('REPORT.md','DIFF.md','TOKENS_H1.json','ids.json','EXPORT_OBJECTS.txt','UPLOAD.json','orch_h1.sh','fin_h1.sh','FIX1.md','FIX2.md','REMOVAL_CANDIDATES.md','ORCHARD_LEDGER_PENDING.jsonl')]
for d in ('tools','tests','payload','runtime'):files.extend(p for p in (H/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend([H/'build'/upload['archive'],H/'build/over_local.json',H/'build/over_fx.json',H/'build/fx/SHA256SUMS.txt'])
files.extend(p for p in (H/'evidence').glob('*.json'))
files.extend([H/'evidence/derive.patch',H/'evidence/derivation_final.log',H/'evidence/stop_bridge/result.json',H/'evidence/staging_test/result.json',H/'evidence/cpu/chain_blocker.json',H/'evidence/cpu/fallback_fix2/result.json',H/'evidence/cpu/fallback_fix2/chain.log',H/'evidence/cpu/fallback_fix2/slots/A.json',H/'evidence/cpu/fallback_fix2/slots/A.sha256',H/'evidence/cpu/fallback_fix2/run/s2.json',H/'evidence/cpu/fallback_fix2/run/inputs/first_step_993.json'])
files.extend(p for p in (H/'evidence/review').iterdir() if p.is_file())
files.extend(p for p in (H/'evidence/fix2').iterdir() if p.is_file())
files.append(H/'evidence/fix2_before/hashes.json')
active_bytes=sum(p.stat().st_size for p in set(files))
assert active_bytes<2_000_000_000
summary.update(sealed_packet_bytes=active_bytes,sealed_packet_under_2GB=True)
(H/'evidence/final_checks.json').write_text(json.dumps(summary,indent=2)+'\n')
(H/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(H))+'\n' for p in sorted(set(files))))
print(json.dumps(summary,indent=2));print('manifest',sha(H/'SHA256SUMS.txt'),'files',len(set(files)))
