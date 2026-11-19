"""Run the unchanged A4 unpacker with an explicit import path under isolated Python."""
import argparse
from pathlib import Path
import runpy
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def main():
    p=argparse.ArgumentParser(add_help=False);p.add_argument('--operator',required=True)
    a,rest=p.parse_known_args();root=package_root(a.operator)
    for name in ('unpack_return.py','fetch_return.py'):
        checked(root/name,read(HERE/'A4_PINS.json')['operators'][name])
    sys.path.insert(0,str(root));sys.argv=[str(root/'unpack_return.py'),*rest]
    runpy.run_path(str(root/'unpack_return.py'),run_name='__main__')

if __name__=='__main__':main()
