"""Restore local metadata dependencies from pinned source files after unpacking code."""
from common import *

def main():
 assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
 cfg=js(ROOT/'config/SOURCES.json')['input_sha256']
 copies={'/scratch/jjyeung/orch_n30/sb_ktow/inputs/K1_MANIFEST.arkit_timing.json':'inputs/local/K1_MANIFEST.json','/scratch/jjyeung/devs1_r2/REQUEST.json':'inputs/local/DEVS1_REQUEST.json','/scratch/jjyeung/orch_n30/e3_geom/work/harness/out/FITS.json':'inputs/local/FITS.json'}
 for source,dest in copies.items():
  target=ROOT/dest
  if target.exists():assert sha(target)==cfg[source];continue
  b=read(source);assert PINS[str(local(source))]==cfg[source];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
 write(ROOT/'out/LOCAL_STAGE.json',dict(status='PASS',copies=copies))
if __name__=='__main__':main()
