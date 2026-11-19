"""Package the blocked S1k2 delivery without opening evaluation data or old archives."""
from common import *
import resource
import tarfile


def main():
    resource.setrlimit(resource.RLIMIT_AS, (39 << 30, 39 << 30))
    files = [W/name for name in ['OPERATOR.md', 'KIT_SPEC_room_pricing.md', 'STATUS.md', 'BLOCKER.md']]
    for directory in ['scripts', 'tests', 'vendor']:
        files.extend(p for p in (W/directory).iterdir() if p.is_file() and p.suffix in ('.py', '.sh'))
    files.extend(W/'configs'/name for name in ['KERNEL_PROVENANCE.json', 'KERNEL_FROZEN.json',
                                             'KERNEL_PROVENANCE_S1K2.json'])
    files.extend(W/'evidence'/name for name in ['k1_room_tables.py', 'k1_rule_variants.py'])
    files.extend(W/'out'/name for name in [
        'S1K_REGISTRATION.json', 'S1K2_RULE.md', 'S1K2_TRAIN_METADATA.json',
        'S1K2_TRAIN_INVENTORY.json', 'S1K2_GT_AUDIT.json', 'S1K2_AUDIT.log',
        'S1K2_TESTS.json', 'S1K2_DRYRUN.json', 'S1K2_VALIDATE.log',
        'S1K2_RESULTS.json', 'S1K2_REPORT.md', 'ROOMKIT_REPORT.md', 'GPU_NEED.json'])
    files = sorted(set(files))
    assert all(p.is_file() and p.is_relative_to(W) for p in files)
    hashes = {str(p): sha(p) for p in files}
    ledger = W/'out/DELIVERY_SHA256.txt'
    ledger.write_text(''.join(f'{hashes[str(p)]}  {p.relative_to(W)}\n' for p in files))
    archive = W/'out/sb_rkfam.tar'
    with tarfile.open(archive, 'w') as tar:
        for p in files+[ledger]:
            tar.add(p, arcname=str(p.relative_to(W)), recursive=False)
    with tarfile.open(archive, 'r') as tar:
        assert set(tar.getnames()) == {str(p.relative_to(W)) for p in files+[ledger]}
        for p in files+[ledger]:
            h = hashlib.sha256()
            f = tar.extractfile(str(p.relative_to(W)))
            for chunk in iter(lambda: f.read(8 << 20), b''):
                h.update(chunk)
            assert h.hexdigest() == sha(p), str(p)
    archive_hash = sha(archive)
    (W/'out/sb_rkfam.tar.sha256').write_text(archive_hash+'  out/sb_rkfam.tar\n')
    write(W/'out/S1K2_PACKAGE.json', dict(status='VERIFIED_BLOCKER_PACKAGE', archive=str(archive),
          sha256=archive_hash, bytes=archive.stat().st_size, verified_members=len(files)+1,
          selection_status='BLOCKED', launch_ready=False,
          excluded='Inherited archives, evaluation manifests/items/predictions/results, caches and temporary fixtures',
          command='bash scripts/cpu.sh scripts/s1k2_package.py'),
          {**hashes, str(ledger): sha(ledger), str(archive): archive_hash})
    print(archive_hash, archive, archive.stat().st_size, 'bytes;', len(files)+1, 'member hashes verified')


if __name__ == '__main__':
    main()
