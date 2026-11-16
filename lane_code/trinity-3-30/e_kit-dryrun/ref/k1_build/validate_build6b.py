"""Validate the sealed batch, completed rehearsal, and portable archive."""
import ast
import base64
import difflib
import hashlib
import io
import json
from pathlib import Path
import tarfile

import job_support as H
from audit_config import audit
import rh_coverage as C

ROOT = Path(__file__).resolve().parent


def digest(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024**2), b''):
        h.update(chunk)
    return h.hexdigest()


def main():
    config = json.loads((ROOT/'packet/CONFIG.json').read_text())
    fields = audit(config)
    assert fields == json.loads((ROOT/'evidence/REPORT6_FIELD_AUDIT.json').read_text())
    assert config['allocation_seconds'] == 10800 and 'deadline_unix' not in config
    script = (ROOT/'packet/a7e31d84.sh').read_text()
    encoded = ast.parse(script.splitlines()[7]).body[0].value.args[0].value
    baseline_protected = json.loads(
        (ROOT/'evidence/REPORT5_VALIDATION.json').read_text())['protected_unchanged']
    protected = {name:sha for name,sha in baseline_protected.items()
        if name.startswith('reference/')}
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(encoded))) as archive:
        embedded = {}
        current_bytes = {}
        for member in archive:
            raw = archive.extractfile(member).read()
            current_bytes[member.name] = raw
            if member.name == 'a.json':
                assert json.loads(raw) == config
            else:
                assert raw == (ROOT/member.name).read_bytes(), member.name
            embedded[member.name] = hashlib.sha256(raw).hexdigest()
    for name, expected in protected.items():
        assert embedded[name] == expected, name
    assert H.sha(ROOT/'manifest_v2/a40fbc19.json') == config['manifest_sha256']
    assert H.sha(ROOT/'packet/d6e92a81.tar') == config['code']['sha256']
    assert config['manifest_sha256'] == baseline_protected['manifest_v2/a40fbc19.json']
    assert config['code']['sha256'] == baseline_protected['packet/d6e92a81.tar']
    package = json.loads((ROOT/'packet/PACKAGE.json').read_text())
    assert H.sha(ROOT/'packet/a7e31d84.sh') == package['batch_sha256']
    assert (ROOT/'packet/a7e31d84.sh').stat().st_size == package['batch_bytes']
    saved = max((ROOT/'rh').glob('RH_1_3.saved_*.tar'), key=lambda p:int(p.stem.split('_')[-1]))
    with tarfile.open(saved) as archive:
        for member in archive:
            if member.name == 'packet/a7e31d84.sh':
                old_script = archive.extractfile(member).read()
                break
        else:
            raise AssertionError('Baseline batch absent')
    assert hashlib.sha256(old_script).hexdigest() == 'fc9ed8a8ef64bd3c287939f3a804a0f5c63fd52c036b18255426461415bd9636'
    old_encoded = ast.parse(old_script.decode().splitlines()[7]).body[0].value.args[0].value
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(old_encoded))) as archive:
        old_bytes = {m.name:archive.extractfile(m).read() for m in archive}
    assert set(old_bytes) == set(current_bytes)
    changes = []
    for name in sorted(current_bytes):
        before, after = old_bytes[name].decode(), current_bytes[name].decode()
        if name == 'a.json':
            before = json.dumps(json.loads(before), indent=2, sort_keys=True)+'\n'
            after = json.dumps(json.loads(after), indent=2, sort_keys=True)+'\n'
        changes.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
            fromfile='fc9ed8a8/'+name, tofile='part_b_short_job/'+name))
    assert ''.join(changes) == (ROOT/'evidence/REPORT6_JOB.diff').read_text()
    batch = Path(json.loads((ROOT/'evidence/BATCH_LATEST.json').read_text())['run'])
    result = json.loads((batch/'RESULT.json').read_text())
    assert result['passed'] and len(result['cases']) == 9
    for scenario, row in result['cases'].items():
        assert row['passed'], scenario
        identity = json.loads((batch/scenario/'CONFIG_IDENTITY.json').read_text())
        assert identity['production_equal_except_transport']
        assert set(identity['changed_fields']) == {'pool', 'cloud', 'pointer'}
    verifiers = json.loads((batch/'success/VERIFIERS.json').read_text())
    assert any(r['role']=='anchors unpack' and r['production_verifier'] for r in verifiers)
    assert any(r['role']=='inventory' and r['detail'].get('anchors') and r['production_verifier'] for r in verifiers)
    copy = json.loads((batch/'success/ANCHOR_COPY.json').read_text())
    H.dump(ROOT/'evidence/REPORT6B_REHEARSAL.json', dict(passed=True, run=str(batch),
        result=result, production_config_transport_only=True, production_anchor_copy=copy,
        success_verifiers=verifiers))
    component = Path(json.loads((ROOT/'evidence/V2_LATEST.json').read_text())['run'])
    component_result = json.loads((component/'RESULT.json').read_text())
    assert component_result['component_rehearsal_passed']
    assert component_result['prepared']['passed']
    assert component_result['resume']['first_commits'] == 3
    assert component_result['resume']['final_commits'] == 6
    assert component_result['allocation_budget_resume']['passed']
    assert component_result['expired_deadline']['passed']
    H.dump(ROOT/'evidence/REPORT6B_COMPONENT.json', dict(run=str(component), **component_result))
    coverage = C.union([(str(batch), json.loads((batch/'COVERAGE.json').read_text())),
                        (str(component), json.loads((component/'COVERAGE.json').read_text()))])
    H.dump(ROOT/'evidence/REPORT6B_COVERAGE.json', coverage)
    (ROOT/'evidence/REPORT6B_COVERAGE.txt').write_text(''.join(
        f"{name}: {row['executed']}/{row['total']} unexecuted={row['unexecuted_lines']}\n"
        for name,row in coverage.items()))
    H.dump(ROOT/'evidence/REPORT6B_VALIDATION.json', dict(passed=True, batch=package,
        embedded_config_equal=True, embedded_files=embedded, helpers_unchanged=protected,
        source_unchanged=True, manifest_v2_unchanged=True, field_rules=len(fields['fields']),
        job_diff_verified_against_fc9ed8a8=True))
    manifest = json.loads((ROOT/'rh/CONTENTS.json').read_text())['files']
    expected = {name:dict(bytes=Path(path).stat().st_size, sha256=H.sha(path))
                for name,path in manifest.items() if name != 'inputs/anchors.tar'}
    expected['inputs/anchors.tar'] = {k:config['anchors'][k] for k in ('bytes','sha256')}
    expected['run_rh.sh'] = dict(bytes=(ROOT/'rh/run_rh.sh').stat().st_size,
                                 sha256=H.sha(ROOT/'rh/run_rh.sh'))
    pin = json.loads((ROOT/'rh/ARCHIVE.json').read_text())
    path = ROOT/'rh/RH_1_3.tar'
    assert path.stat().st_size == pin['bytes'] < 5_000_000_000
    seen, verified = set(), {}
    with tarfile.open(path, 'r|') as archive:
        for member in archive:
            assert member.name not in seen, member.name
            seen.add(member.name)
            if member.name in expected:
                actual = dict(bytes=member.size, sha256=digest(archive.extractfile(member)))
                assert actual == expected[member.name], member.name
                verified[member.name] = actual
    assert set(verified) == set(expected)
    assert 'runtime/p1cpu/bin/python' in seen and 'runtime/uv/bin/python3.12' in seen
    assert H.sha(path) == pin['sha256']
    H.dump(ROOT/'evidence/REPORT6B_ARCHIVE_VALIDATION.json', dict(passed=True,
        archive=pin, archive_members=len(seen), files=verified, unique_members=True,
        environments_present=True, production_anchor_included=True))
    print(json.dumps(dict(passed=True, batch=package, archive=pin, batch_run=str(batch))))


if __name__ == '__main__':
    main()
