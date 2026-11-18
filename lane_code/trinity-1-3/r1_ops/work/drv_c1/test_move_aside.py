"""Small local fixtures and fake Slurm; no remote command or deletion."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

W = Path(__file__).resolve().parent
T = Path(tempfile.mkdtemp(prefix='move_p5_', dir=W))
old_archive = T/'old.tar'
old_archive.write_bytes(Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/out/p_69d2930d.tar').read_bytes())
mock = T/'bin'
mock.mkdir()
for name, body in {
    'squeue': '[[ "$TZ" == UTC ]] || exit 30\n[[ "$FAIL_QUEUE" == 0 ]] || exit 9\nprintf "%s\\n" "$QUEUE"',
    'sacct': '[[ "$TZ" == UTC ]] || exit 30\n[[ "$FAIL_ACCT" == 0 ]] || exit 9\nprintf "%s\\n" "$ACCOUNT"',
}.items():
    p = mock/name
    p.write_text('#!/bin/bash\n'+body+'\n')
    p.chmod(0o700)

cases = ['queued', 'queue_error', 'account_error', 'running', 'no_end', 'no_record',
         'wrong_jobname', 'future_end', 'bundle_target', 'kit_target', 'optional_target',
         'wrong_archive', 'wrong_sums', 'wrong_jobid', 'bad_receipt', 'worker_running',
         'bad_staging', 'linked_staging', 'linked_bundle', 'valid']
for case in cases:
    root = T/case
    root.mkdir(mode=0o700)
    b, k = root/'i_69d2930d', root/'x_69d2930d'
    b.mkdir(mode=0o700)
    k.mkdir(mode=0o700)
    for p in (W/'fixture_p4').rglob('*'):
        dest = b/p.relative_to(W/'fixture_p4')
        if p.is_dir():
            dest.mkdir(mode=0o700, exist_ok=True)
        else:
            os.link(p, dest)
    # Archive hardlink avoids a 14 MB copy per negative test.
    archive = old_archive
    if case == 'wrong_archive':
        (b/'p.tar').write_bytes(b'wrong')
    else:
        os.link(archive, b/'p.tar')
    # Never mutate a hardlinked immutable input. Rewrite the path in this one test.
    if case == 'wrong_sums':
        (b/'wrong_sums').write_text('wrong')
    (b/'job.id').write_text('99' if case == 'wrong_jobid' else '170956')
    (b/'p0.lock').touch()
    for tag in ('e0', 'd0'):
        (b/tag).mkdir()
        (b/tag/'rc').write_text('9' if case == 'worker_running' else '0')
    (k/'o').mkdir()
    (k/'o/170956.proof.json').write_text(json.dumps(dict(job='170956', status='PASS' if case == 'bad_receipt' else 'FAIL', config_identity='fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f')))
    for name in ('r/673bc60f', 'tmp/a_673bc60f', 'tmp/p_673bc60f_170956'):
        (root/name).mkdir(mode=0o700, parents=True)
    target = {'bundle_target': b, 'kit_target': k, 'optional_target': root/'r/673bc60f'}.get(case)
    if target:
        target.with_name(target.name+'.f170956').mkdir()
    stage = root/'n.json'
    if case == 'linked_staging':
        stage.symlink_to(W/'fixture_p5/n.json')
    else:
        stage.write_bytes(b'wrong' if case == 'bad_staging' else (W/'fixture_p5/n.json').read_bytes())
    body = (W/'m0.sh').read_text().replace('/project/community/jjyeung/okh7', str(root))
    body = body.replace('/tmp/jjyeung/', str(root/'tmp')+'/')
    start = body.index('STAGING_PINS = ')
    end = body.index('\n\nif __name__', start)
    body = body[:start]+'STAGING_PINS = '+repr({str(stage): '02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'})+body[end:]
    body = body.replace('python3 -I -B', shlex.quote(sys.executable)+' -I -B')
    if case == 'wrong_sums':
        body = body.replace("B/'sums.txt'", "B/'wrong_sums'")
    if case == 'linked_bundle':
        (root/'linked').symlink_to(b, target_is_directory=True)
        body = body.replace("B = O/'i_69d2930d'", "B = O/'linked'")
    script = root/'m0.sh'
    script.write_text(body)
    account = '170956|a15_cot_ap673bc60f|FAILED|2026-11-17T00:00:00'
    if case == 'running': account = account.replace('FAILED', 'RUNNING')
    if case == 'no_end': account = account.replace('2026-11-17T00:00:00', 'Unknown')
    if case == 'future_end': account = account.replace('2026-', '2099-')
    if case == 'no_record': account = ''
    if case == 'wrong_jobname': account = account.replace('a15_cot_ap673bc60f', 'other')
    env = dict(os.environ, PATH=str(mock)+':/usr/bin:/bin', ACCOUNT=account,
               QUEUE='33|a15_cot_ap673bc60f|advanced|PENDING' if case == 'queued' else '',
               FAIL_QUEUE='1' if case == 'queue_error' else '0',
               FAIL_ACCT='1' if case == 'account_error' else '0')
    before = {p: p.stat().st_ino for p in (b, k)}
    result = subprocess.run(['/bin/bash', str(script)], capture_output=True, text=True, env=env)
    if case == 'valid':
        assert result.returncode == 0, result.stdout+result.stderr
        assert 'PASS moved aside' in result.stdout and result.stdout.count('MOVED ') == 5
        for p, inode in before.items():
            assert not p.exists() and p.with_name(p.name+'.f170956').stat().st_ino == inode
        assert (root/'x_69d2930d.f170956/o/170956.proof.json').exists()
    else:
        assert result.returncode != 0, case
        assert 'REFUSED:' in result.stderr, (case, result.stderr)
        assert all(p.stat().st_ino == inode for p, inode in before.items()), case
    print('PASS m0', case)
print('PASS 19 refusal cases preserve both sources; successful five-path rename preserves inodes and failed receipt')
