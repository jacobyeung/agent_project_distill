"""Deep-report digest: sections 1 (answers), 3 (changes), 4 (refuted), 5 (not established). usage: digest2.py <file> [width] [maxlines]"""
import sys, re
t = open(sys.argv[1]).read().splitlines(); w = int(sys.argv[2]) if len(sys.argv) > 2 else 380; mx = int(sys.argv[3]) if len(sys.argv) > 3 else 70
sec = 0; n = 0
for l in t:
    m = re.match(r'\s*(?:#+\s*|\*\*)\s*(\d)[.)]?\s', l)
    if m: sec = int(m.group(1))
    if re.search(r'(?i)^\W*(appendix|classifier)', l): break
    if sec in (1, 3, 4, 5) and l.strip():
        print(l[:w]); n += 1
        if n >= mx: print('[cut]'); break
