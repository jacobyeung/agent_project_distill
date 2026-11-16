#!/usr/bin/env python3
"""Generate a lane brief from the templates in agent/templates/briefs/.

Usage:
  mkbrief.py operator|reviewer|builder --lane L --node N --events E --cap-gb G
             --scratch-floor-gb F --io-class C --limit T [--limits TEXT] [--title TEXT]
             [--why TEXT] [--do TEXT] [--lane-dir D] [--claude] [--out FILE]
  mkbrief.py successor --predecessor BRIEF --status STATUS.md [--rotate EVENT] (same options)

The header and the budget table come from the arguments; `Why` and `Do` stay as markers for the
orchestrator unless --why/--do fill them. The successor role builds its brief from the
predecessor's brief, its STATUS.md and (optionally) its rotate event: it names the folders the
predecessor used, quotes the next step from STATUS.md and carries the predecessor's Do section.
The template states the role once and points at the lane rules instead of restating them.
--out refuses an existing file. Standard library only; Python 3.6-safe.
"""
import argparse
import os
import re
import string
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES = os.path.join(REPO, 'agent', 'templates', 'briefs')
B = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30'
LANE_RULES = B + '/tools/LANE_RULES.md'
CLAUDE_RULES = B + '/tools/CLAUDE_LANE_RULES.md'
ROLES = ('operator', 'reviewer', 'builder', 'successor')
TITLES = {'operator': 'operator', 'reviewer': 'reviewer', 'builder': 'builder',
          'successor': 'successor'}
IO_CLASSES = {
    'none': 'no transfer to or from /home or /data* and none across the head node; single named '
            'files under 20 MB only',
    'named-reads': 'read the files this brief names on /home and /data*, each once, in bounded '
                   'parts; nothing above 20 MB',
    'governed': 'every stream above 20 MB registers with the IO governor as the lane rules say, '
                'all streams of a step at once',
}
MARKER = 'TODO(orchestrator): fill in.'
_PATH_RE = re.compile(r'(?<![A-Za-z0-9_.\-/])(/(?:scratch|data2|data3|data|home)/[A-Za-z0-9_.@+\-/]+)')
_NEXT_RE = re.compile(r'^(?:[-*]\s*)?(?:\*\*)?(next|next step|owed)\b', re.I)


def _read(path):
    with open(path, 'r') as handle:
        return handle.read()


def _section(text, title_prefix):
    """Body of the first `## ` section whose title starts with title_prefix, or ''."""
    lines = text.splitlines()
    out = []
    inside = False
    for line in lines:
        if line.startswith('## '):
            if inside:
                break
            inside = line[3:].strip().lower().startswith(title_prefix.lower())
            continue
        if inside:
            out.append(line)
    return '\n'.join(out).strip()


def folders(*texts):
    """Directories named in the texts: absolute paths, trimmed to their directory part."""
    seen = []
    for text in texts:
        for path in _PATH_RE.findall(text):
            path = path.rstrip('.,;:)')
            base = os.path.basename(path.rstrip('/'))
            if '.' in base and not path.endswith('/'):
                path = os.path.dirname(path)
            path = path.rstrip('/')
            if path and path not in seen:
                seen.append(path)
    return seen


def next_steps(status_text, limit=12):
    """What the predecessor was doing and owes next, verbatim from STATUS.md.

    Lines that start with "Next" or "Owed" come first, wherever they sit; then the lines of the
    first `## ` section, which a STATUS keeps as its current state.
    """
    explicit = []
    first = []
    section = 0
    for line in status_text.splitlines():
        if line.startswith('## '):
            section += 1
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.startswith(('- ', '* ')):
            stripped = stripped[2:].strip()
        if len(stripped) > 400:
            stripped = stripped[:397] + '...'
        if _NEXT_RE.match(line.strip()):
            explicit.append(stripped)
        elif section == 1:
            first.append(stripped)
    out = []
    for line in explicit + first:
        if line not in out:
            out.append(line)
    return out[:limit]


def predecessor_lane(brief_text):
    match = re.match(r'^#\s*Lane\s+([A-Za-z0-9_.\-]+)', brief_text)
    return match.group(1) if match else 'unknown'


