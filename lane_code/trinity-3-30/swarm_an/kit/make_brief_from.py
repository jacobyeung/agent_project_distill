"""Compose a Devin deep-read brief from an existing one (lane swarm_an).
usage: make_brief_from.py <template lane, e.g. san_dd_dirtw> <new lane> <assignment file> [minutes]
Keeps the template's head (rules, context) and tail (how to read the traces, deliverable), swaps the lane name
and replaces the block from '## Your assignment' up to '## How to read the traces' with the assignment file."""
import io, sys
L = '/scratch/jjyeung/orch_n30/swarm_an/'
tpl, new, assign = sys.argv[1], sys.argv[2], sys.argv[3]
minutes = sys.argv[4] if len(sys.argv) > 4 else '75'
s = io.open(L + 'briefs/%s.md' % tpl, encoding='utf-8').read()
a = s.index('## Your assignment'); b = s.index('## How to read the traces')
body = io.open(assign, encoding='utf-8').read()
t = s[:a] + body.rstrip('\n') + u'\n\n' + s[b:]
assert t.count(tpl) >= 4
t = t.replace(tpl, new)
old = 'finish within 75 minutes of your start'
assert old in t
t = t.replace(old, 'finish within %s minutes of your start' % minutes)
out = L + 'briefs/%s.md' % new
io.open(out, 'w', encoding='utf-8').write(t)
print(out, len(t), 'chars;', t.count(new), 'mentions of the lane')
