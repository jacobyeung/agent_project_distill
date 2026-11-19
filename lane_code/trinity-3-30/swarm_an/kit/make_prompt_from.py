"""Compose a Codex analyst prompt from an existing one (lane swarm_an).
usage: make_prompt_from.py <template stem, e.g. m200_deep2_gapbands> <new stem, e.g. m200_doubt_dist> <assignment file>
Keeps the template's head (rules, context) and tail (how to read the traces, required report) and replaces the block
from '## Your assignment' up to '## How to read the traces' with the assignment file; the analyst id in the text follows the stem."""
import io, sys
P = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_an/prompts/'
tpl, new, assign = sys.argv[1], sys.argv[2], sys.argv[3]
s = io.open(P + tpl + '.md', encoding='utf-8').read()
a = s.index('## Your assignment'); b = s.index('## How to read the traces')
t = s[:a] + io.open(assign, encoding='utf-8').read().rstrip('\n') + u'\n\n' + s[b:]
assert 'san_' + tpl in t
t = t.replace('san_' + tpl, 'san_' + new)
io.open(P + new + '.md', 'w', encoding='utf-8').write(t)
print(P + new + '.md', len(t), 'chars')
