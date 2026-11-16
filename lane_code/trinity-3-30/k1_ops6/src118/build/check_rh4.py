"""Small contract checks for callback coverage and two-run result collection."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import uuid

import job_support as H
import rh_coverage as C
import rh_prepare

ROOT = Path(__file__).resolve().parent


def main():
    run = ROOT/'evidence'/('rh4_checks_'+uuid.uuid4().hex[:10])
    run.mkdir()
    source = run/'observer.py'
    source.write_text('seen = []\ndef observe(frame, event, value):\n'
                      '    if event == "return" and frame.f_code.co_name == "target":\n'
                      '        seen.append(value)\n'
                      '    elif event == "unreachable":\n'
                      '        raise AssertionError("unreachable")\n'
                      'def target():\n    return 23\n')
    original = {}
    exec(compile(source.read_text(), str(source), 'exec'), original)
    hits = {}
    tree, probes = C.observer_tree(str(source), hits)
    instrumented = dict(probes)
    exec(compile(tree, str(source), 'exec'), instrumented)
    previous = sys.getprofile()
    try:
        for env in (original, instrumented):
            sys.setprofile(env['observe'])
            assert env['target']() == 23
            sys.setprofile(None)
    finally:
        sys.setprofile(previous)
    assert original['seen'] == instrumented['seen'] == [23]
    assert {3, 4, 5} <= hits[str(source)] and 6 not in hits[str(source)]
    destination = run/'collection'
    (destination/'out').mkdir(parents=True)
    def coverage(lines, digest='a'*64):
        return {'/different/root/wrapper.py':dict(sha256=digest, executed_lines=lines,
                   unexecuted_lines=sorted({1,2,3}-set(lines)), executed=len(lines), total=3)}
    for name, lines in [('v2_current',[1]), ('batch_current',[2]), ('v2_stale',[3])]:
        H.dump(destination/'evidence'/name/'COVERAGE.json', coverage(lines))
    H.dump(destination/'evidence/batch_current/success/job_tmp/not_evidence.json', {})
    H.dump(destination/'out/RESULT.json', dict(outer_namespace_started=True,
        evidence_runs=['v2_current','batch_current'], namespace_executed=True))
    rh_prepare.collect(destination, 0)
    combined = json.loads((destination/'out/COVERAGE_UNION.json').read_text())
    assert len(combined) == 1
    row = next(iter(combined.values()))
    assert row['executed_lines'] == [1,2] and row['unexecuted_lines'] == [3]
    assert len(C.union([('one',coverage([1])), ('two',coverage([2], 'b'*64))])) == 2
    with tarfile.open(destination/'out/RH_RESULT.tar') as archive:
        names = archive.getnames()
    assert 'out/COVERAGE_UNION.json' in names
    assert 'evidence/batch_current/COVERAGE.json' in names
    assert not any('stale' in name or 'job_tmp' in name for name in names)
    script = (ROOT/'packet/a7e31d84.sh').read_text()
    encoded = ast.parse(script.splitlines()[7]).body[0].value.args[0].value
    payload = base64.b64decode(encoded)
    protected = {}
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        for member in archive:
            if member.name.endswith('.py'):
                raw = archive.extractfile(member).read()
                assert raw == (ROOT/member.name).read_bytes(), member.name
                protected[member.name] = hashlib.sha256(raw).hexdigest()
    for name, expected in [('packet/d6e92a81.tar','e9ffe4aef8b1c6a055b5f7083d1d925ad82760d76e08532bf3a4a3dd200de1e0'),
                           ('manifest_v2/a40fbc19.json','e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146'),
                           ('packet/a7e31d84.sh','446c9c70fe241d40d564faf1a26778440370f27262266468a64526e69b4d489e')]:
        assert H.sha(ROOT/name) == expected
        protected[name] = expected
    result = dict(passed=True, observer_preserves_result=True, unreachable_callback_branch_not_credited=True,
                  union_excludes_stale_runs=True, union_separates_source_hashes=True,
                  embedded_job_modules_unchanged=protected)
    H.dump(run/'RESULT.json', result)
    H.dump(ROOT/'evidence/REPORT4_VALIDATION.json', dict(run=str(run), **result))
    print(json.dumps(dict(run=str(run), passed=True)))


if __name__ == '__main__':
    main()
