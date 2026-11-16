<!-- recovered by seal_plan: transcript=a97ad692 line=3179 utc=2026-11-15T09:24:56.910Z kind=commands original_path=(bash command)  -->
df -BG --output=avail /scratch | tail -1; date -u +%H:%M:%SZ; cd /scratch/jjyeung/orch_cd && du -sm evalx/work/milestone/native_package_s24_07 evalx/builds rs_rows rs_tree official544 k1_ops k1_build dense_plan tree_review3 codex_local 2>/dev/null | sort -rn | head -10; du -sm /scratch/jjyeung/k1_buf 2>/dev/null; echo "== my procs by write rate (5 s)"; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import os,time
uid=os.getuid()
def snap():
    d={}
    for p in os.listdir('/proc'):
        if not p.isdigit(): continue
        try:
            if os.stat('/proc/'+p).st_uid!=uid: continue
            d[p]=int([l for l in open('/proc/%s/io'%p) if l.startswith('write_bytes')][0].split()[1])
        except Exception: pass
    return d
a=snap(); time.sleep(5); b=snap()
for mb,p in sorted(((b[p]-a.get(p,b[p]))/5/1e6,p) for p in b)[-5:][::-1]:
    try: cmd=open('/proc/%s/cmdline'%p).read().replace('\0',' ')[:130]
    except Exception: cmd='?'
    print('%.1f MB/s pid %s %s'%(mb,p,cmd))
PY
echo "== other users recent"; ls -lt --time-style=+%H:%M /scratch | sed -n '2,5p' | cut -c1-90; for u in npalghat lnayak; do ls -lt --time-style=+%m-%dT%H:%M /scratch/$u 2>/dev/null | sed -n '2,3p' | cut -c1-100; done