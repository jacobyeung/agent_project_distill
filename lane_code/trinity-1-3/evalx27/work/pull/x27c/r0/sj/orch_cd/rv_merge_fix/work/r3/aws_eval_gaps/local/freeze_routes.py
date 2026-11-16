"""Freeze CP1 routes exclusively from the complete pinned dev-noReVSI generations."""
import argparse,json,sys
from pathlib import Path
from common import ROOT,pin,sha
sys.path.insert(0,str(ROOT/'evaluator'))
from routing import freeze
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--direct',required=True,help='dev direct JSONL absolute-path@sha256')
p.add_argument('--routed',required=True,help='dev routed JSONL absolute-path@sha256')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();dev=ROOT/'inputs/DEV_ITEMS_noReVSI.jsonl'
table=freeze(dict(path=str(dev),sha256=sha(dev)),pin(a.direct),pin(a.routed))
with a.output.open('x') as f:json.dump(table,f,sort_keys=True,indent=2);f.write('\n')
print(str(a.output.resolve())+'@'+sha(a.output))
