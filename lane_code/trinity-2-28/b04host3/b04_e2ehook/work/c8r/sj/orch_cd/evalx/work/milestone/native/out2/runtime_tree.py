from pathlib import Path

from common import OUT, digest, load, local, sha


EXPECTED_SOURCES_SHA = 'b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
MANIFEST = OUT/'RUNTIME_TREE.json'


def verified_sources(root):
    root = local(root)
    recorded = load(MANIFEST)
    if (recorded.get('schema') != 'legs1-runtime-tree-v1'
            or recorded.get('sources_sha256') != EXPECTED_SOURCES_SHA
            or digest(recorded['sources']) != EXPECTED_SOURCES_SHA
            or recorded['files'] != len(recorded['sources'])):
        raise ValueError('Recorded runtime-tree hash differs')
    actual = {}
    for path in sorted(root.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            if not local(path).is_relative_to(root):
                raise ValueError('Runtime tree contains an external file')
            actual[str(path.relative_to(root))] = sha(path)
    if actual != recorded['sources']:
        changed = sorted(k for k in actual.keys() | recorded['sources'].keys()
                         if actual.get(k) != recorded['sources'].get(k))
        raise ValueError('Runtime tree hash mismatch: '+', '.join(changed[:8]))
    return actual


def identity(root, sources):
    value = digest(sources)
    if value != EXPECTED_SOURCES_SHA:
        raise ValueError('Runtime tree identity differs')
    return dict(root=str(local(root)), sources_sha256=value, files=len(sources),
                identity_kind='canonical_relative_path_file_sha256_map')
