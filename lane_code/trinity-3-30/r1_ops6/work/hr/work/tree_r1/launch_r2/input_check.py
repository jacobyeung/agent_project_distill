"""Read-only source authentication before physical staging or GO."""
import base64
import hashlib
from pathlib import Path
import tarfile


def digest(path):
    with Path(path).expanduser().open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def sources(plan):
    checked, members = {}, []
    for name, entry in sorted(plan['entries'].items()):
        if 'required_parameter' in entry:
            raise ValueError('unbound_staging_parameter:'+entry['required_parameter'])
        if 'payload' in entry:
            if hashlib.sha256(base64.b64decode(entry['payload'],validate=True)).hexdigest() != entry['sha256']:
                raise ValueError('inline_sha_mismatch:'+name)
            continue
        source = entry.get('archive', entry.get('directory', entry))
        parts = source.get('parts', [])
        if not parts or not source.get('sha256'):
            raise ValueError('unpinned_staging_source:'+name)
        key = tuple(parts)
        if key not in checked:
            h = hashlib.sha256()
            for path in parts:
                with Path(path).expanduser().open('rb') as f:
                    for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
            checked[key] = h.hexdigest()
        if checked[key] != source['sha256']:
            raise ValueError('staging_source_sha_mismatch:'+name)
        if 'archive' in entry:
            members.append((name, entry))
    # Verify members without extraction or large temporary copies.
    for name, entry in members:
        source = entry['archive']
        if len(source['parts']) != 1:
            if source.get('inventory', {}).get(entry['member']) != entry['sha256']:
                raise ValueError('multipart_member_inventory_missing:'+name)
            continue
        with tarfile.open(Path(source['parts'][0]).expanduser()) as archive:
            f = archive.extractfile(entry['member'])
            if f is None or hashlib.file_digest(f,'sha256').hexdigest() != entry['sha256']:
                raise ValueError('archive_member_sha_mismatch:'+name)
    for role in ('bwrap','venv'):
        if role in plan:
            p = plan[role]
            if not p.get('sha256') or digest(p['file']) != p['sha256']:
                raise ValueError('runtime_source_sha_mismatch:'+role)
    return {'sources':len(checked), 'members':len(members), 'status':'PASS'}
