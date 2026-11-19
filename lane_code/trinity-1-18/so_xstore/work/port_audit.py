"""Rebase source-line citations once, using the supplied source snapshots."""
from pathlib import Path
import difflib
import re

L = Path(__file__).resolve().parent.parent
path = L / 'out/INPUT_AUDIT.md'
text = path.read_text()
assert "relative to build 20's" in text
maps = {}

def line_at(name, number):
    old = L / 'work/tree_build20' / name
    new = L / 'in/tree21b/work/tree_r1' / name
    if not old.is_file() or not new.is_file():
        return number
    if name not in maps:
        a, b = old.read_text().splitlines(), new.read_text().splitlines()
        mapping = {}
        for tag, i, j, k, m in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
            for n in range(i, j):
                mapping[n + 1] = k + min(n - i, max(0, m - k - 1)) + 1
        maps[name] = mapping
    return maps[name][number]

output = []
for line in text.splitlines(True):
    current = ['']
    def replace(match):
        name, number = match.group(1), int(match.group(2))
        if name:
            current[0] = name
        name = current[0]
        return '`' + (match.group(1) or '') + ':' + str(line_at(name, number)) + '`'
    output.append(re.sub(r'`((?:student_pilot|launch_s1|launch_r2|trace_format)/[A-Za-z0-9_./]+)?:(\d+)`', replace, line))
text = ''.join(output)
text = text.replace("relative to build 20's `work/tree_r1`, supplied at `/scratch/jjyeung/orch_n30/so_launch/in/tree`. Build 21b was absent at task start.",
                    "relative to build 21b's `work/tree_r1`, supplied at `/scratch/jjyeung/orch_n30/so_xstore/in/tree21b`. Its source seal is `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`.")
text = text.replace("The build-20 report also records missing real receipts (`out/BUILD20_REPORT.md:25` in the supplied input package).",
                    "The supplied build report lists absent payload dependencies (`out/BUILD21_REPORT.md:63` in the input package); its receipt-reader and CPU-proof results do not constitute an execution trace of this lane's proposed store.")
path.write_text(text)
