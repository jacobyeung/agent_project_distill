from pathlib import Path
L=Path(__file__).resolve().parents[2]
dest=L/'fixtures/grammar/work'
dest.mkdir(parents=True,exist_ok=True)
for name in ('trace_grammar.py','test_trace_grammar.py'):
    (dest/name).write_bytes((L/'work/rows_slices/work'/name).read_bytes())
