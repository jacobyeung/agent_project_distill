from pathlib import Path
import json,os
L=Path(__file__).resolve().parents[2];B=L/'work/build21';P=L/'work/build20'
def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
B.mkdir(exist_ok=True)
(B/'STORAGE_START.json').write_text(json.dumps(dict(workspace=size(L),temporary=size(L/'work/tmp'),capacity_limit=3_000_000_000,increment_limit=3_500_000_000),indent=2))
for name in ('run.sh','test20.py','joblib.py','kit.py','jobtest.py','native20.py','native_assets20.py','real20.py','receipts.py','focused.py','upload.py'):
    text=(P/name).read_text().replace("B=L/'work/build20'","B=L/'work/build21'").replace('B20_PROOF','B21_PROOF').replace('B20_MONITOR_ROOT','B21_MONITOR_ROOT')
    if name=='test20.py':text=text.replace("str(L/'work/build18')","str(L/'work/build18'),str(L/'work/build19'),str(L/'work/build20')")
    (B/name.replace('20','21')).write_text(text)
for name in ('inputs','base','proofs'):(B/name).mkdir(exist_ok=True)
for name in ('config.json','kit_config.json','mix.json','component_rows.json'):
    p=P/'inputs'/name
    if p.exists():(B/'inputs'/name).write_bytes(p.read_bytes())
for name in ('joblib.py','kit.py'):(B/'base'/name).write_bytes((P/name).read_bytes())
(B/'STATUS.md').write_text('GO=false. Item 1 is in progress. The host is trinity-1-18. All writes remain inside the workspace. The capacity exception applies only to its fixed proof folder; other new outputs remain within the ordinary storage allowance.\n')
print((B/'STORAGE_START.json').read_text())
