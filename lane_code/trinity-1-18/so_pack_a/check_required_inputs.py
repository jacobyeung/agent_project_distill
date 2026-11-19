"""Refuse missing local build/harness inputs by name. Never stages data."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pack as P

def check(manifest,group):
    items=[x for x in manifest['inputs'] if x['group']==group]
    P.need(items,'Unknown required-input group: '+group)
    P.need(all(x.get('location')=='local' for x in items),'Use the read-only remote preflight and native CPU stage for Orchard inputs')
    return P.required_inputs(dict(required_inputs=items))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--group',required=True);a=p.parse_args()
    try:print(json.dumps(check(P.read(a.manifest),a.group),sort_keys=True))
    except (P.Rejected,OSError,KeyError) as e:print('REJECTED: '+str(e),file=sys.stderr);sys.exit(1)
