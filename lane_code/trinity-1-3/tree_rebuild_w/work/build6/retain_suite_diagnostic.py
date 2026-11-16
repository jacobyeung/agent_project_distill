"""Retain first package receipts in their fixed proof folders before the final run."""
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6'
for variant in ('tree','base'):
 root=B/'proofs'/('suite_'+variant)
 for name in ('results.json','source_hashes.json','hits.json','temporary_sizes.json'):
  source=root/name;target=root/('diagnostic_'+name)
  if not target.exists():target.write_bytes(source.read_bytes())
for name in ('SUITE_COMPARISON.json','DELIVERY.json'):
 source=B/name;target=B/('DIAGNOSTIC_'+name)
 if source.exists() and not target.exists():target.write_bytes(source.read_bytes())
