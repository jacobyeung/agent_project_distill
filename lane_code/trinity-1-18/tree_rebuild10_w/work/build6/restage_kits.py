"""Retain the previous kit bytes and restage the current source from empty."""
import json,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
old=json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256']
saved=B/('kits_'+old[:8])
if saved.exists():raise ValueError('Previous kit retention folder already exists')
(B/'kits').rename(saved)
for script in ('build_kits.py','seal.py','record_adaptations.py','make_delivery.py'):
 subprocess.run([sys.executable,'-I','-s','-B',str(B/script)],check=True)
