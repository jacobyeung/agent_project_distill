"""Fresh interpreter entry for the original-policy proof."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from adapter import load
from proof import run

def main():
    p=argparse.ArgumentParser()
    for name in ('reference','request','spec','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();run(a.reference,a.request,load(a.spec),a.out)
if __name__=='__main__':main()
