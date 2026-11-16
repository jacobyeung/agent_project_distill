"""Accept a trainer build as one commit: tree_commit.py --repo CLONE --branch BR (--tree DIR | --tar FILE)
   --build NAME --expect-seal HEX [--prefix trainer] [--subdir REL] [--seal-code DIR] [--seal-python PY]
   [--report FILE]

1. Reads the build (a directory, or a tar extracted into a fresh directory under TMPDIR; --subdir picks the
   tree inside it, for example ``tree_r1``). Members outside --subdir are left out and listed in the report.
2. Computes the seal with the tree's own code (``student_pilot/source_seal.inventory`` and
   ``p3_provenance.digest``, through seal_of.py under the trainer interpreter) and refuses unless the
   ``tree_sha256`` starts with --expect-seal.
3. Builds the commit with Git plumbing and no working tree: a private index, ``hash-object -w --no-filters``
   of every sealed member (ignore patterns and attribute filters never apply), ``write-tree``, then the
   parent's root tree with the prefix entry replaced (``ls-tree``/``mktree``), plus one row appended to
   tools/treegit/SEALS.jsonl, ``commit-tree`` with message ``trainer: <build> seal <digest> tar <sha256>``.
4. Verifies before the branch moves: ``git archive <commit> <prefix>`` extracted into a fresh directory must
   reproduce the seal; otherwise it refuses and names the differing members.
5. ``update-ref`` with the old value, so a concurrent move of the branch makes it refuse. If the branch is
   checked out in CLONE, ``read-tree -m -u old new`` brings that working tree along.

Members the seal skips (directories ``.git``, ``__pycache__``, ``artifacts``) stay out of Git. A link, a
non-regular file, a member above 16 MB or a path Git cannot store makes it refuse and name the member.
Python 3.6 safe, standard library only. Exit 0 on success with a JSON report on stdout; exit 2 on refusal.
"""
import argparse
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from tools.orchkit import util  # noqa: E402

SEAL_SKIP_DIRS = ('.git', '__pycache__', 'artifacts')  # the dirs student_pilot/source_seal.inventory skips
MAX_BYTES = 16000000
SEALS_PATH = ('tools', 'treegit', 'SEALS.jsonl')
DEFAULT_SEAL_PYTHON = '/scratch/jjyeung/envs/p1cpu/bin/python'
EMPTY_TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


class Refused(Exception):
    pass


