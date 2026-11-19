"""Require unused export objects before minting twenty fresh capabilities."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

HELPER = Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py')

HELPER_SHA = 'b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d'

def main():
    if len(sys.argv) != 9:
        raise SystemExit('REFUSED: expected output, namespace, run, and five milestones')
    out, kit, run, *milestones = sys.argv[1:]
    if kit != '8865619b' or run != '6ed2c7aa' or milestones != ['m400', 'm600', 'mstop', 'mstopB', 'mstopC']:
        raise SystemExit('REFUSED: export plan differs')
    p = Path(out)
    if p.exists() or p.is_symlink():
        raise SystemExit('REFUSED: session destination already exists')
    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
        raise SystemExit('REFUSED: mint helper bytes differ')
    spec = importlib.util.spec_from_file_location('sealed_mint', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    token = helper.token()
    # The sealed training wrapper can publish a fallback slot under this prefix.
    # A CPU proof cannot create one; refuse unexpected state before minting.
    prefix = 'q8/d2d30e36/'+run+'_s'
    url = 'https://storage.googleapis.com/storage/v1/b/'+helper.BUCKET+'/o?'+urllib.parse.urlencode(dict(prefix=prefix, maxResults=1, fields='items(name),nextPageToken'))
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer '+token})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            import json
            listing = json.load(response)
    except (urllib.error.URLError, ValueError):
        raise SystemExit('REFUSED: cannot establish fallback export absence; no session minted') from None
    if not isinstance(listing, dict) or listing.get('items') or listing.get('nextPageToken'):
        raise SystemExit('REFUSED: fallback export namespace is occupied; no session minted')
    names = [f'q8/{kit}/{run}_{m}.tar.part{i:02d}-of-04' for m in milestones for i in range(4)]
    for name in names:
        url = 'https://storage.googleapis.com/storage/v1/b/'+helper.BUCKET+'/o/'+urllib.parse.quote(name, safe='')+'?fields=name,generation'
        request = urllib.request.Request(url, headers={'Authorization': 'Bearer '+token})
        try:
            with urllib.request.urlopen(request, timeout=60):
                raise SystemExit('REFUSED: export object exists; no session minted; preserve existing object: '+name)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise SystemExit('REFUSED: cannot establish export absence; no session minted') from None
    helper.token = lambda: token
    helper.mint(out, kit, run, milestones)
    print('PASS 20 export destinations absent; fresh ifGenerationMatch=0 sessions minted')

if __name__ == '__main__':
    main()
