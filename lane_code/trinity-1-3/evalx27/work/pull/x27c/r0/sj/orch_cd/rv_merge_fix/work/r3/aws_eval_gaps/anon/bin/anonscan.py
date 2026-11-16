#!/usr/bin/env python3
"""Leak scanner for AWS kits (Trinity side only; the word list never leaves Trinity).

usage:
  anonscan.py [--words W.json] [--report OUT.json] TARGET...
TARGET forms:
  names:FILE      one path per line (remote listings, tar member lists): every line is a name
  text:PATH       file or directory: names of every entry, plus content by type (see below)
  argv:FILE       runtime capture (NUL- or newline-separated argv/env/log text): every line strict
  cap:FILE        cap.py output JSON (argv, env, names): every entry strict
  log:PATH        log file(s): every line strict
Content rules for text: (strict = every line; code = every line, with the code_allow contexts removed first)
  *.sh *.py *.txt *.md *.out *.log *.cfg (no extension too) -> code; *.json -> keys and whitespace-free string
  values (ids, paths) strict, prose skipped; *.jsonl (data rows, <=64 MB) -> keys and path-like values only; *.tar -> member names;
  *.gz *.npz *.pt *.png *.mp4 *.safetensors and other binaries -> name only.
Hex tokens (>= 6 hex digits, even length) that decode to printable ASCII are decoded and scanned too.
Exit 0 = zero blocking hits; 1 = hits (listed in the report and on stdout); 2 = usage error.
"""
import argparse, json, os, re, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_EXT = {'.sh', '.py', '.txt', '.md', '.out', '.log', '.cfg', '.tsv', '.csv', '.yaml', '.yml', '.toml', '.ini', ''}
BIN_EXT = {'.gz', '.npz', '.pt', '.png', '.jpg', '.mp4', '.safetensors', '.bin', '.tgz', '.zst', '.npy', '.pyc', '.so'}
MAX_TEXT = 64 << 20
HEX = re.compile(r'(?<![0-9A-Fa-f])([0-9A-Fa-f]{6,})(?![0-9A-Fa-f])')