def render(role, args):
    if role not in ROLES:
        raise ValueError('unknown role %r' % role)
    if args.io_class not in IO_CLASSES:
        raise ValueError('io class %r is not one of %s' % (args.io_class, ', '.join(IO_CLASSES)))
    templates = args.templates or TEMPLATES
    lane_dir = args.lane_dir or '/scratch/jjyeung/orch_n30/%s' % args.lane
    values = {
        'lane': args.lane, 'node': args.node, 'events': args.events, 'limit': args.limit,
        'cap_gb': args.cap_gb, 'scratch_floor_gb': args.scratch_floor_gb,
        'io_class': args.io_class, 'io_meaning': IO_CLASSES[args.io_class],
        'limits_text': args.limits or 'none beyond the budgets above.',
        'lane_dir': lane_dir, 'role_title': TITLES[role],
        'title_suffix': (': ' + args.title) if args.title else '',
        'lane_rules': LANE_RULES,
        'extra_rules': (', then `%s`' % CLAUDE_RULES) if args.claude else '',
        'why': args.why or MARKER, 'do': args.do or MARKER,
    }
    if role == 'successor':
        if not args.predecessor or not args.status:
            raise ValueError('successor needs --predecessor and --status')
        brief_text = _read(args.predecessor)
        status_text = _read(args.status)
        rotate_text = _read(args.rotate) if args.rotate else ''
        pred_do = _section(brief_text, 'Do') or brief_text.strip()
        found = folders(brief_text, status_text, rotate_text)
        nexts = next_steps(status_text)
        values.update({
            'pred_lane': predecessor_lane(brief_text),
            'pred_brief': args.predecessor_cite or args.predecessor,
            'pred_status': args.status_cite or args.status,
            'pred_rotate': ('`%s`' % (args.rotate_cite or args.rotate)) if args.rotate
            else 'none given; look for the newest `*_RESULT_rotate*.md` in the events folder',
            'pred_folders': '\n'.join('- `%s`' % path for path in found) or '- none found',
            'pred_next': '\n'.join('- %s' % line for line in nexts)
            or '- STATUS.md names no next step; read it whole.',
            'pred_do': pred_do,
        })
        if not args.title:
            values['title_suffix'] = ': successor of lane %s' % values['pred_lane']
    header = string.Template(_read(os.path.join(templates, '_header.md')))
    body = string.Template(_read(os.path.join(templates, role + '.md')))
    text = header.substitute(values) + body.substitute(values)
    return text


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('role', choices=ROLES)
    parser.add_argument('--lane', required=True)
    parser.add_argument('--node', required=True)
    parser.add_argument('--events', required=True)
    parser.add_argument('--cap-gb', required=True, type=int)
    parser.add_argument('--scratch-floor-gb', required=True, type=int)
    parser.add_argument('--io-class', required=True, choices=sorted(IO_CLASSES))
    parser.add_argument('--limit', required=True, help='session limit, UTC, e.g. 2026-11-16T22:30Z')
    parser.add_argument('--limits', default=None, help='free-text lane-specific limits')
    parser.add_argument('--title', default=None)
    parser.add_argument('--why', default=None)
    parser.add_argument('--do', default=None)
    parser.add_argument('--lane-dir', default=None)
    parser.add_argument('--claude', action='store_true', help='also point at CLAUDE_LANE_RULES.md')
    parser.add_argument('--predecessor', default=None, help='predecessor brief (successor)')
    parser.add_argument('--status', default=None, help="predecessor's STATUS.md (successor)")
    parser.add_argument('--rotate', default=None, help="predecessor's rotate event (successor)")
    parser.add_argument('--predecessor-cite', default=None, help='path to print for --predecessor')
    parser.add_argument('--status-cite', default=None, help='path to print for --status')
    parser.add_argument('--rotate-cite', default=None, help='path to print for --rotate')
    parser.add_argument('--templates', default=None)
    parser.add_argument('--out', default=None)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        text = render(args.role, args)
    except (ValueError, KeyError) as err:
        sys.stderr.write('REFUSED: %s\n' % err)
        return 2
    if args.out:
        if os.path.exists(args.out):
            sys.stderr.write('REFUSED: %s exists; choose a fresh path\n' % args.out)
            return 2
        fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'w') as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
