#!/.orchkit_real/python -IS
"""Stands in for a system interpreter inside the dry-run sandbox, so children started with -I are traced.

dryrun.py bakes REAL and TRACE_PY, rewrites the first line to the real interpreter's bound path,
and binds this file over the interpreter path the kit names (for example /usr/bin/python3.6). The
kernel then runs `REAL -IS pywrap.py <the kit's own arguments>`; this file re-executes REAL with the
kit's own flags and the tracer in front of the kit's script. Standard library only; Python 3.6-safe.
"""
import os
import sys

REAL = ''  # baked by dryrun.py
TRACE_PY = ''  # baked by dryrun.py

args = sys.argv[1:]
flags = []
i = 0
while i < len(args):
    a = args[i]
    if a in ('-c', '-m') or not a.startswith('-') or a == '-' or a.startswith('--'):
        break
    if a in ('-W', '-X'):
        flags.extend(args[i:i + 2])
        i += 2
        continue
    flags.append(a)
    i += 1
rest = args[i:]
if rest and rest[0] != '-' and not rest[0].startswith('--') and not any(
        ('c' in f[1:] or 'm' in f[1:]) for f in flags):
    os.execv(REAL, [REAL] + flags + [TRACE_PY, '--'] + rest)
os.execv(REAL, [REAL] + args)
