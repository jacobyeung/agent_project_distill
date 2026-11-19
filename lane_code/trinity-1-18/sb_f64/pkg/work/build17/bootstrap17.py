from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build17'
for name in ('run.sh','test16.py'):
    raw=(L/'work/build16'/name).read_text().replace("work/build16'","work/build17'").replace("'B16_PROOF'","'B17_PROOF'")
    if name=='test16.py':raw=raw.replace("str(B)]","str(B),str(L/'work/build16')]")
    (B/('test17.py' if name=='test16.py' else name)).write_text(raw)
