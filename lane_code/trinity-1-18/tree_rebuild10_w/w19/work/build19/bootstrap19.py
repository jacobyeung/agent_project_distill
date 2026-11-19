from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]; B=L/'work/build19'; P=L/'work/build18'
(L/'work/tmp').mkdir(exist_ok=True)
def size(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file() and not x.is_symlink())
(B/'STORAGE_START.json').write_text(json.dumps(dict(workspace=size(L),temporary=size(L/'work/tmp'))))
for name in ('run.sh','test18.py','native18.py','kits18.py','suite18.py','packet18.py','packet_inputs18.py','real18.py','storage18.py','compare18.py','delta_coverage18.py','delivery18.py','integrity18.py'):
    s=(P/name).read_text().replace("B=L/'work/build18'","B=L/'work/build19'").replace('B18_PROOF','B19_PROOF')
    if name not in ('native18.py','test18.py','delta_coverage18.py'):
        s=s.replace('work/build18','work/build19').replace('BUILD18_REPORT','BUILD19_REPORT').replace('tree_rebuild_b18_','tree_rebuild_b19_').replace('Build 18','Build 19')
    if name=='test18.py':s=s.replace("str(L/'work/build17')]","str(L/'work/build17'),str(L/'work/build18')]")
    if name=='delta_coverage18.py':s=s.replace('w17b','w18').replace('build-17','build-18').replace('build-18 observations','build-19 observations')
    if name=='suite18.py':s=s.replace("'work/build19/inputs',","'work/build19/inputs','work/build18/inputs',")
    (B/name.replace('18','19')).write_text(s)
(B/'STATUS.md').write_text('Build 19: GO=false. The verified component deferral and official-read guards are being implemented.\n')
