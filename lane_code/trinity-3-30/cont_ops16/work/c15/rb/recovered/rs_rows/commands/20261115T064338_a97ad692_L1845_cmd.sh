<!-- recovered by seal_plan: transcript=a97ad692 line=1845 utc=2026-11-15T06:43:38.239Z kind=commands original_path=(bash command)  -->
F=/scratch/jjyeung/orch_cd/rs_rows/out/SAMPLES_R2.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$F" <<'PY'
import sys,re
t=open(sys.argv[1]).read()
fams=re.split(r'\n## ',t)[1:]
want={'facing':2,'object_rel_direction_medium':1,'object_rel_distance':1,'object_size_estimation':1,'route_planning':1,'recovery':1,'box_3d':1,'object_counting':1,'obj_appearance_order':1,'units':1,'totals':1}
for f in fams:
    name=f.split('\n',1)[0].strip()
    if name not in want: continue
    rows=re.split(r'\n### ',f)[1:]
    for r in rows[:want[name]]:
        lines=r.split('\n')
        rid=lines[0][:40]
        body='\n'.join(lines[1:])
        q=[l for l in lines[1:] if l.strip() and not l.startswith('```')][:1]
        m=re.search(r'<think>.*?</think>\s*\n*(.*?)\n```',body,re.S)
        print('#### %s | %s'%(name,rid)); print('Q:',(q[0] if q else '')[:260])
        if m:
            th=re.search(r'<think>(.*?)</think>',body,re.S).group(1).strip()
            print(th[:1100]); print('ANS:',m.group(1).strip()[:160])
        else:
            print(body[:900])
        print()
PY