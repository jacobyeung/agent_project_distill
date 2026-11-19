from pathlib import Path
L=Path(__file__).resolve().parents[2];r=L/'work/build23/proofs/capacity/400/q/p'
for p in sorted((p for p in r.rglob('*') if p.is_file()),key=lambda p:p.stat().st_size,reverse=True)[:10]:print(p.stat().st_size,p.relative_to(r))
