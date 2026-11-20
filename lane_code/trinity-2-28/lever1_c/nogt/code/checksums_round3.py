"""Append current hashes; preserve the complete existing checksum history."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from round3 import ROOT, OUT, BASE, sha, preserved_npzs

def main():
    path=OUT/'SHA256SUMS'
    assert path.read_bytes().startswith((BASE/'SHA256SUMS').read_bytes())
    preserved_npzs()
    latest={}
    for line in path.read_text().splitlines():
        digest,name=line.split('  ',1);latest[name]=digest
    paths=[p for folder in (ROOT/'code',OUT,ROOT/'logs') for p in folder.rglob('*') if p.is_file() and p!=path]
    paths += [ROOT/n for n in ('ark_ref_list.txt','ark_ref_stage.log','arkit_listing.json','ref_arkit_listing.json')]
    appended=[]
    for p in sorted(paths):
        name=str(p.relative_to(ROOT));digest=sha(p)
        if latest.get(name)!=digest:appended.append(f'{digest}  {name}\n')
    with path.open('a') as f:f.writelines(appended)
    print(f'Appended {len(appended)} new/current checksum entries; old lines and 15 existing NPZ hashes preserved.')

if __name__=='__main__':main()
