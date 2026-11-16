"""Verify sealed bytes before any staging or execution."""
import json
from pathlib import Path
import re
import sys
from v import sha, checked

def main(root, build_only=False):
    root=Path(root); cert=json.loads((root/'ANON_OK.json').read_text())
    if not build_only and (cert.get('status')!='CLEAN' or cert.get('hits')!=0):
        raise ValueError('Scan refused')
    manifest=root/'SHA256SUMS.txt'
    if sha(manifest)!=cert['manifest_sha256']: raise ValueError('Manifest differs')
    expected=set()
    for line in manifest.read_text().splitlines():
        digest,name=line.split('  ',1);p=root/name
        if (name in expected or not re.fullmatch('[0-9a-f]{64}',digest)
                or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or sha(p)!=digest):
            raise ValueError('Kit differs')
        expected.add(name)
    actual={str(p.relative_to(root)) for d in ('b','k') for p in (root/d).rglob('*') if p.is_file()}
    actual.update(name for name in ('job.sh','job8.sh') if (root/name).is_file())
    if actual!=expected: raise ValueError('Executable inventory differs')
    cur=json.loads((root/'k/0.json').read_text())
    if not build_only and not re.fullmatch('(?:[0-9a-f]{40}|sha256:[0-9a-f]{64})',cur.get('commit') or ''): raise ValueError('Revision absent')
    for key in ('trainer','record'):
        pin=cur[key];p=root/'k'/Path(pin['file']).name
        if sha(p)!=pin['sha256']: raise ValueError('Deployment differs')
    return cert

if __name__=='__main__': main(sys.argv[1], '--build-only' in sys.argv[2:])
