import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import resolve
p=argparse.ArgumentParser();p.add_argument('--pool',required=True);p.add_argument('--listing',required=True);p.add_argument('--output',required=True)
a=p.parse_args();resolve(Path(__file__).resolve().parents[1],a.pool,a.listing,a.output)
