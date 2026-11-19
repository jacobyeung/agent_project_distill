from pathlib import Path
import sqlite3
L=Path(__file__).resolve().parents[2]
for p in (L/'work/build23/proofs/capacity/400/q/p').glob('prepare_*/*/rows.sqlite'):
 with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as db:
  print(p.parent.name,db.execute('SELECT count(*), avg(length(row)), min(length(row)), max(length(row)) FROM rows').fetchone(),p.stat().st_size)
