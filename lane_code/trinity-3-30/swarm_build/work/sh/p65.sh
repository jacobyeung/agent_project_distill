R=/scratch/jjyeung/orch_n30
python3 - <<'PY'
import re,os,subprocess,glob
src=glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/out/GPU_NEED.json')+glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/configs/*.json')+glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/*.md')+['/scratch/jjyeung/orch_n30/sb_ktow3/out/GPU_NEED.json']+glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/scripts/*.py')+glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/*.py')
paths=set()
for f in src:
    if not os.path.isfile(f): continue
    s=open(f,errors='ignore').read()
    paths|=set(re.findall(r'/scratch/jjyeung/[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+){0,3}',s))
roots=set()
for p in paths:
    parts=p.split('/')
    r='/'.join(parts[:5]) if len(parts)>4 and parts[3] in ('orch_n30','n30_mirror','k1','envs','b01ec87a6f29b','devs1_r2') else '/'.join(parts[:4])
    roots.add(r)
print(len(src),'files',len(paths),'paths',len(roots),'roots')
for r in sorted(roots):
    if os.path.exists(r):
        o=subprocess.run(['timeout','90','du','-sh',r],stdout=subprocess.PIPE,universal_newlines=True).stdout.split('\t')[0]
        print(o, r)
    else: print('ABSENT', r)
PY
echo ====; head -c 3500 $R/sb_ktfix/out/FIX_REPORT.md
