import json,shutil,subprocess,sys,os
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');T=W/'pkg/work/tree_r1'
M={
'M01':('student_pilot/row_text_audit.py',"(printed is None or responses == printed)","(True)"),
'M02':('student_pilot/row_text_audit.py',"event.get('text') != response or ",""),
'M03':('student_pilot/row_text_audit.py',r"r'box\s+unavailable|not\s+seen|unresolved'",r"r'box unavailable|not seen|unresolved'"),
'M04':('student_pilot/extent_receipt.py',"any(s != 'full' for s in statuses)","any(s == 'half' for s in statuses)"),
'M05':('student_pilot/extent_receipt.py',"if entry.get('repair_sha256') != (digest(repair) if repair else None):","if False:"),
'M06':('student_pilot/extent_receipt.py',"kind in ('object_abs_distance', ","kind in ("),
'M07':('student_pilot/r1_training.py',"thought, re.I)) < 2 or","thought, re.I)) < 0 or"),
'M08':('student_pilot/r1_training.py',"if any(progress.get(k) != v for k, v in expected.items()):","if progress.get('step') != expected['step']:"),
'M09':('student_pilot/scene_division_gate.py',"if counts['outside'] or counts['heldout']:","if counts['heldout']:"),
'M10':('student_pilot/r1_mix.py',"min(n, 4*counts[k])","min(n, 5*counts[k])"),
'M11':('student_pilot/carrier_c1_run.py',"        check(value, stream)\n","        pass\n"),
'MG':('student_pilot/row_text_audit.py',"r'<tool_response>[^<]*</tool_response>'","r'<tool_response>[\\s\\S]*</tool_response>'"),
'M12':('student_pilot/r1_training.py',"get('max_own_probability') != 0:","get('max_own_probability') not in (0, 0.1):"),
}
mods=sys.argv[2:];name=sys.argv[1];f,a,b=M[name]
R=W/'mut2'/name;d=R/'work/tree_r1'
if not d.exists():
    shutil.copytree(T,d)
    for x in (W/'pkg/work').iterdir():
        if x.name!='tree_r1':(R/'work'/x.name).symlink_to(x)
    for x in ('fixtures','out'):(R/x).symlink_to(W/'pkg'/x)
p=d/f;s=p.read_text();assert s.count(a)==1,(name,s.count(a));p.write_text(s.replace(a,b))
subprocess.run([str(W/'suites/run.sh'),'mut_'+name,str(d),*mods])
log=(W/'suites'/('mut_'+name+'.log')).read_text()
tail=[l for l in log.splitlines() if l.startswith(('Ran ','OK','FAILED','rc='))]
fails=[l.split(' (')[0] for l in log.splitlines() if l.startswith(('FAIL:','ERROR:'))]
json.dump(dict(mutant=name,file=f,old=a,new=b,summary=tail,failing=fails[:20]),open(W/'mut'/(name+'.json'),'w'),indent=1)
print(name,tail,len(fails))