class Scanner:
    def __init__(self, words):
        w = json.load(open(words))
        alt = '|'.join(re.escape(s) for s in w['substr'])
        walt = '|'.join(re.escape(s) for s in w['word'])
        self.block = re.compile('(%s)|(?<![A-Za-z0-9])(%s)(?![A-Za-z0-9])' % (alt, walt), re.I)
        self.adv = re.compile('|'.join(re.escape(s) for s in w['advisory']), re.I)
        self.allow = re.compile('|'.join(w['code_allow']), re.I)
        self.hits, self.advisory, self.scanned = [], [], 0

    def _decode_hex(self, s):
        out = []
        for m in HEX.finditer(s):
            h = m.group(1)
            if len(h) % 2:
                continue
            try:
                b = bytes.fromhex(h).decode('ascii')
            except (ValueError, UnicodeDecodeError):
                continue
            if b.isprintable() and sum(c.isalpha() for c in b) >= 3:
                out.append(b)
        return out

    def check(self, where, kind, s, code=False):
        self.scanned += 1
        t = self.allow.sub(' ', s) if code else s
        found = [m.group(0) for m in self.block.finditer(t)]
        found += ['hex:' + d for d in self._decode_hex(t) if self.block.search(d)]
        if found:
            self.hits.append({'where': where, 'kind': kind, 'words': sorted(set(x.lower() for x in found)),
                              'text': s if len(s) <= 300 else s[:300] + '...'})
        a = [m.group(0).lower() for m in self.adv.finditer(t)]
        if a:
            self.advisory.append({'where': where, 'kind': kind, 'words': sorted(set(a))})

    # ---- content walkers
    def json_obj(self, where, o, path='$', paths_only=False):
        if isinstance(o, dict):
            for k, v in o.items():
                self.check(where, 'json-key ' + path, str(k))
                self.json_obj(where, v, path + '.' + str(k)[:40], paths_only)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                self.json_obj(where, v, path + '[]', paths_only)
        elif isinstance(o, str):
            if not re.search(r'\s', o) and (not paths_only or '/' in o):
                self.check(where, 'json-val ' + path, o)

    def text_file(self, p, label):
        ext = os.path.splitext(p)[1].lower()
        try:
            size = os.path.getsize(p)
        except OSError:
            return
        if ext in BIN_EXT or ext.startswith('.part'):
            return
        if ext == '.tar':
            try:
                with tarfile.open(p) as tf:
                    for m in tf:
                        self.check(label, 'tar-member', m.name)
                        if m.issym() or m.islnk():
                            self.check(label, 'tar-link ' + m.name, m.linkname)
            except (tarfile.TarError, OSError) as e:
                self.hits.append({'where': label, 'kind': 'tar-unreadable', 'words': [], 'text': repr(e)})
            return
        if size > MAX_TEXT:
            self.advisory.append({'where': label, 'kind': 'skipped-large', 'words': [str(size)]})
            return
        data = open(p, 'rb').read()
        if b'\0' in data[:8192] and ext not in ('.out', '.log'):
            return
        txt = data.decode('utf-8', 'replace')
        if ext == '.json':
            try:
                self.json_obj(label, json.loads(txt))
                return
            except ValueError:
                pass
        if ext == '.jsonl':  # data rows: keys and path-like values (containing '/') only; other values are data
            for n, line in enumerate(txt.splitlines(), 1):
                if line.strip():
                    try:
                        self.json_obj('%s:%d' % (label, n), json.loads(line), paths_only=True)
                    except ValueError:
                        self.check('%s:%d' % (label, n), 'line', line)
            return
        code = ext in ('.sh', '.py', '')
        for n, line in enumerate(txt.splitlines(), 1):
            self.check('%s:%d' % (label, n), 'line', line, code=code)

    def text_target(self, root):
        root = os.path.abspath(root)
        if os.path.isfile(root):
            self.check(root, 'name', root)
            self.text_file(root, root)
            return
        for dp, dns, fns in os.walk(root):
            dns.sort()
            for n in dns + sorted(fns):
                p = os.path.join(dp, n)
                rel = os.path.relpath(p, root)
                self.check(rel, 'name', rel)
                if os.path.islink(p):
                    self.check(rel, 'symlink-target', os.readlink(p))
            for n in sorted(fns):
                p = os.path.join(dp, n)
                if not os.path.islink(p):
                    self.text_file(p, os.path.relpath(p, os.path.dirname(root)))

    def lines_target(self, p, kind):
        data = open(p, 'rb').read().decode('utf-8', 'replace')
        for n, line in enumerate(re.split(r'[\n\0]', data), 1):
            if line:
                self.check('%s:%d' % (os.path.basename(p), n), kind, line)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--words', default=os.path.join(HERE, 'anon_words.json'))
    ap.add_argument('--report')
    ap.add_argument('--max-print', type=int, default=40)
    ap.add_argument('targets', nargs='+')
    a = ap.parse_args(argv)
    sc = Scanner(a.words)
    for t in a.targets:
        kind, _, path = t.partition(':')
        if kind == 'names':
            sc.lines_target(path, 'name')
        elif kind == 'text':
            sc.text_target(path)
        elif kind == 'argv':
            sc.lines_target(path, 'runtime')
        elif kind == 'cap':  # cap.py output: argv, env and names, all strict
            doc = json.load(open(path))
            for key in ('argv', 'env', 'names'):
                for n, s in enumerate(doc.get(key, [])):
                    sc.check('%s:%s[%d]' % (os.path.basename(path), key, n), 'runtime-' + key, s)
        elif kind == 'log':
            if os.path.isdir(path):
                for dp, _, fns in os.walk(path):
                    for n in sorted(fns):
                        sc.lines_target(os.path.join(dp, n), 'log')
            else:
                sc.lines_target(path, 'log')
        else:
            print('bad target %r' % t, file=sys.stderr)
            return 2
    rep = {'status': 'CLEAN' if not sc.hits else 'LEAK', 'hits': len(sc.hits), 'checked': sc.scanned,
           'advisory': len(sc.advisory), 'targets': a.targets, 'hit_list': sc.hits, 'advisory_list': sc.advisory}
    if a.report:
        json.dump(rep, open(a.report, 'w'), indent=1)
    for h in sc.hits[:a.max_print]:
        print('HIT %s [%s] %s :: %s' % (h['where'], h['kind'], ','.join(h['words']), h['text'][:200]))
    print('ANONSCAN %s hits=%d checked=%d advisory=%d' % (rep['status'], len(sc.hits), sc.scanned, len(sc.advisory)))
    return 0 if not sc.hits else 1


if __name__ == '__main__':
    sys.exit(main())
