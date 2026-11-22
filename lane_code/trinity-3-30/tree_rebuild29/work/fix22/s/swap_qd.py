"""Swap the source tree of a sealed kit (qd) to another tree, following W/w24y2/out/apply_24m4x.py.

Usage: python -I swap_qd.py KIT_IN TREE_DIR OUT_DIR [EXPECT_TREE_SEAL]
KIT_IN is read only. OUT_DIR must not exist; it receives OUT_DIR/kit (the new kit),
OUT_DIR/u/<sha256 of decoded k/c0.json> (the code capsule the kit pins by u/ path) and OUT_DIR/RESULT.json.
Changed members (as in apply_24m4x.py minus its extent change): k/7.json, k/c0.json, k/a.json and the tar
it names, k/p.json (code_sha256, uploads, pin_paths), k/c.json (code -> k/7.json), k/n.json (code -> u/<c0>),
SHA256SUMS.txt, BUILD.json. Run with the old tree to prove the procedure is the identity on the reviewed kit.
"""
from pathlib import Path
import base64, hashlib, json, shutil, sys


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    value = json.loads(Path(path).read_bytes())
    if isinstance(value, dict) and value.get('encoding') == 'base64-json':
        raw = base64.b64decode(value['payload'], validate=True)
        if hashlib.sha256(raw).hexdigest() != value['sha256']:
            raise ValueError('Capsule differs: ' + str(path))
        return json.loads(raw)
    return value


def write(path, raw):
    path = Path(path)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    path.write_bytes(raw)
    path.chmod(mode)


def cap(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    write(path, (json.dumps(dict(encoding='base64-json', payload=base64.b64encode(raw).decode(),
                                 sha256=hashlib.sha256(raw).hexdigest())) + '\n').encode())


def main(kit_in, tree, out, expect=None):
    kit_in, tree, out = Path(kit_in).resolve(), Path(tree).resolve(), Path(out).resolve()
    sys.path.insert(0, str(tree))
    from student_pilot.source_seal import inventory, archive, check_archive
    from student_pilot.p3_provenance import file_pin
    from launch_r1.build import verify
    from student_pilot.p3_provenance import digest
    base_seal = verify(kit_in)
    base_tree = load(kit_in / 'k/a.json')['source']['tree_sha256']
    before = {str(p.relative_to(kit_in)): sha(p) for p in kit_in.rglob('*') if p.is_file()}
    files = inventory(tree)
    seal = digest(files)
    if expect and seal != expect:
        raise ValueError('Tree seal differs: ' + seal)
    out.mkdir(mode=0o700)
    k = out / 'kit'
    shutil.copytree(kit_in, k, copy_function=shutil.copy2)
    packed = out / 't.tar'
    archive(tree, packed, files, compress=True)
    check_archive(file_pin(packed), files)
    for rel in ('k/7.json', 'k/c0.json'):
        value = load(k / rel)
        value.update(files=files, tree_sha256=seal, commit='sha256:' + seal)
        for field in ('sources', 'operation_sources'):
            if field in value:
                value[field] = {n: files[n] for n in value[field]}
        value['archive']['sha256'] = sha(packed)
        cap(k / rel, value)
    value = load(k / 'k/a.json')
    write(k / value['source']['path'], packed.read_bytes())
    value['source'].update(sha256=sha(packed), tree_sha256=seal)
    value['GO'] = False
    cap(k / 'k/a.json', value)
    spec = load(k / 'k/p.json')
    old = spec['code_sha256']
    raw = base64.b64decode(json.loads((k / 'k/c0.json').read_bytes())['payload'])
    h = hashlib.sha256(raw).hexdigest()
    spec['code_sha256'] = h
    for item in spec['uploads']:
        if item['sha256'] == old:
            item.update(sha256=h, bytes=len(raw))
            for field in ('path', 'opaque_name', 'name'):
                if field in item:
                    item[field] = item[field].replace(old, h)
    spec['pin_paths'] = {v['sha256']: spec['namespace'] + '/u/' + v['sha256'] for v in spec['uploads']}
    cap(k / 'k/p.json', spec)
    for rel in ('k/c.json', 'k/n.json'):
        value = load(k / rel)
        value['code'] = dict(path='k/7.json', sha256=sha(k / 'k/7.json')) if rel == 'k/c.json' else dict(path='u/' + h, sha256=h)
        cap(k / rel, value)
    (out / 'u').mkdir()
    (out / 'u' / h).write_bytes(raw)
    checks = {str(p.relative_to(k)): sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('BUILD.json', 'SHA256SUMS.txt')}
    write(k / 'SHA256SUMS.txt', ''.join(v + '  ' + n + '\n' for n, v in sorted(checks.items())).encode())
    value = load(k / 'BUILD.json')
    value.update(source_seal=seal, kit_sha256=sha(k / 'SHA256SUMS.txt'), config_sha256=sha(k / 'k/c.json'), GO=False)
    cap(k / 'BUILD.json', value)
    new_seal = verify(k)
    after = {str(p.relative_to(k)): sha(p) for p in k.rglob('*') if p.is_file()}
    changed = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    packed.unlink()
    result = dict(base_kit=base_seal, base_tree=base_tree, tree_sha256=seal, tree_tar_sha256=after[load(k / 'k/a.json')['source']['path']],
                  tree_tar_path=load(k / 'k/a.json')['source']['path'], kit=new_seal, identity=new_seal == base_seal,
                  changed=changed, changed_sha256={n: after.get(n) for n in changed},
                  code_capsule=dict(name='u/' + h, sha256=h, bytes=len(raw), old=old),
                  r1_training=files.get('student_pilot/r1_training.py'))
    (out / 'RESULT.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main(*sys.argv[1:])
