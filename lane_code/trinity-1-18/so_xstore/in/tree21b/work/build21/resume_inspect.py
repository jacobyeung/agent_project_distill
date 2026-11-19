from pathlib import Path
import json
B=Path(__file__).resolve().parent
root=B/'proofs/capacity'
for directory in sorted(root.iterdir()):
    if directory.is_dir():
        files=[p for p in directory.rglob('*') if p.is_file()]
        print(directory.name, sum(p.stat().st_size for p in files), len(files))
        if directory.name in ('400','600'):
            for p in files:
                if p.stat().st_size>40_000_000:print('  ',p.relative_to(root),p.stat().st_size)
for step in ('400','600'):
    p=root/step/'q/RESULT.json'
    if p.exists():
        value=json.loads(p.read_text());print(step,value.get('status'),value.get('steps'),value.get('refusal'))
