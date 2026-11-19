"""Validate a reviewed archive and land it through the single sync owner."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time


class Refusal(Exception):
    pass


def require(ok, message):
    if not ok:
        raise Refusal(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_text(value, field):
    require(bool(value) and len(value) <= 512 and
            not any(ord(c) < 32 or ord(c) == 127 for c in value),
            f'{field} must be nonempty text without control characters (max 512)')
    return value


def review(raw, seal, sha, bind_sha=None):
    text = raw.decode('utf-8', errors='strict')
    require(not re.search(r'NO[- ]GO|REJECT', text, re.I),
            'negative review requires a fresh accepting verdict file')
    lines = [line for line in text.splitlines() if line.strip()]
    accepted = ('GO', 'ACCEPT', 'ACCEPT WITH FINDINGS')
    first = re.fullmatch(r'VERDICT: *(.+?)\s*', lines[0], re.I) if lines else None
    require(first is not None and first[1].upper() in accepted,
            'first non-empty line must be VERDICT: GO, ACCEPT, or ACCEPT WITH FINDINGS; '
            'GO AFTER FIXES needs a separate later GO file')
    verdict = first[1].upper()
    fields = {}
    for line in lines:
        m = re.fullmatch(r'(Seal|SHA256)\s*:\s*(.+)', line, re.I)
        if m:
            key = m[1].lower()
            require(key not in fields or fields[key] == m[2].strip(), f'ambiguous {key} metadata')
            fields[key] = m[2].strip()
        m = re.fullmatch(r'VERDICT: *(.*?)\s*', line, re.I)
        if m:
            require(m[1].upper() in accepted, 'conflicting verdict requires a fresh review file')
    require(fields.get('seal', seal) == seal, 'review seal differs from supplied seal')
    require(fields.get('sha256', sha).lower() == sha, 'review SHA256 differs from supplied SHA256')
    if bind_sha is not None:
        require(bind_sha.lower() == sha, '--bind-sha differs from supplied SHA256')
    methods = [key for key in ('seal', 'sha256') if key in fields]
    if bind_sha is not None:
        methods.append('owner_bind_sha256')
    require(bool(methods), 'review needs matching Seal/SHA256 or owner --bind-sha after reading it')
    return verdict, dict(checked=True, methods=methods, sha256=sha)


def within(path, boundary):
    try:
        path.relative_to(boundary)
        return True
    except ValueError:
        return False


@contextmanager
def owner_lock(path, seconds):
    require(0 <= seconds <= 3600, 'lock timeout must be between 0 and 3600 seconds')
    with path.open('a') as f:
        end = time.monotonic() + seconds
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                require(time.monotonic() < end, f'timed out waiting for sync owner lock {path}; no Git ran')
                time.sleep(min(0.1, max(0, end - time.monotonic())))
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def run(args, *, cwd=None, timeout=300):
    env = None
    if args[0] == 'git':
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        selectors = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                     'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES')
        require(not any(k in os.environ for k in selectors),
                'inherited Git repository/index selector refused; use a clean owner environment')
    try:
        result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.DEVNULL, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise Refusal(f'command timed out; stopped without retry: {args[0]}') from None
    require(result.returncode == 0,
            f'command failed ({result.returncode}): {args[0]} {args[1:]}\n' +
            result.stderr.decode(errors='replace')[-2000:])
    return result.stdout


def unpack(archive, dest):
    """Extract regular files manually; never follow archive links or tar extraction paths."""
    seen = set()
    total = 0
    count = 0
    with tarfile.open(archive, 'r:*') as tf:
        for member in tf:
            count += 1
            require(count <= 10000, 'archive has more than 10000 members')
            name = member.name
            require(not any(ord(c) < 32 or ord(c) == 127 for c in name), 'control character in archive name')
            require('\\' not in name and not name.startswith('/'), 'unsafe archive path')
            parts = name.split('/')
            require('..' not in parts, 'parent traversal in archive path')
            rel = str(PurePosixPath(name))
            if rel == '.' and member.isdir():
                continue
            require(rel not in ('', '.') and rel not in seen, f'duplicate or empty archive member: {rel}')
            require(member.isdir() or member.isfile(), f'archive links/devices refused: {rel}')
            require(rel != 'KIT.json', 'root KIT.json is reserved for landing metadata')
            seen.add(rel)
            target = dest / rel
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            total += member.size
            require(total <= 64 * 1024 * 1024, 'archive expands beyond 64 MiB')
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tf.extractfile(member)
            require(source is not None, f'cannot read archive member {rel}')
            with source, target.open('xb') as out:
                shutil.copyfileobj(source, out, 64 * 1024)
            require(target.stat().st_size == member.size, f'truncated archive member {rel}')
            target.chmod(0o755 if member.mode & 0o111 else 0o644)
    return seen


def inventory(root):
    found = {}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), f'symlink refused: {p}')
        if p.is_file():
            found[p.relative_to(root).as_posix()] = {
                'sha256': digest(p), 'bytes': p.stat().st_size,
                'executable': bool(p.stat().st_mode & 0o111)}
        else:
            require(p.is_dir(), f'nonregular file refused: {p}')
    return found


def secret_scan(script, source, dest, flag):
    run([sys.executable, '-I', '-s', '-B', str(script), str(source), str(dest), str(flag)])
    require(flag.is_file() and flag.stat().st_size == 0, f'secret scan flagged files; see {flag}')
    # The supplied scanner skips unreadable files; verify that every byte survived.
    before, after = inventory(source), inventory(dest)
    require({k: (v['sha256'], v['bytes']) for k, v in before.items()} ==
            {k: (v['sha256'], v['bytes']) for k, v in after.items()}, 'scanner omitted or changed a file')


def prepare(args, root, filter_script, scan_script):
    raw = root / 'raw'
    raw.mkdir()
    # Copy once, then hash and extract that snapshot to prevent archive replacement races.
    archive = root / 'kit.tar'
    require(args.archive.is_file() and args.archive.stat().st_size <= 64 * 1024 * 1024,
            'archive must be a regular file no larger than 64 MiB')
    total = 0
    with args.archive.open('rb') as source, archive.open('xb') as snapshot:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            require(total <= 64 * 1024 * 1024, 'archive grew beyond 64 MiB while snapshotting')
            snapshot.write(chunk)
    require(digest(archive) == args.sha256, 'archive SHA256 mismatch')
    verdict_path = args.verdict.resolve(strict=True)
    require(verdict_path.is_file() and verdict_path.stat().st_size <= 512 * 1024,
            'review must be a regular file no larger than 512 KiB')
    verdict_bytes = verdict_path.read_bytes()
    verdict, binding = review(verdict_bytes, args.seal, args.sha256, args.bind_sha)
    members = unpack(archive, raw)
    scanned = root / 'scanned'
    scanned.mkdir()
    secret_scan(scan_script, raw, scanned, root / 'raw_flags.txt')
    meta = root / 'filter_meta'
    selected = run([sys.executable, '-I', '-s', '-B', str(filter_script), 'kit', str(meta)], cwd=raw)
    paths = set(os.fsdecode(p) for p in selected.split(b'\0') if p)
    manifest = meta / 'DEDUP_kit.tsv.gz'
    paths.discard(os.path.relpath(manifest, raw))
    with gzip.open(manifest, 'rt', encoding='utf-8', errors='surrogateescape') as f:
        for line in f:
            duplicate, kept = line.rstrip('\n').split('\t')
            require(kept in paths, 'invalid dedup manifest')
            paths.add(duplicate)
    represented = set(paths)
    for rel in paths:
        represented.update(str(p) for p in PurePosixPath(rel).parents if str(p) != '.')
    skipped = sorted(members - represented)
    for rel in skipped:
        print('SKIPPED ' + json.dumps(rel))
    require(not skipped or args.allow_skips, 'filter skipped files; inspect SKIPPED and pass --allow-skips explicitly')
    require(bool(paths), 'filter admitted no files')
    payload = root / 'payload'
    payload.mkdir()
    for rel in sorted(paths):
        require(not Path(rel).is_absolute() and '..' not in Path(rel).parts, 'filter emitted unsafe path')
        source = raw / rel
        require(source.is_file() and not source.is_symlink(), 'filter emitted a missing file or symlink')
        dest = payload / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        dest.chmod(0o755 if source.stat().st_mode & 0o111 else 0o644)
    files = inventory(payload)
    metadata = dict(seal=args.seal, sha256=args.sha256, builder=args.builder, reviewer=args.reviewer,
                    binding=binding, skipped=skipped,
                    verdict_path=str(verdict_path), verdict_sha256=hashlib.sha256(verdict_bytes).hexdigest(),
                    verdict=verdict, date=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    file_count=len(files), files=files)
    (payload / 'KIT.json').write_text(json.dumps(metadata, sort_keys=True, indent=2) + '\n')
    final_scan = root / 'final_scan'
    final_scan.mkdir()
    secret_scan(scan_script, payload, final_scan, root / 'metadata_flags.txt')
    for rel, info in files.items():
        print(f"FILE {json.dumps(rel)} bytes={info['bytes']} sha256={info['sha256']}")
    print(f"COUNT files={len(files)} bytes={sum(v['bytes'] for v in files.values())} metadata_files=1")
    return payload, metadata


def check_target(args, repo, metadata):
    target = repo / 'kits' / args.name
    require(not (repo / 'kits').is_symlink() and not target.is_symlink(), 'kits destination is a symlink')
    if target.exists():
        require(target.is_dir() and (target / 'KIT.json').is_file(), 'existing name has no valid KIT.json')
        actual = inventory(target)
        old = json.loads((target / 'KIT.json').read_text())
        require({k: v for k, v in old.items() if k != 'date'} ==
                {k: v for k, v in metadata.items() if k != 'date'}, 'kit name already exists with different content or provenance')
        actual.pop('KIT.json', None)
        require(actual == metadata['files'], 'existing kit bytes or modes differ')
        return True
    return False


def land(args, state, repo, payload, metadata):
    def git(*argv):
        return run(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                    '-C', str(repo), *argv]).decode().strip()
    require(git('symbolic-ref', '--quiet', '--short', 'HEAD') == 'lane-code', 'owner clone must already be on lane-code')
    git('diff', '--quiet')
    git('diff', '--cached', '--quiet')
    target = repo / 'kits' / args.name
    if check_target(args, repo, metadata):
        tracked = {p for p in git('ls-files', '-z', '--', f'kits/{args.name}').split('\0') if p}
        expected = {f'kits/{args.name}/{p}' for p in metadata['files']} | {f'kits/{args.name}/KIT.json'}
        require(tracked == expected, 'existing kit is not fully tracked; inspect interrupted landing')
        print('IDENTICAL already landed; verifying and publishing current lane-code head')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(payload, target)
        git('add', '-f', '--', f'kits/{args.name}')
        message = (f"Land kit {args.name}\n\nSeal: {metadata['seal']}\nSHA256: {metadata['sha256']}\n"
                   f"Builder: {metadata['builder']}\nReviewer: {metadata['reviewer']}\nDate: {metadata['date']}")
        git('commit', '-q', '-m', message)
    head = git('rev-parse', 'HEAD')
    require(bool(re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', head)), 'invalid HEAD returned by Git')
    for remote, label in (('origin', 'GitHub'), ('home', 'home')):
        git('push', '-q', remote, 'HEAD:refs/heads/lane-code')
        lines = git('ls-remote', remote, 'refs/heads/lane-code').splitlines()
        require(lines == [f'{head}\trefs/heads/lane-code'], f'{remote} lane-code verification failed')
        print(f"{metadata['date']} verified {label} lane-code = {head}")
    landed_at = datetime.now(timezone.utc)
    landed = (f"{landed_at.strftime('%Y-%m-%dT%H:%M:%SZ')} LANDED kits/{args.name} "
              f"commit={head} sha256={metadata['sha256']}")
    with (state / 'KITS_LANDED.txt').open('a') as f:
        f.write(landed + '\n')
    events = args.events
    events.mkdir(parents=True, exist_ok=True)
    event = events / (landed_at.strftime('%Y%m%dT%H%M%S%fZ') +
                      f'_RESULT_kit_{args.name}_landed.md')
    if event.exists():
        require(not event.is_symlink() and event.read_text() == landed + '\n', 'kit event collision')
    else:
        with event.open('x') as f:
            f.write(landed + '\n')
    print(landed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('seal')
    parser.add_argument('sha256')
    parser.add_argument('verdict', type=Path)
    parser.add_argument('name')
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--builder', required=True)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--bind-sha', help='owner confirms this SHA256 after reading the verdict')
    parser.add_argument('--allow-skips', action='store_true')
    args = parser.parse_args(argv)
    require(os.environ.get('LCS_ENABLE_KIT_LANDING') == '1', 'disabled; owner must set LCS_ENABLE_KIT_LANDING=1')
    require(bool(re.fullmatch('[a-z0-9_]+', args.name)), 'invalid kit name; use [a-z0-9_]+')
    safe_text(args.seal, 'seal')
    args.builder = safe_text(args.builder.strip(), 'builder')
    args.reviewer = safe_text(args.reviewer.strip(), 'reviewer')
    require(args.builder.casefold() != args.reviewer.casefold(), 'builder and reviewer must differ')
    require(bool(re.fullmatch('[0-9a-fA-F]{64}', args.sha256)), 'SHA256 must be 64 hex digits')
    args.sha256 = args.sha256.lower()
    state = Path(os.environ.get('LCS_S', '/scratch/jjyeung/distill_sync')).resolve()
    repo = Path(os.environ.get('LCS_R', str(state / 'repo'))).resolve()
    test_root = os.environ.get('LCS_TEST_ROOT')
    if test_root:
        boundary = Path(test_root).resolve(strict=True)
        require(boundary != Path('/') and str(boundary).startswith('/scratch/'), 'test root must be on /scratch')
        events = Path(os.environ.get('LCS_EV', str(boundary / 'events'))).resolve()
        require(all(within(p, boundary) for p in (state, repo, events)), 'test writes must stay within test root')
    else:
        require(not any(k in os.environ for k in ('LCS_FILTER', 'LCS_SCAN', 'LCS_B', 'LCS_EV')),
                'production tool/event overrides require LCS_TEST_ROOT')
        require(socket.gethostname().split('.')[0] == 'trinity-3-30', 'owner runs only on trinity-3-30')
        require(state == Path('/scratch/jjyeung/distill_sync') and repo == state / 'repo',
                'production must use the hourly owner state, clone, and lock; overrides require LCS_TEST_ROOT')
    tools = Path(os.environ.get('LCS_B', '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30')) / 'tools'
    args.events = events if test_root else tools.parent / 'events' / 'code_sync'
    filter_script = Path(os.environ.get('LCS_FILTER', str(tools / 'lane_code_filter.py'))).resolve(strict=True)
    scan_script = Path(os.environ.get('LCS_SCAN', str(tools / 'lane_code_scan.py'))).resolve(strict=True)
    require(state.is_dir(), f'owner state does not exist: {state}')
    require(not (state / '.sync.lock').is_symlink(), 'owner lock must not be a symlink')
    with owner_lock(state / '.sync.lock', float(os.environ.get('LCS_LOCK_TIMEOUT', '600'))):
        root = Path(tempfile.mkdtemp(prefix='land_kit_', dir=state))
        print(f'AUDIT {root}')
        payload, metadata = prepare(args, root, filter_script, scan_script)
        check_target(args, repo, metadata)
        if args.dry:
            print('DRY validated; stopped before Git or clone writes')
            return 0
        require(repo.is_dir(), f'owner clone does not exist: {repo}')
        land(args, state, repo, payload, metadata)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Refusal, OSError, ValueError, tarfile.TarError, UnicodeError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
