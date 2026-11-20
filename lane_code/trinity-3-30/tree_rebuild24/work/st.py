import sys,re
p='/scratch/jjyeung/orch_n30/tree_rebuild24/STATUS.md'; s=open(p).read().split('\n')
upd, new = sys.argv[1], sys.argv[2:]
s[1]='Updated: '+upd
i=[k for k,l in enumerate(s) if l.startswith('## Running')][0]
s[i]='## Running ('+upd.split()[0][11:16]+'Z) — NEWEST FIRST'
s[i+1:i+1]=new
open(p,'w').write('\n'.join(s))
