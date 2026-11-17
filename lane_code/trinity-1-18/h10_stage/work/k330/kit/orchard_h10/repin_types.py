"""Replace only job.py and runner.py in the backed-up sl118 package."""
import copy
import json
import runpy

from orchard_h10.common import canonical, opaque, sha, write
from orchard_h10.repin_operator import pin
from orchard_h10.repin_terminator import K, TOKEN, members, render

EXPECTED = 'e01ada41399d2951e7ba88e2ad4e975b39cc5b915795e841d540a3b64634ec2b'
EXPECTED_PLAN = '811c6533d66753a45ea5547ef6ad2b99e6703c6ff23f012c7461d492cc053954'
NAMES = ('orchard_h10/job.py', 'orchard_h10/runner.py')


def main():
    package = K/'orchard_h10/package'
    backup = K/'orchard_h10/package_e01ada41'
    proof = K/'tmp/t15/repin'
    assert sha(package/'0.tgz') == EXPECTED
    assert sha(backup/'0.tgz') == EXPECTED
    assert not (proof/'new').exists(), 'Require a fresh rebuild destination'
    original = {p.name: p.read_bytes() for p in package.iterdir() if p.is_file()}
    assert len(original) == 8
    assert {p.name for p in backup.iterdir()} == set(original)
    assert {p.name for p in (proof/'selftest').iterdir()} == set(original)
    assert all((backup/n).read_bytes() == raw == (proof/'selftest'/n).read_bytes()
               for n, raw in original.items())
    old = members(backup/'0.tgz')
    assert len(old) == 924
    cfg = json.loads(old['9.json'])
    assert cfg['token'] == TOKEN and canonical(cfg) == EXPECTED_PLAN
    assert json.loads(original['0.json'])['plan_sha256'] == EXPECTED_PLAN
    assert old['9.json'] == json.dumps(cfg, sort_keys=True).encode()
    payload = {n: raw for n, raw in old.items() if n != '9.json'}
    assert cfg['payload_pins'] == {n: pin(raw) for n, raw in payload.items()}
    tokens = (K/'orchard_h10/TOKENS.json').read_bytes()
    updated = copy.deepcopy(cfg)
    for name in NAMES:
        payload[name] = (K/name).read_bytes()
        assert payload[name] != old[name]
        updated['payload_pins'][name] = pin(payload[name])
    staged = proof/'new'
    public = render(staged, dict(payload), updated)
    new = members(staged/'0.tgz')
    assert list(new) == list(old) == sorted(old)
    changed = [n for n in old if old[n] != new[n]]
    assert set(changed) == {'9.json', *NAMES}
    restored = copy.deepcopy(json.loads(new['9.json']))
    for name in NAMES:
        assert new[name] == (K/name).read_bytes()
        restored['payload_pins'][name] = cfg['payload_pins'][name]
    assert restored == cfg
    assert json.dumps(restored, sort_keys=True).encode() == old['9.json']
    assert updated['payload_pins'] == {n: pin(raw) for n, raw in new.items() if n != '9.json'}
    assert public['plan_sha256'] == canonical(updated)
    for name, raw in new.items():
        if name.endswith('.py'):
            compile(raw, name, 'exec')
    helpers = runpy.run_path(str(staged/'3.py'), run_name='repin_types_check')
    from orchard_h10.job import verify_config
    loaded = helpers['load_helpers'](staged)
    verify_config(loaded)
    assert loaded['plan_sha256'] == public['plan_sha256']
    for p in staged.iterdir():
        (package/p.name).write_bytes(p.read_bytes())
    assert all((package/p.name).read_bytes() == p.read_bytes() for p in staged.iterdir())
    assert (K/'orchard_h10/TOKENS.json').read_bytes() == tokens
    verify_config(helpers['load_helpers'](package))
    receipt = json.loads((package/'PACKAGE.json').read_text())
    assert all(sha(package/n) == h for n, h in receipt['files'].items())
    for p in package.iterdir():
        if p.name != '0.tgz':
            opaque([p.name, p.read_text()])
    record = dict(
        old=dict(sha256=EXPECTED, bytes=len(original['0.tgz']), plan_sha256=EXPECTED_PLAN),
        new=dict(sha256=sha(package/'0.tgz'), bytes=(package/'0.tgz').stat().st_size,
                 plan_sha256=public['plan_sha256'], package_sha256=sha(package/'PACKAGE.json')),
        members=len(new), unchanged_members=len(old)-len(changed), changed_members=changed,
        payload_pins_verified=len(payload), config_change='job.py and runner.py payload pins only',
        changed_public_files=[n for n, raw in original.items() if (package/n).read_bytes() != raw],
        new_files=receipt['files'], no_change_selftest='all eight files byte-identical',
        source_matches_payload_members=True, helpers_and_config='passed',
        public_opacity='passed', compile='all payload Python passed', receipt_hashes='passed',
        tokens_unchanged=True, template_pins_unchanged=True)
    write(proof/'verification.json', record)
    print(json.dumps(record, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
