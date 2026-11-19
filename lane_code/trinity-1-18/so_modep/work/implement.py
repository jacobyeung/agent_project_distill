from pathlib import Path
T=Path(__file__).resolve().parent/'tree'
p=T/'student_pilot/orchard_paths.py'
s=p.read_text()
s=s.replace('def owned(path, *, resolve=None):', '''def _within(path, root):
    """Lexical containment; resolution and filesystem checks remain at callers."""
    if os.environ.get('S1_PREP_FAST_PATHS') != '1':
        return path.is_relative_to(root)
    # PosixPath.parts is normalized exactly as the parents used by is_relative_to.
    # The anchor check also handles a relative root such as Path('.').
    from pathlib import PurePosixPath
    root = Path(root)
    if not isinstance(path, PurePosixPath) or not isinstance(root, PurePosixPath):
        return path.is_relative_to(root)
    parts, prefix = path.parts, root.parts
    return path.anchor == root.anchor and parts[:len(prefix)] == prefix


def owned(path, *, resolve=None):''')
s=s.replace('path.is_relative_to(root) and path != root', '_within(path, root) and path != root')
s=s.replace("    # JSON permits both", "    if os.environ.get('S1_PREP_FAST_PATHS') == '1':\n        return _resolve_read_fast(path, mapping, resolve)\n    # JSON permits both")
s += '''

from functools import lru_cache


@lru_cache(maxsize=32)
def _mapping_items(mapping):
    # Cache text parsing only. Never cache resolved paths, stat results or hashes.
    pairs = json.loads(mapping) if mapping.startswith('{') else dict([mapping.split('=', 1)])
    return tuple((source, Path(destination)) for source, destination in pairs.items())


def _resolve_read_fast(path, mapping, resolve):
    allowed = {'/data2': PROJECT / 'data2root',
               '/home/jjyeung/agent_project': PROJECT / 'source_home'}
    for source, destination in _mapping_items(mapping):
        if source not in allowed:
            raise ValueError('Unsupported logical read root')
        if not (destination == allowed[source] or _within(destination, SCRATCH)):
            raise ValueError('Mapped inputs must stay in owned Orchard storage')
        if '..' in destination.parts or not owned(destination, resolve=resolve):
            raise ValueError('Mapped destination escapes owned storage')
        source_path = Path(source)
        if _within(path, source_path):
            if '..' in path.parts:
                raise ValueError('Read path traversal is forbidden')
            result = destination.joinpath(*path.parts[len(source_path.parts):])
            if not _within(resolve(result), resolve(destination)):
                raise ValueError('Mapped input symlink escapes its root')
            return result
    return path
'''
p.write_text(s)
p=T/'student_pilot/s1_admission.py';s=p.read_text()
s=s.replace('        from .orchard_paths import resolve_read\n','        from .orchard_paths import resolve_read, _within\n',1)
s=s.replace('not any(path.is_relative_to(root) for root in self.roots)', 'not any(_within(path, root) for root in self.roots)')
p.write_text(s)
p=T/'student_pilot/s1_exclusions.py';s=p.read_text()
# This read-only iterator avoids decoding unselected payloads; SQL retains the original i order.
pos=s.index('def _database(')
s=s[:pos]+'''def _selected_rows(connection, wanted):
    """Read selected rows in native i order without materializing other payloads."""
    # SQLite INTEGER indices fit in int64. Out-of-range requests remain missing
    # and are rejected by the existing found != wanted check.
    ordered = sorted(index for index in wanted if index <= (1 << 63)-1)
    for start in range(0, len(ordered), 256):
        batch = ordered[start:start+256]
        placeholders = ','.join('?' for _ in batch)
        yield from connection.execute(
            'SELECT i,row FROM rows WHERE i IN ('+placeholders+') ORDER BY i', batch)


'''+s[pos:]
s=s.replace('    with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as connection:\n        rule.expect(source,', '''    with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as connection:
        import os
        fast = os.environ.get('S1_PREP_SELECT_SQL') == '1'
        def rows():
            return (_selected_rows(connection, wanted) if fast else
                    connection.execute("SELECT i,row FROM rows ORDER BY i"))
        rule.expect(source,''',1)
s=s.replace('for index, text in connection.execute("SELECT i,row FROM rows ORDER BY i")\n                             if index in wanted)', 'for index, text in rows()\n                             if index in wanted)',1)
s=s.replace('        for index, text in connection.execute("SELECT i,row FROM rows ORDER BY i"):', '        for index, text in rows():',1)
p.write_text(s)
