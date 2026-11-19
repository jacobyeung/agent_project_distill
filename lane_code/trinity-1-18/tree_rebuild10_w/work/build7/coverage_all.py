"""Aggregate only exact-source monitoring receipts, then classify external inputs."""
import json,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7'
sources=[]
for root in (L/'work/build5/proofs',L/'work/build6/proofs',B/'proofs'):
 for p in root.rglob('source_hashes.json'):
  folder=p.parent
  if (folder/'results.json').exists() and (folder/'hits.json').exists():sources.append(str(folder))
subprocess.run([sys.executable,'-I','-s','-B',str(B/'coverage.py'),*sorted(sources)],check=True)
subprocess.run([sys.executable,'-I','-s','-B',str(B/'classify_coverage.py')],check=True)
