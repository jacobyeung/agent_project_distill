"""Synchronize the archived operator source with the fixed submit helper.

Run from K with: bash cpu.sh -m orchard_h10.repin_operator_member
"""
import copy
import json
import runpy

from orchard_h10.common import canonical, opaque, sha, write
from orchard_h10.repin_operator import pin
from orchard_h10.repin_terminator import K, TOKEN, members, render

EXPECTED = '5f9898505dd3e0857d8b97bf24336a783a2dddc0c240c3fa5dbfc0dd9ac84e3c'
EXPECTED_PLAN = '1f506aafcdd09ccbe7a9f0b80d871bea9c3a5d81df3973782e691c461a410823'
MEMBER = 'orchard_h10/operator.py'


def main():
    package = K/'orchard_h10/package'
    backup = K/'orchard_h10/package_5f989850'
    proof = K/'tmp/t12/repin'
    assert not backup.exists(), 'Refuse to overwrite the current-package backup'
    assert not proof.exists(), 'Require a fresh proof directory'
    assert sha(package/'0.tgz') == EXPECTED
    original = {p.name: p.read_bytes() for p in package.iterdir() if p.is_file()}
    assert len(original) == 8
    old = members(package/'0.tgz')
    assert len(old) == 920
    cfg = json.loads(old['9.json'])
    assert cfg['token'] == TOKEN
    assert canonical(cfg) == EXPECTED_PLAN
    assert json.loads(original['0.json'])['plan_sha256'] == EXPECTED_PLAN
    assert old['9.json'] == json.dumps(cfg, sort_keys=True).encode()
    payload = {n: raw for n, raw in old.items() if n != '9.json'}
    assert cfg['payload_pins'] == {n: pin(raw) for n, raw in payload.items()}
    source = (K/MEMBER).read_bytes()
    assert source == payload['8.py']
    before = b"'PATH':'/usr/bin:/bin'"
    after = b"'PATH':'/usr/local/bin:/usr/bin:/bin'"
    assert payload[MEMBER].count(before) == 1
    assert source == payload[MEMBER].replace(before, after, 1)
    tokens = (K/'orchard_h10/TOKENS.json').read_bytes()

    backup.mkdir()
    for name, raw in original.items():
        (backup/name).write_bytes(raw)
        assert (backup/name).read_bytes() == raw
    selftest = proof/'selftest'
    render(selftest, dict(payload), copy.deepcopy(cfg))
    assert {p.name for p in selftest.iterdir()} == set(original)
    assert all((selftest/n).read_bytes() == raw for n, raw in original.items())
    print('No-change self-test: all eight current files reproduce byte-for-byte', flush=True)

    payload[MEMBER] = source
    updated = copy.deepcopy(cfg)
    updated['payload_pins'][MEMBER] = pin(source)
    staged = proof/'new'
    public = render(staged, dict(payload), updated)
    new = members(staged/'0.tgz')
    assert new.keys() == old.keys()
    changed = [n for n in old if old[n] != new[n]]
    assert set(changed) == {MEMBER, '9.json'}
    assert len(old)-len(changed) == 918
    assert new[MEMBER] == new['8.py'] == source
    restored = copy.deepcopy(json.loads(new['9.json']))
    restored['payload_pins'][MEMBER] = cfg['payload_pins'][MEMBER]
    assert restored == cfg
    assert json.dumps(restored, sort_keys=True).encode() == old['9.json']
    assert updated['payload_pins'] == {n: pin(raw) for n, raw in new.items() if n != '9.json'}
    assert public['plan_sha256'] == canonical(updated)
    compile(new[MEMBER], MEMBER, 'exec')
    helpers = runpy.run_path(str(staged/'3.py'), run_name='repin_operator_member_check')
    from orchard_h10.job import verify_config
    loaded = helpers['load_helpers'](staged)
    verify_config(loaded)
    assert loaded['plan_sha256'] == public['plan_sha256']

    for p in staged.iterdir():
        (package/p.name).write_bytes(p.read_bytes())
    assert all((package/p.name).read_bytes() == p.read_bytes() for p in staged.iterdir())
    assert (K/MEMBER).read_bytes() == source
    assert (K/'orchard_h10/TOKENS.json').read_bytes() == tokens
    loaded = helpers['load_helpers'](package)
    verify_config(loaded)
    receipt = json.loads((package/'PACKAGE.json').read_text())
    assert all(sha(package/n) == h for n, h in receipt['files'].items())
    for p in package.iterdir():
        if p.name != '0.tgz':
            opaque([p.name, p.read_text()])
    record = dict(
        old=dict(sha256=EXPECTED, bytes=len(original['0.tgz']), plan_sha256=EXPECTED_PLAN),
        new=dict(sha256=sha(package/'0.tgz'), bytes=(package/'0.tgz').stat().st_size,
                 plan_sha256=public['plan_sha256'], package_sha256=sha(package/'PACKAGE.json')),
        members=len(old), unchanged_members=918, changed_members=changed,
        payload_pins_verified=len(payload), config_change=f'payload_pins[{MEMBER!r}] only',
        changed_public_files=[n for n, raw in original.items() if (package/n).read_bytes() != raw],
        new_files=receipt['files'], no_change_selftest='all eight files byte-identical',
        source_matches_both_payload_members='passed', helpers_and_config='passed',
        public_opacity='passed', compile='passed', receipt_hashes='passed',
        tokens_unchanged=True, terminator_unchanged=True, template_pins_unchanged=True)
    write(proof/'verification.json', record)
    print(json.dumps(record, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
