"""Add V3 frame ranking; GT presence is always identified as an oracle arm."""
import argparse
import csv
import json
from pathlib import Path
from .io import rows,write_rows,dump,sha
from .prepare import mdg_presence,call_counts
from .audit_labels import AUDIT


def rank(candidates,out,mdg_root=None):
    groups=rows(candidates);presence={}
    if mdg_root is None:
        allowed={(g['scene'],g['name']) for g in groups}
        with AUDIT.open() as stream:
            for r in csv.DictReader(stream):
                if (r['scene'],r['name']) in allowed:
                    presence[r['scene'],r['name'],int(r['slot'])]=float(r['visible']=='True')
    for g in groups:
        p=mdg_presence(mdg_root,g['scene'],g['name']) if mdg_root else [presence[g['scene'],g['name'],k] for k in range(32)]
        g['v3_slots']=sorted(range(32),key=lambda k:(-p[k],k))[:4]
        g['v3_presence_source']='mdg' if mdg_root else 'GT_PRESENCE_ORACLE'
    write_rows(out,groups)
    source_meta=Path(str(candidates)+'.meta.json')
    meta=json.loads(source_meta.read_text()) if source_meta.exists() else {}
    meta.update(parent_candidates_sha256=sha(candidates),v3_presence_source='mdg' if mdg_root else 'GT_PRESENCE_ORACLE',counts=call_counts(groups))
    if mdg_root is None:meta['v3_presence_sha256']=sha(AUDIT)
    dump(str(out)+'.meta.json',meta);return meta['counts']


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--candidates',required=True);p.add_argument('--out',required=True)
    p.add_argument('--mdg-root');a=p.parse_args();print(json.dumps(rank(a.candidates,a.out,a.mdg_root)))

if __name__=='__main__':main()
