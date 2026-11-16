"""Archive small GPU receipts and metrics; exclude model and feature tensors."""
import argparse,tarfile
from pathlib import Path

def collect(results,card,ledger,archive):
    results=Path(results);card=Path(card);ledger=Path(ledger);archive=Path(archive)
    files=[(p,'results/'+str(p.relative_to(results))) for p in results.rglob('*') if p.is_file() and p.suffix in ('.json','.log','.md')]
    files += [(p,'card/'+str(p.relative_to(card))) for p in card.rglob('*') if p.is_file() and p.suffix in ('.json','.md')]
    if ledger.is_file():files.append((ledger,'GPU_TIME.json'))
    size=sum(p.stat().st_size for p,_ in files)
    if size>50_000_000:raise ValueError('Small-result payload exceeds 50 MB; inspect before transfer')
    with tarfile.open(archive,'w:gz') as tf:
        for p,name in sorted(files):tf.add(p,arcname=name,recursive=False)
    print(dict(files=len(files),uncompressed_bytes=size,archive_bytes=archive.stat().st_size))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--card',required=True);p.add_argument('--ledger',required=True);p.add_argument('--archive',required=True);a=p.parse_args();collect(a.results,a.card,a.ledger,a.archive)
