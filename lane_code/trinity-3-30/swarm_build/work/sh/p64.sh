R=/scratch/jjyeung/orch_n30
date -u +%TZ; head -c 400 $R/sb_ktfix/STATUS.md; echo
python3 - <<'PY'
import re,os,subprocess,glob
src=[f for f in glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/out/GPU_NEED.json')+glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/configs/*.json')+glob.glob('/scratch/jjyeung/orch_n30/sb_ktfix/*.md') if os.path.isfile(f)]
paths=set()
for f in src:
    try: s=open(f).read()
    except: continue
    paths|=set(re.findall(r'/scratch/jjyeung/[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+){0,2}',s))
roots=set()
for p in paths:
    parts=p.split('/')
    r='/'.join(parts[:5]) if parts[3] in ('orch_n30','n30_mirror','k1','envs') else '/'.join(parts[:4])
    roots.add(r)
print(len(src),'files',len(paths),'paths',len(roots),'roots')
for r in sorted(roots):
    if os.path.exists(r):
        o=subprocess.run(['timeout','60','du','-sh',r],capture_output=True,text=True).stdout.split('\t')[0]
        print(o, r)
    else: print('ABSENT', r)
PY
