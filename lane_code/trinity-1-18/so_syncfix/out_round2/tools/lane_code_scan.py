# lane_code_scan.py <stage> <dest> <flag list>: secret-scan every staged file; copy clean, changed files
# to <dest> (same relative path); flagged files are never copied and are listed as "<path>\t<pattern>".
import os, re, sys, shutil

def checked_archive(path):
    """Read an uncompressed incoming tar completely before publishing its slot."""
    import stat
    import tarfile
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = os.open(path, flags)
    raw = os.fdopen(fd, 'rb')
    try:
        info = os.fstat(raw.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('archive is not a regular file')
        # Iteration reads all headers; require every payload to fit the received file.
        with tarfile.open(fileobj=raw, mode='r:') as archive:
            for member in archive:
                parts = member.name.split('/')
                if member.name.startswith('/') or '..' in parts or not member.name:
                    raise ValueError('unsafe archive path: %r' % member.name)
                if not (member.isfile() or member.isdir()):
                    raise ValueError('nonregular archive entry: %r' % member.name)
                if member.offset_data + member.size > info.st_size:
                    raise ValueError('truncated archive entry: %r' % member.name)
                if member.isfile():
                    data = archive.extractfile(member)
                    while data.read(65536):
                        pass
                    data.close()
    finally:
        raw.close()


def atomic_clean_write(path, data, pending):
    """Publish the bytes that passed the secret scan, outside the Git add paths."""
    import stat
    os.makedirs(os.path.dirname(path), exist_ok=True)
    os.makedirs(os.path.dirname(pending), exist_ok=True)
    try:
        mode = stat.S_IMODE(os.stat(path, follow_symlinks=False).st_mode)
    except FileNotFoundError:
        mask = os.umask(0)
        os.umask(mask)
        mode = 0o666 & ~mask
    fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, 'wb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise ValueError('copy temporary path is not regular')
        os.fchmod(f.fileno(), mode)
        f.write(data)
    os.replace(pending, path)


def robust_copy_scan(stage, dest, flagout):
    import stat
    import tarfile
    flags = []
    copied = same = scanned = 0
    pending = os.environ.get('LCS_COPY_TMP', os.path.join(os.path.dirname(dest), '.lcs-copy.pending'))

    # The fixed scratch name is outside every path passed to Git add.
    sys.stderr.write('COPY_PENDING %s\n' % pending)
    sys.stderr.flush()

    def entries():
        if os.path.isfile(stage):
            # Acceptance already validates the entire archive; repeat before any copy.
            checked_archive(stage)
            with tarfile.open(stage, 'r:') as archive:
                for member in archive:
                    if member.isfile():
                        with archive.extractfile(member) as source:
                            yield member.name, source.read()
        else:
            # Queue scans also use this function. Reject special files before copying.
            paths = []
            for d, dirs, files in os.walk(stage, followlinks=False):
                dirs.sort()
                for name in dirs + sorted(files):
                    path = os.path.join(d, name)
                    mode = os.lstat(path).st_mode
                    if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                        raise ValueError('nonregular staged entry: %r' % path)
                    if stat.S_ISREG(mode):
                        paths.append(path)
            for path in paths:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as source:
                    if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                        raise ValueError('changed staged entry: %r' % path)
                    yield os.path.relpath(path, stage), source.read()

    for rel, data in entries():
        scanned += 1
        hit = [n for n, p in PATS if p.search(data)] + (['env_secret_value'] if any(v in data for v in ENV_VALUES) else [])
        if hit:
            flags.append('%s\t%s' % (rel, ','.join(hit)))
            continue
        dp = os.path.join(dest, rel)
        # Refuse links in the destination path. The clone is private and sync-locked.
        parent = os.path.abspath(dp)
        while parent != os.path.dirname(parent):
            if os.path.islink(parent):
                raise ValueError('symlink in copy destination: %r' % parent)
            parent = os.path.dirname(parent)
        try:
            with open(dp, 'rb') as old:
                if old.read() == data:
                    same += 1
                    continue
        except OSError:
            pass
        atomic_clean_write(dp, data, pending)
        copied += 1
    os.makedirs(os.path.dirname(flagout), exist_ok=True)
    with open(flagout, 'w') as f:
        f.write(''.join(x + '\n' for x in flags))
    print('SCAN scanned=%d copied=%d unchanged=%d flagged=%d list=%s' % (scanned, copied, same, len(flags), flagout))
    for x in flags[:50]:
        print('FLAG ' + x)


if os.environ.get('LCS_ROBUST_SYNC', '0') == '1' and sys.argv[1:2] == ['--accept-archive']:
    incoming, accepted = sys.argv[2:4]
    checked_archive(incoming)
    # Same-directory rename accepts the complete source in one operation.
    print('ACCEPTING %s' % accepted, flush=True)
    os.replace(incoming, accepted)
    sys.exit(0)

stage, dest, flagout = sys.argv[1:4]
PATS = [
    ('private_key_block', re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('aws_akia', re.compile(rb'AKIA[0-9A-Z]{16}')),
    ('hf_token', re.compile(rb'(?<![A-Za-z0-9])hf_[A-Za-z0-9]{30,}')),
    ('sk_key', re.compile(rb'(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{20,}')),
    ('github_token', re.compile(rb'(ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}')),
    ('google_api_key', re.compile(rb'AIza[0-9A-Za-z_\-]{30,}')),
    ('private_key_field', re.compile(rb'"private' rb'_key"')),
    ('url_credentials', re.compile(rb'[a-z][a-z0-9+.\-]*://[^\s/:@"\']+:[^\s/@"\'$]{6,}@')),
    ('url_token_param', re.compile(rb'[?&](token|access_token|api_key|apikey|key|sig|signature)=[A-Za-z0-9_\-%.]{16,}')),
    ('bearer_literal', re.compile(rb'Bearer\s+[A-Za-z0-9_\-.=]{20,}')),
    ('api_key_assign', re.compile(rb'(?<![A-Za-z0-9])(GEMINI|GOOGLE|OPENROUTER|NV|NVIDIA|ANTHROPIC|OPENAI|HF)_(API_)?(KEY|TOKEN)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}')),
]
ENV_VALUES = [os.environ[k].encode() for k in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'HF_TOKEN', 'OPENROUTER_API_KEY',
              'NV_API_KEY', 'NVIDIA_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY') if len(os.environ.get(k, '')) >= 16]
if os.environ.get('LCS_ROBUST_SYNC', '0') == '1':
    robust_copy_scan(stage, dest, flagout)
    sys.exit(0)

flags = []; copied = 0; same = 0; scanned = 0
for d, dirs, files in os.walk(stage):
    dirs.sort()
    for f in sorted(files):
        sp = os.path.join(d, f); rel = os.path.relpath(sp, stage)
        if os.path.islink(sp):
            continue
        try:
            data = open(sp, 'rb').read()
        except OSError:
            continue
        scanned += 1
        hit = [n for n, p in PATS if p.search(data)] + (['env_secret_value'] if any(v in data for v in ENV_VALUES) else [])
        if hit:
            flags.append('%s\t%s' % (rel, ','.join(hit))); continue
        dp = os.path.join(dest, rel)
        try:
            if open(dp, 'rb').read() == data:
                same += 1; continue
        except OSError:
            pass
        os.makedirs(os.path.dirname(dp), exist_ok=True)
        shutil.copyfile(sp, dp); copied += 1
os.makedirs(os.path.dirname(flagout), exist_ok=True)
open(flagout, 'w').write(''.join(x + '\n' for x in flags))
print('SCAN scanned=%d copied=%d unchanged=%d flagged=%d list=%s' % (scanned, copied, same, len(flags), flagout))
for x in flags[:50]:
    print('FLAG ' + x)
