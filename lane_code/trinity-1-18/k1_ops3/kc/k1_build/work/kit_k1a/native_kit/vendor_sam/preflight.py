"""Verify all staged PNG bytes and identities without importing torch."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import argparse,time
from PIL import Image

def audit(manifest,root):
 m=json.loads(Path(manifest).read_text());validate_manifest(m);root=scratch(root);total=0;seen=set();started=time.monotonic()
 for c in m['captures']:
  for f in c['frames']:
   p=root/f['path']
   if f['path'] not in seen:
    if sha(p)!=f['sha256']:raise ValueError('PNG content mismatch '+str(p))
    with Image.open(p) as im:
     if im.format!='PNG' or list(im.size)!=c['hw'][::-1]:raise ValueError('PNG size/format mismatch')
     im.verify()
    seen.add(f['path']);total+=p.stat().st_size
 return dict(status='pass',captures=len(m['captures']),frames=len(seen),bytes=total,seconds=time.monotonic()-started,manifest_sha256=sha(manifest))
def main():
 p=argparse.ArgumentParser(__doc__);p.add_argument('--manifest',required=True);p.add_argument('--frames',required=True);p.add_argument('--out',required=True);a=p.parse_args();dump(a.out,audit(a.manifest,a.frames))
if __name__=='__main__':main()
