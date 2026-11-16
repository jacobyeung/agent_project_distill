"""Collect only compiled-source, current-hash coverage from completed proofs."""
import json
from pathlib import Path
import subprocess
import sys

L=Path(__file__).resolve().parents[2]
folders=[]
for receipt in (L/'work/build5/proofs').rglob('results.json'):
    root=receipt.parent
    if 'suite_base' in root.parts or 'legacy_base' in root.parts:
        continue
    if not (root/'source_hashes.json').is_file():
        continue
    result=json.loads(receipt.read_text())
    if result.get('complete') and result.get('coverage_code_filter')=='compiled-source fingerprint':
        folders.append(str(root))
for name,args in [('coverage.py',sorted(folders)),('reconcile.py',[])]:
    subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5'/name),*args],check=True)
