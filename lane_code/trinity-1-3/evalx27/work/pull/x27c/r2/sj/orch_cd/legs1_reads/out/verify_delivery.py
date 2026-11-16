"""Verify output and runtime dependency inventories without running evaluation."""
import hashlib
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent

def main():
    count=0
    for manifest in (ROOT/'out/SHA256SUMS',ROOT/'out/DEPENDENCIES.sha256'):
        for line in manifest.read_text().splitlines():
            expected,name=line.split('  ',1);p=(ROOT/name).resolve()
            if not p.is_relative_to(ROOT):raise ValueError('Inventory path leaves lane')
            with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            if actual!=expected:raise ValueError('SHA256 differs: '+name)
            count+=1
    print(f'PASS: {count} output/dependency file hashes')
if __name__=='__main__':main()
