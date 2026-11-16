"""Mode-preserving writes confined to one derived output tree."""
from contextlib import contextmanager
import stat
from pathlib import Path


def manifest_members(root):
    """Read the sealed member names without walking the surrounding runtime tree."""
    names = []
    for line in (Path(root) / 'SHA256SUMS.txt').read_text().splitlines():
        digest_, name = line.split('  ', 1)
        if (len(digest_) != 64 or any(c not in '0123456789abcdef' for c in digest_)
                or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))
                or name in names):
            raise ValueError('invalid sealed member')
        names.append(name)
    return sorted(names)


def member_directories(names):
    return {'.'} | {str(p) for name in names for p in Path(name).parents}


def mode_inventory(root):
    root = Path(root)
    names = manifest_members(root)
    dirs = member_directories(names)
    modes = {}
    for name in sorted(set(names) | dirs, key=lambda n: (len(Path(n).parts), n)):
        mode = (root / name).lstat().st_mode
        if not (stat.S_ISDIR(mode) if name in dirs else stat.S_ISREG(mode)):
            raise ValueError('unsupported sealed member: ' + name)
        modes[name] = stat.S_IMODE(mode)
    return modes


class SealedOutput:
    def __init__(self, root, file_mode=0o400):
        root = Path(root).absolute()
        if root != root.resolve(strict=True): refuse('symlink in output root')
        self.root = root
        self.file_mode = file_mode

    def checked(self, path):
        path = Path(path).absolute()
        if (path != self.root and self.root not in path.parents) or '..' in path.parts:
            refuse('write outside output directory')
        for p in [path, *path.parents]:
            if p.is_symlink(): refuse('symlink in output write')
            if p == self.root: break
        if path.is_file() and path.stat().st_nlink != 1:
            refuse('linked output file')
        return path

    @contextmanager
    def writable(self, path, mode=None):
        path = self.checked(path)
        if path == self.root: refuse('write must name an output member')
        parent = path.parent
        parent_mode = stat.S_IMODE(parent.stat().st_mode)
        final_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else (
            self.file_mode if mode is None else mode)
        try:
            parent.chmod(parent_mode | stat.S_IWUSR)
            if path.exists(): path.chmod(final_mode | stat.S_IWUSR)
            yield path
        finally:
            try:
                if path.exists(): path.chmod(final_mode)
            finally:
                parent.chmod(parent_mode)

    def text(self, path, text, mode=None):
        with self.writable(path, mode) as p: p.write_text(text)

    def write(self, path, value, mode=None):
        self.text(path, enc(value) + '\n', mode)

    def copy(self, source, path, mode=None):
        with self.writable(path, mode) as p: shutil.copyfile(source, p)

    def mkdir(self, path, mode):
        with self.writable(path, mode) as p: p.mkdir(mode=mode | stat.S_IWUSR)
