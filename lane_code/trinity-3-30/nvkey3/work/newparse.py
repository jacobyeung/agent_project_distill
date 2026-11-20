_JSTR = r'"(?:[^"\\]|\\.)*"'
_JARG = r'(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|/(?:[^/\\\n]|\\.)+/[gimsuy]*)'
_JCALL = (r'\s*\.\s*(?:(?P<m>replaceAll|replace)\s*\(\s*(?P<a>' + _JARG + r')\s*,\s*(?P<b>' + _JARG + r')\s*\)'
          r'|(?P<u>toUpperCase|toLowerCase|trim)\s*\(\s*\)|(?P<bare>replaceAll|replace)\b)')
_JS = re.compile('(' + _JSTR + ')((?:' + _JCALL.replace('?P<m>', '').replace('?P<a>', '').replace('?P<b>', '').replace('?P<u>', '').replace('?P<bare>', '') + ')+)?')
_JS1 = re.compile(_JCALL)
PARSE_STATS = collections.Counter()
def _jsval(a):
    if a[0] == '/':
        j = a.rfind('/'); return ('re', a[1:j], a[j + 1:])
    body = a[1:-1] if a[0] == '"' else a[1:-1].replace("\\'", "'").replace('"', '\\"')
    try: return ('s', json.loads('"' + body + '"', strict=False), '')
    except Exception: return ('s', body, '')
def _jscall(m):
    if not m.group(2): return m.group(0)
    try: s = json.loads(m.group(1), strict=False)
    except Exception: s = m.group(1)[1:-1]
    for c in _JS1.finditer(m.group(2)):
        PARSE_STATS['js_calls'] += 1
        if c.group('u'): s = {'toUpperCase': str.upper, 'toLowerCase': str.lower, 'trim': str.strip}[c.group('u')](s); continue
        if c.group('bare'): PARSE_STATS['js_bare'] += 1; continue
        ka, pa, fa = _jsval(c.group('a')); kb, b, fb = _jsval(c.group('b'))
        if kb != 's': continue
        if ka == 're':
            try: s = re.sub(pa, lambda _m: b, s, count=0 if ('g' in fa or c.group('m') == 'replaceAll') else 1, flags=re.I if 'i' in fa else 0)
            except re.error: pass
        else:
            if s.count(pa) > 1 and c.group('m') == 'replace': PARSE_STATS['js_first_only'] += 1
            s = s.replace(pa, b) if c.group('m') == 'replaceAll' else s.replace(pa, b, 1)
    return json.dumps(s)
def _balance(x):
    out = []; st = []; ins = esc = False
    for ch in x:
        if ins:
            out.append(ch)
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': ins = False
            continue
        if ch == '"': ins = True
        elif ch in '{[': st.append(ch)
        elif ch in '}]':
            want = '{' if ch == '}' else '['
            if want not in st: continue
            while st[-1] != want: out.append('}' if st.pop() == '{' else ']')
            st.pop()
        out.append(ch)
    if ins: out.append('"')
    while st: out.append('}' if st.pop() == '{' else ']')
    return ''.join(out)
def _hoist(d):
    if isinstance(d, dict):
        for key in ('named', 'kinds', 'check', 'inventory'):
            if key in d: continue
            for v in list(d.values()):
                if isinstance(v, dict) and key in v: d[key] = v.pop(key); break
    return d
def parse(t):
    """Reply text -> JSON value or None. Applies the JavaScript string calls the models append inside JSON (.replace("l", "L"), .replace(" ", ""),
    a bare .replace, replaceAll, toUpperCase) with JavaScript semantics (a string pattern replaces its first occurrence), then the comma repairs,
    then a bracket repair that closes unclosed objects and arrays (top-level keys found one level down are moved up only on that repair)."""
    if not t: return None
    t = t.strip(); t = re.sub(r'^```(json)?', '', t).strip(); t = re.sub(r'```$', '', t).strip()
    if '.' in t:
        t2 = _JS.sub(_jscall, t)
        if t2 != t: PARSE_STATS['js_replies'] += 1; t = t2
    fixes = (lambda x: x, lambda x: re.sub(r',\s*([}\]])', r'\1', x), lambda x: re.sub(r'(?<=[}\]"0-9el])\s*\n\s*(?=")', ',\n', re.sub(r',\s*([}\]])', r'\1', x)))
    for cand in (t, t[t.find('{'):t.rfind('}') + 1]):
        for fix in fixes:
            try: return json.loads(fix(cand), strict=False)
            except Exception: pass
    s = t[t.find('{'):] if '{' in t else t
    for fix in fixes:
        try:
            d = json.loads(_balance(fix(s)), strict=False); PARSE_STATS['balanced'] += 1; return _hoist(d)
        except Exception: pass
    try:
        import ast
        return ast.literal_eval(re.sub(r'\btrue\b', 'True', re.sub(r'\bfalse\b', 'False', re.sub(r'\bnull\b', 'None', t[t.find('{'):t.rfind('}') + 1]))))
    except Exception: return None
