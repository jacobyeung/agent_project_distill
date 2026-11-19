"""Print a report without its examples section and appendix. usage: digest.py <final_message.md> [width]"""
import sys, re
t = open(sys.argv[1]).read().splitlines(); w = int(sys.argv[2]) if len(sys.argv) > 2 else 700
skip = False
for l in t:
    if re.match(r"\s*(#+\s*|\*\*)3[.)]?\s", l) and re.search(r"(?i)example", l): skip = True; print('[examples section omitted]'); continue
    if skip and re.match(r'\s*(#+\s*|\*\*)?4[.)]?\s', l): skip = False
    if re.search(r'(?i)^\W*(appendix|classifier)', l): print('[appendix omitted]'); break
    if not skip and l.strip(): print(l[:w])
