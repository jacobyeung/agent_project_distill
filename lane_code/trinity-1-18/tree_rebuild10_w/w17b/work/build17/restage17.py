"""Retain the earlier owned kit directories; build the final kits from empty."""
from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build17'
old=B/'kits';retained=B/'retained_kits17'
assert old.is_dir() and not retained.exists()
old.rename(retained)
for script in (L/'work/n1fix2/seal.py',B/'kits17.py',B/'operator17.py'):
    result=subprocess.run([sys.executable,'-I','-s','-B',str(script)])
    if result.returncode:raise SystemExit(result.returncode)
