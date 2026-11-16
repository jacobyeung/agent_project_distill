<!-- recovered by seal_plan: transcript=71f94277 line=12650 utc=2026-11-12T12:53:37.271Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - "$M" <<'EOF'
import sys, os
m = sys.argv[1]
p = m + '/aws-pull-under-100gb-approved.md'
t = open(p).read()
a = t.index('The per-user IO cap is 15 MB/s')
b = t.index('**Evacuate AWS continuously')
new = ('Rates on Trinity (USER 2026-11-12, relayed in the main queue line 159): one internet download may run at 20 MB/s and other copies at 10 MB/s, inside the admins\' hard limit of 20 MB/s per user summed over every node. It is one budget for the whole user: main has priority, so when main runs a 20 MB/s download, distillation pauses every head-node and NFS stream until main writes that it has ended. Writes to /home and /data* count double.\n\n')
t = t[:a] + new + t[b:]
d0 = t.index('description: ')
d1 = t.index('\n', d0)
t = t[:d0] + 'description: "USER 2026-11-12: Trinity downloads may run at 20 MB/s and other copies at 10 MB/s inside the 20 MB/s per-user limit; main has priority (pause ours while main downloads); AWS pulls under 200 GB and downloads under ~100 GB need no ask"' + t[d1:]
open(p + '.next', 'w').write(t); os.replace(p + '.next', p)
q = m + '/MEMORY.md'
L = open(q).read().split('\n')
for i, l in enumerate(L):
    if 'aws-pull-under-100gb-approved.md' in l:
        L[i] = '- **USER 11-12:** [IO rates + pulls](aws-pull-under-100gb-approved.md) download 20 MB/s, other copies 10 MB/s; pause ours while main downloads; AWS pulls <200 GB, downloads <100 GB need no ask'
open(q + '.next', 'w').write('\n'.join(L)); os.replace(q + '.next', q)
print('ok')
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: queue watcher fired: main queue line 159, USER 2026-11-12: Trinity downloads at 20 MB/s, other copies at 10 MB/s; memory aws-pull-under-100gb-approved.md rewritten to the current rates; watcher re-armed." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md