def check_authority(kit):
    """Authenticate the deployed authority before checking its resource limits."""
    import hashlib
    import json
    import re
    from pathlib import Path
    manifest = kit/'SHA256SUMS.txt'
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError('Missing or linked derived manifest')
    pins = {}
    for line in manifest.read_text().splitlines():
        digest, name = line.split('  ', 1)
        if (not re.fullmatch('[0-9a-f]{64}', digest) or name in pins
                or Path(name).is_absolute() or '..' in Path(name).parts):
            raise ValueError('Invalid derived manifest')
        pins[name] = digest
    path = kit/'k/4.json'
    if (path.parent.is_symlink() or path.is_symlink() or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != pins.get('k/4.json')):
        raise ValueError('Authority SHA differs from derived manifest')
    auth = json.loads(path.read_bytes())
    validate(auth)
    for key, value in dict(config_sha256='@IDENTITY@',
                           source_revision='sha256:@TREE@',
                           admission_contract_sha256='@CONTRACT@').items():
        if auth.get(key) != value:
            raise ValueError('Authority identity differs: '+key)
    print('PASS sealed p/t/u authority; k/4.json SHA matches derived manifest')
    return auth
