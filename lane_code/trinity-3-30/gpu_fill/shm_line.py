import sys,re
# summarise one read_shm.sh output: card use and distillation /dev/shm total on the node
OLD={'g13','sc_moving600_1113','spatialclaw_envfix_1112','timed_fanout_1112','run_trace_archive_metadata'}
t=open(sys.argv[1]).read().splitlines()
host=next((l for l in t if l.startswith('HOST')),'HOST ? UTC ?').split()
cards=[l.split(', ') for l in t if re.match(r'^\d+, NVIDIA',l)]
busy=[c[0]+':'+c[2].replace(' MiB','M')+'/'+c[4].replace(' ','') for c in cards if int(c[2].split()[0])>500]
free=[c[0] for c in cards if int(c[2].split()[0])<=500]
def gb(s):
    v=float(s[:-1]); return {'K':v/1e6,'M':v/1e3,'G':v,'T':v*1e3}.get(s[-1],v)
mine={};old=0.0
on=False
for l in t:
    if l=='JJSHM': on=True; continue
    if on and '\t' in l:
        sz,p=l.split('\t'); n=p.rsplit('/',1)[-1]
        if n in OLD: old+=gb(sz)
        else: mine[n]=gb(sz)
shm=next((l.split() for l in t if l.startswith('tmpfs')),None)
print(f"Reading {host[1]} {host[3]} (ssh, each tick): busy cards {' '.join(busy) or 'none'}; empty {free}. Distillation /dev/shm/jjyeung = {sum(mine.values()):.1f} GB of 85 cap ("+', '.join(f'{k} {v:.1f}' for k,v in sorted(mine.items()))+f"); older dirs {old:.0f} GB not counted; /dev/shm used {shm[2] if shm else '?'} of {shm[1] if shm else '?'}.")
