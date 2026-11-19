from pathlib import Path
import sys
D=Path(__file__).resolve().parent;L=D.parents[1]
sys.path.insert(0,str(D))
# Do not import the patch script: installation is deliberately separate.
def put(p,s):
 old=L/'attic/build24h'/p.relative_to(L);old.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and not old.exists():p.rename(old)
 p.write_text(s)
for k in (L/'work/build24/kits/n',L/'out/kit_n_go'):
 put(k/'b/pc.sh',(D/'live.sh').read_text());put(k/'b/sr.py',(D/'sr.py').read_text())
 s=(k/'job.sh').read_text().replace('( python3 -B -I -s -B "$ROOT/b/x.py"', '( set +e; python3 -B -I -s -B "$ROOT/b/x.py"').replace('"$ROOT/b/l.py" "$ROOT" ) &','"$ROOT/b/l.py" "$ROOT"; exit "${PIPESTATUS[0]}" ) &')
 put(k/'job.sh',s)
