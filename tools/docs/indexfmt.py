"""Parse the design-record index (distill_design/INDEX.md) in both its legacy and its grouped form.

Standard library only and Python 3.6-safe. Nothing here writes a file.

A row is a Markdown table row below a header row, or a bullet line that links a record
(`- [NAME](NAME): status`). The grouped form uses one table per `## ` section with the columns
`Topic | File | Status | Verdict | Evidence`; the section whose heading starts with "Archive" holds
superseded and closed rows, whose Status cell starts with `SUPERSEDED_BY:` or `CLOSED:`.

A File cell may name several entries of the folder (a record and its evidence archives), each in
backticks or separated by commas or " + ". A directory entry may carry a trailing slash.
"""
import re

COLUMNS = ('topic', 'file', 'status', 'verdict', 'evidence')
VERDICTS = ('GO', 'NO-GO', 'OPEN', 'DESIGN', 'REGISTERED', 'RESULT')
EVIDENCE = ('OK', 'PARTIAL', 'LOST-2-18')
ARCHIVE_PREFIXES = ('SUPERSEDED_BY:', 'CLOSED:')
MAX_ROW_CHARS = 300
MAX_STATUS_CHARS = 160

_SEP_RE = re.compile(r'^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$')
_LINK_RE = re.compile(r'^- \[([^\]]*)\]\(([^)]*)\)\s*:?\s*(.*)$')
_TOKEN_RE = re.compile(r'(?:\.\./)?[A-Za-z0-9_][A-Za-z0-9_.+/\-]*')
_EXT_RE = re.compile(r'\.(md|json|jsonl|tsv|tgz|tar|tar\.gz|txt|csv)$')


class Row(object):
    """One index row. `files` lists folder entries; cells absent from the format are None."""

    def __init__(self, lineno, kind, section, raw, topic=None, files=None, status=None,
                 verdict=None, evidence=None, file_cell=None):
        self.lineno = lineno
        self.kind = kind
        self.section = section
        self.raw = raw
        self.topic = topic
        self.files = files or []
        self.status = status
        self.verdict = verdict
        self.evidence = evidence
        self.file_cell = file_cell

    @property
    def archived(self):
        return bool(self.section) and self.section.lower().startswith('archive')

    def as_dict(self):
        return {'line': self.lineno, 'kind': self.kind, 'section': self.section,
                'topic': self.topic, 'files': list(self.files), 'status': self.status,
                'verdict': self.verdict, 'evidence': self.evidence}


def split_cells(line):
    """Cells of a Markdown table line, outer pipes removed, each stripped."""
    body = line.strip()
    if body.startswith('|'):
        body = body[1:]
    if body.endswith('|'):
        body = body[:-1]
    return [cell.strip() for cell in body.split('|')]


def file_names(cell):
    """Folder entries named in a File cell.

    Backticked names win; otherwise every token that carries a file extension (or a trailing
    slash, for a directory) counts. A token with a slash inside names a file outside the folder.
    """
    if cell is None:
        return []
    ticked = re.findall(r'`([^`]+)`', cell)
    if ticked:
        parts = ticked
    else:
        link = re.match(r'^\s*\[([^\]]*)\]\(([^)]*)\)\s*$', cell)
        parts = [link.group(2)] if link else _TOKEN_RE.findall(cell)
    names = []
    for part in parts:
        part = part.strip()
        is_dir = part.endswith('/')
        part = part.rstrip('/')
        if not part or ' ' in part:
            continue
        if is_dir or _EXT_RE.search(part):
            names.append(part)
    return names


def _column_map(cells):
    mapping = {}
    for idx, cell in enumerate(cells):
        key = cell.strip().lower()
        for col in COLUMNS:
            if key.startswith(col):
                mapping.setdefault(col, idx)
    return mapping


def parse(text):
    """Return (rows, tables) for an index text. tables lists (header line number, column names)."""
    lines = text.splitlines()
    rows = []
    tables = []
    section = None
    colmap = None
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        lineno = idx + 1
        stripped = line.strip()
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            if level >= 2:
                section = stripped.lstrip('#').strip()
            colmap = None
            idx += 1
            continue
        if stripped.startswith('|'):
            nxt = lines[idx + 1].strip() if idx + 1 < len(lines) else ''
            if colmap is None and _SEP_RE.match(nxt):
                cells = split_cells(stripped)
                colmap = _column_map(cells)
                tables.append((lineno, [c.lower() for c in cells]))
                idx += 2
                continue
            if colmap is not None and not _SEP_RE.match(stripped):
                cells = split_cells(stripped)

                def cell(name):
                    pos = colmap.get(name)
                    if pos is None or pos >= len(cells):
                        return None
                    return cells[pos]

                file_cell = cell('file')
                rows.append(Row(lineno, 'table', section, line, topic=cell('topic'),
                                files=file_names(file_cell), status=cell('status'),
                                verdict=cell('verdict'), evidence=cell('evidence'),
                                file_cell=file_cell))
            idx += 1
            continue
        colmap = None
        match = _LINK_RE.match(stripped)
        if match:
            rows.append(Row(lineno, 'bullet', section, line, topic=match.group(1),
                            files=file_names(match.group(2)), status=match.group(3).strip() or None,
                            file_cell=match.group(2)))
        idx += 1
    return rows, tables


def listed_files(rows):
    """Every folder entry named by any row, in order (repeats kept)."""
    out = []
    for row in rows:
        out.extend(row.files)
    return out


def read_listing(path, ignore=('INDEX.md',)):
    """Names from a saved one-name-per-line `ls` of the folder, minus ignored names."""
    names = []
    with open(path, 'r') as handle:
        for line in handle:
            name = line.strip().rstrip('/')
            if name and name not in ignore:
                names.append(name)
    return names
