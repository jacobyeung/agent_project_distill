"""n_ops10 patch 3 of nauto.py: the stop-object check runs only for a job that reached training (a parse line of its own with a step), so a refusal before training raises no STOP_NOT_UPLOADED. Usage: python3 patch_nauto3.py SRC DST"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
old1 = "el = g('elapsed') or ''\n"
new1 = "el = g('elapsed') or ''\nif job.isdigit() and (g('step') or '').isdigit(): J['stepped'] = True  # n_ops10: the job reached training\n"
old2 = "    if J.get('gpu4') and not J.get('stopcheck') and now - J['ended'] >= 600:"
new2 = "    if J.get('gpu4') and J.get('stepped') and not J.get('stopcheck') and now - J['ended'] >= 600:"
for o, n in ((old1, new1), (old2, new2)):
    assert s.count(o) == 1, o
    s = s.replace(o, n)
open(dst, 'x').write(s)
print('patched', dst)
