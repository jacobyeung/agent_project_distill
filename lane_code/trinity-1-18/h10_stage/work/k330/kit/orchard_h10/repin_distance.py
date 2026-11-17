"""Add the four pinned sl118 sources to the current authenticated package."""
import copy
import json
import runpy

from orchard_h10.common import canonical, opaque, sha, write
from orchard_h10.repin_operator import pin
from orchard_h10.repin_terminator import K, TOKEN, members, render

EXPECTED = 'e82ac3295fe0ae83cb62f08a62f63017dc55fbfdf828211db10575bb49feea96'
EXPECTED_PLAN = '1de19b86d81f2bf9a5b254270e61496e45d454893fe893cbbd325739f74764c8'
NAMES = ('name_emb.py', 'selector_inputs.py', 'sl_tables.py', 'sl_tables_v1.py')
PREFIX = 'b/heads/selector/sl118/'


def main():
    package = K/'orchard_h10/package'
    backup = K/'orchard_h10/package_e82ac329'
    proof = K/'tmp/t14/repin'
    assert not backup.exists(), 'Require a fresh backup directory'
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
    expected_pins = {}
    for line in (K.parent.parent/'b04_pins.txt').read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] in {PREFIX+n for n in NAMES}:
            assert parts[1] not in expected_pins
            expected_pins[parts[1]] = parts[0]
    added = {}
    for name in NAMES:
        source = K.parent/'b04_sl118_from_330/heads/selector/sl118'/name
        assert source.is_file() and not source.is_symlink()
        raw = source.read_bytes()
        member = PREFIX+name
        assert member not in old
        assert pin(raw)['sha256'] == expected_pins[member]
        added[member] = raw
    assert added[PREFIX+'selector_inputs.py'] == old['b/heads/selector/selector_inputs.py']
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

    payload.update(added)
    updated = copy.deepcopy(cfg)
    updated['payload_pins'].update({n: pin(raw) for n, raw in added.items()})
    staged = proof/'new'
    public = render(staged, dict(payload), updated)
    new = members(staged/'0.tgz')
    assert list(new) == sorted(new)
    assert set(new) - set(old) == set(added)
    assert set(old) <= set(new) and len(new) == 924
    changed = [n for n in old if old[n] != new[n]]
    assert changed == ['9.json']
    assert all(new[n] == raw for n, raw in added.items())
    restored = copy.deepcopy(json.loads(new['9.json']))
    restored['payload_pins'] = {n: v for n, v in restored['payload_pins'].items() if n not in added}
    assert restored == cfg
    assert json.dumps(restored, sort_keys=True).encode() == old['9.json']
    assert updated['payload_pins'] == {n: pin(raw) for n, raw in new.items() if n != '9.json'}
    assert public['plan_sha256'] == canonical(updated)
    for name, raw in new.items():
        if name.endswith('.py'):
            compile(raw, name, 'exec')
    compile((K/'orchard_h10/build.py').read_bytes(), 'build.py', 'exec')
    helpers = runpy.run_path(str(staged/'3.py'), run_name='repin_distance_check')
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
        old_members=920, new_members=924, unchanged_old_members=919,
        changed_old_members=changed, added_members={n: pin(raw) for n, raw in added.items()},
        payload_pins_verified=len(payload), config_change='four added payload_pins only',
        changed_public_files=[n for n, raw in original.items() if (package/n).read_bytes() != raw],
        new_files=receipt['files'], no_change_selftest='all eight files byte-identical',
        b04_pins_verified=True, selector_inputs_duplicate_identical=True,
        helpers_and_config='passed', public_opacity='passed', compile='all payload Python passed',
        receipt_hashes='passed', tar_order='sorted, as orchard_launcher.tar_bytes',
        tokens_unchanged=True, template_pins_unchanged=True)
    write(proof/'verification.json', record)
    print(json.dumps(record, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
