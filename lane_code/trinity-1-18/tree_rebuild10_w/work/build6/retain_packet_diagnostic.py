from pathlib import Path
L=Path(__file__).resolve().parents[2];P=L/'work/build6/proofs/packet'
target=P/'initial_results.json'
if not target.exists():target.write_bytes((P/'results.json').read_bytes())
