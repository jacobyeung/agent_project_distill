"""Authenticate and materialize the exact selector import tree in a fresh directory."""
import hashlib,json,tarfile
from pathlib import Path

def selection_tree(bundle, target):
    bundle=Path(bundle);target=Path(target)
    code=json.loads((bundle/'c.json').read_text())
    archive=bundle/'t.tar'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=code['archive']['sha256']:
        raise ValueError('Selector archive differs')
    target.mkdir(mode=0o700)
    seen=set()
    with tarfile.open(archive) as tf:
        for member in tf:
            name=member.name;rel=Path(name)
            if (not member.isfile() or rel.is_absolute() or '..' in rel.parts or
                    name in seen or name not in code['files'] or member.size>32000000):
                raise ValueError('Unsafe selector archive member')
            raw=tf.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest()!=code['files'][name]:
                raise ValueError('Selector member differs')
            path=target/rel;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(raw)
            path.chmod(0o600);seen.add(name)
    if seen!=set(code['files']):raise ValueError('Selector inventory differs')
    return target
