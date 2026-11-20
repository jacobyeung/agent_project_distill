"""Deterministically partition a validated capture manifest without crossing scenes."""
import sys,argparse,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bindings as B
from run import validate_manifest

def partition(m,count):
 if count<1 or count>16:raise ValueError('Choose between 1 and 16 cards')
 shards=[]
 for i in range(count):
  x=copy.deepcopy(m);x['captures']=[c for n,c in enumerate(sorted(m['captures'],key=lambda c:c['canonical'])) if n%count==i]
  if x['captures']:shards.append((i,x))
 return shards
if __name__=='__main__':
 p=argparse.ArgumentParser(__doc__);p.add_argument('--manifest',required=True);p.add_argument('--out',required=True);p.add_argument('--cards',type=int,required=True);a=p.parse_args();m=validate_manifest(B.load(a.manifest))
 for i,x in partition(m,a.cards):B.write(Path(a.out)/f'manifest_{i}.json',x)
