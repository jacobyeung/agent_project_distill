from pathlib import Path
p=Path('code/common.py');s=p.read_text()
a=s.index('def code_pins():');b=s.index('\ndef done_valid(',a)
s=s[:a]+'''DELIVERY_SCRIPTS=('cpu.sh','gpu_environment.sh','run_A.sh','run_B.sh','run_C.sh')
def code_pins():
 paths=[p for p in (ROOT/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md')]
 paths += [p for p in (ROOT/'configs').glob('*.json') if p.name!='CODE_REVIEW.json']
 paths += [ROOT/'scripts'/n for n in DELIVERY_SCRIPTS]
 return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
''' +s[b:]
p.write_text(s)
p=Path('code/dryrun.py');s=p.read_text().replace("('A0','deployed')", "('A0','deployed','A0_deployed')");s=s.replace("result=dict(status=status,gpu_hours_used=0", "result=dict(status=status,code_sha256=digest(code_pins()),gpu_hours_used=0");p.write_text(s)
p=Path('code/runner.py');s=p.read_text().replace("if read_json(ROOT/'out/DRYRUN.json')['status']!='PASS':raise RuntimeError('BLOCKER: section 6 dry run has not passed')", "dry=read_json(ROOT/'out/DRYRUN.json')\n if dry['status']!='PASS' or dry.get('code_sha256')!=digest(code_pins()):raise RuntimeError('BLOCKER: section 6 dry run has not passed for current code')");p.write_text(s)
p=Path('code/artifacts.py');s=p.read_text().replace("code_pins();edited();placeholders();print('review artifacts written')", "pins=code_pins();write_json(ROOT/'out/CODE_SHA256.json',dict(files=pins,code_sha256=digest(pins)));edited();placeholders();print('review artifacts written')");p.write_text(s)