def _run(args, cwd=None, env=None, data=None, check=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.Popen(args, cwd=cwd, env=e, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(data)
    if check and p.returncode != 0:
        raise Refused('%s failed rc=%d: %s' % (' '.join(args[:4]), p.returncode,
                                               err.decode('utf-8', 'replace').strip()[-400:]))
    return p.returncode, out, err


class Git(object):
    def __init__(self, repo, index=None):
        self.repo = repo
        self.env = {'GIT_INDEX_FILE': index} if index else {}

    def __call__(self, *args, **kw):
        data = kw.pop('data', None)
        check = kw.pop('check', True)
        rc, out, err = _run(['git', '-C', self.repo] + list(args), env=self.env, data=data, check=check)
        return out if check else (rc, out)

    def text(self, *args, **kw):
        return self(*args, **kw).decode('utf-8').strip()


def _safe_component(name):
    low = name.lower().rstrip('. ')
    return name not in ('', '.', '..') and low != '.git' and '/' not in name and '\0' not in name


def collect(root):
    """Walk ``root`` like the seal does. Returns (files [(rel, abspath, mode)], skipped dirs, empty dirs)."""
    files, skipped, empty = [], [], []
    for d, dirs, names in os.walk(root):
        rel_d = os.path.relpath(d, root)
        keep = []
        for x in sorted(dirs):
            rel = x if rel_d == '.' else os.path.join(rel_d, x)
            st = os.lstat(os.path.join(d, x))
            if stat.S_ISLNK(st.st_mode):
                raise Refused('member is a link: %s' % rel)
            if x in SEAL_SKIP_DIRS:
                skipped.append(rel + '/')
                continue
            keep.append(x)
        dirs[:] = keep
        if not names and not keep and rel_d != '.':
            empty.append(rel_d + '/')
        for x in sorted(names):
            rel = x if rel_d == '.' else os.path.join(rel_d, x)
            p = os.path.join(d, x)
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                raise Refused('member is a link: %s' % rel)
            if not stat.S_ISREG(st.st_mode):
                raise Refused('member is not a regular file: %s' % rel)
            if st.st_size > MAX_BYTES:
                raise Refused('member above 16 MB: %s' % rel)
            if not all(_safe_component(c) for c in rel.split(os.sep)):
                raise Refused('Git cannot store this path: %s' % rel)
            files.append((rel, p, '100755' if st.st_mode & 0o100 else '100644'))
    return files, skipped, empty


def extract_tar(tar_path, dest, subdir):
    """Extract the members under ``subdir`` into ``dest``; return the members left out."""
    sub = subdir.strip('/')
    left_out = []
    with tarfile.open(tar_path, 'r:*') as tf:
        for m in tf:
            name = m.name[2:] if m.name.startswith('./') else m.name
            name = name.rstrip('/')
            parts = name.split('/')
            if name.startswith('/') or '..' in parts:
                raise Refused('tar member with an unsafe path: %s' % m.name)
            if sub and not (name == sub or name.startswith(sub + '/')):
                if m.isfile():
                    left_out.append(name)
                continue
            rel = name[len(sub):].lstrip('/') if sub else name
            if not rel:
                continue
            target = os.path.join(dest, rel)
            if m.isdir():
                if not os.path.isdir(target):
                    os.makedirs(target)
                continue
            if not m.isfile():
                raise Refused('tar member Git cannot hold exactly (link or special file): %s' % m.name)
            if not os.path.isdir(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            src = tf.extractfile(m)
            with open(target, 'xb') as out:
                while True:
                    block = src.read(1 << 20)
                    if not block:
                        break
                    out.write(block)
            os.chmod(target, 0o755 if m.mode & 0o100 else 0o644)
    return left_out


def seal_of(seal_python, code_root, tree):
    script = os.path.join(HERE, 'seal_of.py')
    rc, out, err = _run([seal_python, '-I', '-B', script, '--code', code_root, tree], check=False)
    try:
        res = json.loads(out.decode('utf-8'))['trees'][tree]
    except (ValueError, KeyError):
        raise Refused('seal code failed rc=%d: %s' % (rc, err.decode('utf-8', 'replace').strip()[-400:]))
    if 'error' in res:
        raise Refused('the seal code refuses %s: %s' % (tree, res['error']))
    return res['tree_sha256'], res['files']


def ls_tree(git, tree):
    entries = {}
    for rec in git('ls-tree', '-z', tree).split(b'\0'):
        if not rec:
            continue
        meta, name = rec.split(b'\t', 1)
        mode, typ, sha = meta.decode().split(' ')
        entries[name] = (mode, typ, sha)
    return entries


def replace_path(git, tree, comps, entry):
    """Return a new tree id: ``tree`` with the entry at path ``comps`` set to (mode, type, sha)."""
    entries = ls_tree(git, tree) if tree else {}
    name = comps[0].encode('utf-8')
    if len(comps) == 1:
        entries[name] = entry
    else:
        old = entries.get(name)
        if old is not None and old[1] != 'tree':
            raise Refused('%s exists and is not a directory' % comps[0])
        entries[name] = ('040000', 'tree', replace_path(git, old[2] if old else None, comps[1:], entry))
    data = b''.join(('%s %s %s\t' % e).encode() + n + b'\0' for n, e in sorted(entries.items()))
    return git.text('mktree', '-z', data=data)


def diff_files(a, b):
    names = sorted(set(a) | set(b))
    return [n for n in names if a.get(n) != b.get(n)]


def tree_commit(repo, branch, build, expect_seal, tree=None, tar=None, prefix='trainer', subdir='',
                seal_code=None, seal_python=DEFAULT_SEAL_PYTHON, utc=None, before_update_ref=None):
    if not re.match(r'^[0-9a-f]{8,64}$', expect_seal or ''):
        raise Refused('--expect-seal must be 8 to 64 lowercase hex characters')
    if not re.match(r'^[A-Za-z0-9._-]+$', prefix) or not _safe_component(prefix):
        raise Refused('--prefix must be one path component')
    if not re.match(r'^[A-Za-z0-9._-]+$', build):
        raise Refused('--build must match [A-Za-z0-9._-]+')
    if (tree is None) == (tar is None):
        raise Refused('give exactly one of --tree and --tar')
    repo = os.path.abspath(repo)
    git = Git(repo)
    if _run(['git', 'check-ref-format', '--branch', branch], check=False)[0] != 0:
        raise Refused('bad branch name %s' % branch)
    rc, old = git('rev-parse', '-q', '--verify', 'refs/heads/%s^{commit}' % branch, check=False)
    if rc != 0:
        raise Refused('branch %s does not exist in %s' % (branch, repo))
    old = old.decode().strip()
    work = tempfile.mkdtemp(prefix='treegit_')
    report = {'branch': branch, 'build': build, 'parent': old, 'prefix': prefix, 'work': work}
    if tar is not None:
        tar = os.path.abspath(tar)
        report['tar_sha256'] = util.sha256_file(tar)[0]
        root = os.path.join(work, 'src')
        os.makedirs(root)
        report['left_out'] = extract_tar(tar, root, subdir)
    else:
        report['tar_sha256'] = None
        root = os.path.join(os.path.abspath(tree), subdir) if subdir else os.path.abspath(tree)
        report['left_out'] = []
    if not os.path.isdir(root):
        raise Refused('build tree %s is missing' % root)
    files, skipped, empty = collect(root)
    report['seal_skipped_dirs'] = skipped
    report['empty_dirs_not_in_git'] = empty
    seal, inv = seal_of(seal_python, seal_code or root, root)
    report['seal'] = seal
    report['files'] = len(inv)
    if not seal.startswith(expect_seal):
        raise Refused('seal %s does not start with --expect-seal %s' % (seal, expect_seal))
    mine = sorted(f[0] for f in files)
    if mine != sorted(inv):
        raise Refused('member set differs from the seal inventory: %s' % diff_files(dict.fromkeys(mine), dict.fromkeys(inv))[:10])

    # Subtree from a private index; blobs written without filters.
    index = os.path.join(work, 'index')
    ig = Git(repo, index=index)
    ids = git.text('hash-object', '-w', '--no-filters', '--stdin-paths',
                   data=''.join(f[1] + '\n' for f in files).encode('utf-8', 'surrogateescape')).split('\n')
    if len(ids) != len(files):
        raise Refused('hash-object returned %d ids for %d files' % (len(ids), len(files)))
    info = b''.join(('%s %s\t' % (f[2], i)).encode() + f[0].encode('utf-8', 'surrogateescape') + b'\0'
                    for f, i in zip(files, ids))
    ig('update-index', '-z', '--add', '--index-info', data=info)
    sub_tree = ig.text('write-tree')
    report['git_tree'] = sub_tree

    # Root tree: parent's tree with the prefix entry replaced and one SEALS.jsonl row appended.
    root_tree = git.text('rev-parse', old + '^{tree}')
    new_root = replace_path(git, root_tree, [prefix], ('040000', 'tree', sub_tree))
    rc, prev = git('cat-file', 'blob', '%s:%s' % (old, '/'.join(SEALS_PATH)), check=False)
    prev = prev if rc == 0 else b''
    if prev and not prev.endswith(b'\n'):
        prev += b'\n'
    row = {'utc': utc or util.utc_iso(), 'build': build, 'seal': seal, 'tar_sha256': report['tar_sha256'],
           'parent': old, 'prefix': prefix, 'git_tree': sub_tree, 'files': len(inv)}
    seals_blob = git.text('hash-object', '-w', '--no-filters', '--stdin', data=prev + util.canonical_json(row) + b'\n')
    new_root = replace_path(git, new_root, list(SEALS_PATH), ('100644', 'blob', seals_blob))
    msg = 'trainer: %s seal %s tar %s\n' % (build, seal, report['tar_sha256'] or 'none')
    commit = git.text('commit-tree', new_root, '-p', old, data=msg.encode('utf-8'))
    report['commit'] = commit

    # Verify through git archive before the branch moves.
    vdir = os.path.join(work, 'verify')
    os.makedirs(vdir)
    arch = os.path.join(work, 'archive.tar')
    with open(arch, 'xb') as f:
        f.write(git('archive', '--format=tar', commit, prefix))
    extract_tar(arch, vdir, '')
    vseal, vinv = seal_of(seal_python, seal_code or root, os.path.join(vdir, prefix))
    if vseal != seal:
        raise Refused('git archive of %s does not reproduce the seal; members differing: %s'
                      % (commit, diff_files(inv, vinv)[:20]))
    report['verified_archive_seal'] = vseal

    if before_update_ref is not None:
        before_update_ref()
    rc, out = git('update-ref', '-m', 'tree_commit %s' % build, 'refs/heads/' + branch, commit, old, check=False)
    if rc != 0:
        raise Refused('branch %s moved since it was read (expected %s); nothing changed' % (branch, old))
    rc, head = git('symbolic-ref', '-q', 'HEAD', check=False)
    if rc == 0 and head.decode().strip() == 'refs/heads/' + branch and git.text('rev-parse', '--is-bare-repository') == 'false':
        rc, out = git('read-tree', '-m', '-u', old, commit, check=False)
        report['worktree_synced'] = rc == 0
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--repo', required=True)
    ap.add_argument('--branch', required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--tree')
    g.add_argument('--tar')
    ap.add_argument('--build', required=True)
    ap.add_argument('--expect-seal', required=True)
    ap.add_argument('--prefix', default='trainer')
    ap.add_argument('--subdir', default='')
    ap.add_argument('--seal-code', default=None, help='tree whose student_pilot seal code to run (default: the build)')
    ap.add_argument('--seal-python', default=os.environ.get('TREEGIT_SEAL_PYTHON', DEFAULT_SEAL_PYTHON))
    ap.add_argument('--report', default=None)
    a = ap.parse_args(argv)
    try:
        rep = tree_commit(a.repo, a.branch, a.build, a.expect_seal, tree=a.tree, tar=a.tar, prefix=a.prefix,
                          subdir=a.subdir, seal_code=a.seal_code, seal_python=a.seal_python)
    except Refused as exc:
        sys.stderr.write('REFUSED: %s\n' % exc)
        return 2
    if a.report:
        util.write_json(a.report, rep)
    short = dict(rep)
    short['left_out'] = len(rep['left_out'])
    sys.stdout.write(json.dumps(short, sort_keys=True) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
