"""Install only the reviewed so_read additions; this never changes the sealed A10b tree."""
import argparse
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--enable-extensions',action='store_true');a=ap.parse_args()
    if not a.enable_extensions:raise Refusal('Extensions default OFF; require --enable-extensions')
    src=HERE/'so_read';dest=HERE/'extensions';manifest=read(src/'MANIFEST.json')
    if dest.exists():
        from runner228 import extensions
        extensions()
        print(json.dumps(dict(installed=str(dest),active_by_default=False,existing_verified=True)))
        return
    dest.mkdir(exist_ok=False)
    for name in ('01_bounded_read_caches.diff','02_atomic_scene_shards.diff','03_production_integration.diff'):
        pin=manifest['patches'][name];checked(src/name,pin)
        subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-i',str(src/name)],cwd=dest,check=True)
    from runner228 import extensions
    extensions()
    print(json.dumps(dict(installed=str(dest),active_by_default=False)))

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError) as e:print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
