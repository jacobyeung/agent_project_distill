from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
source=B/'inputs/extents.json';retained=L/'work/merge11/proofs/text/retained_extents.json'
assert source.is_file() and not retained.exists()
source.rename(retained)
(L/'work/merge11/proofs/text/PAUSE.json').write_text('{"reason":"The proof reloads the same extent receipt per row. Stop it through its input pin, then reuse one reader per stream.","cluster_kill":false}\n')
