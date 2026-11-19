"""Smoke-test r400 unpacking and scoring with explicitly synthetic local metadata.

Usage: check_local_return.py BUILD PROOF FRESH_OUTPUT_UNDER_OUT_PKG
This creates mock authentication receipts for a local test, never an Orchard result.
"""
import json
from pathlib import Path
import subprocess
import sys

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import build_ownread as B


def main(build, proof, output):
    build, proof, output = [Path(p).resolve() for p in (build, proof, output)]
    output.mkdir(parents=True, exist_ok=False)
    plan = json.loads((build/'READ_PLAN.json').read_text())
    cfg = json.loads((build/'src/9.json').read_text())
    public = json.loads((build/'package/0.json').read_text())
    pin = dict(plan['export_binding'], schema='h1-export-pins-v1', preparation={})
    for name, digest in cfg['export_binding']['preparation_sha256'].items():
        pin['preparation'][name] = dict(sha256=digest, bytes=1,
                                      path='prep/'+name+'.json', source_path='/fixture/'+name)
    inputs = dict(archives=[dict(sha256=pin['archive_sha256'])], files={})
    for key, member in [('artifact', 'artifact.json'), ('heads', 'heads.pt'),
                        ('full_weights', 'full_weights/full_weights.json')]:
        pin[key] = dict(bytes=1, sha256='0'*64)
        inputs['files'][key] = dict(pin[key], path=cfg['logical']+'/d/'+pin['member_directory']+'/'+member)
    files = {str(p.relative_to(proof/'ret_strict')): p.read_bytes()
             for p in (proof/'ret_strict').rglob('*') if p.is_file()}
    identity = json.loads(files['metadata/IDENTITY.json'])
    identity.update(plan=public['plan_sha256'], inputs=B.canonical(inputs), reads=plan['read_settings'],
                    operator_sha256=B.sha((build/'tower_sequence.py').read_bytes()))
    for name, value in [('IDENTITY', identity), ('INPUTS', inputs), ('EXPORT_PIN', pin)]:
        files['metadata/'+name+'.json'] = B.jbytes(value)
    for name in list(files):
        if name.endswith('/environment.json'):
            env = json.loads(files[name]); env['binding']['step'] = pin['step']
            env['binding']['lineage'] = pin['lineage']; files[name] = B.jbytes(env)
    raw = B.tarbytes(files); archive = output/'fixture.tgz'; archive.write_bytes(raw)
    receipt = dict(plan_sha256=public['plan_sha256'], token=public['token']+'00000001',
                   job=1, synthetic=False, archive_bytes=len(raw), archive_sha256=B.sha(raw),
                   complete=True, status='COMPLETE')
    exit_path = output/'MOCK_EXIT.json'; exit_path.write_bytes(B.jbytes(receipt))
    subprocess.run([sys.executable, '-B', str(build/'unpack_return.py'), '--archive', str(archive),
                    '--exit', str(exit_path), '--out', str(output/'unpacked')], check=True)
    subprocess.run([sys.executable, '-B', str(KIT/'ownread.py'), '--package', str(build),
                    '--root', str(output/'unpacked'), '--out', str(output/'score')], check=True)
    print('PASS: workspace unpack/scorer workflow with synthetic metadata, not an Orchard measurement.')


if __name__ == '__main__': main(*sys.argv[1:])
