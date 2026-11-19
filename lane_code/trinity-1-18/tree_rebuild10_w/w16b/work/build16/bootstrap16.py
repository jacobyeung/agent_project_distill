from pathlib import Path
L=Path(__file__).resolve().parents[2]
B=L/'work/build16'
prior=L.parent/'w16/work/build16'
for name in ('inspect16.py','inputs16.py','census16.py'):
    (B/name).write_bytes((prior/name).read_bytes())
(B/'run.sh').write_bytes((L/'work/build15/run.sh').read_bytes())
