import re, os
p = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/STATUS.md'
lane = '/scratch/jjyeung/orch_n30/tree_rebuild30/STATUS.md'
W = '/scratch/jjyeung/orch_n30/tree_rebuild30/work/'
top = open(W + 'st_top.md').read().rstrip('\n') + '\n'
nxt = open(W + 'st_next.md').read().rstrip('\n') + '\n'
s = open(p).read()
s = re.sub(r'<!-- tr30 top -->.*?<!-- /tr30 top -->\n', '', s, flags=re.S)
i = s.index('## Running (')
j = s.index('\n', i) + 1
s = s[:j] + '<!-- tr30 top -->\n' + top + '<!-- /tr30 top -->\n' + s[j:]
k = s.index('## Next (in order;')
s = s[:k] + nxt
s = re.sub(r'^# tree_rebuild STATUS.*$', '# tree_rebuild STATUS (successor resumes from this file alone; lane tree_rebuild30 on trinity-3-30)', s, count=1, flags=re.M)
open(p + '.tmp', 'w').write(s)
os.replace(p + '.tmp', p)
open(lane, 'w').write(s)
print(len(s))
