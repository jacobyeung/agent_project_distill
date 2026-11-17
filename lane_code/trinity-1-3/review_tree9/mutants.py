import json,shutil,subprocess,os,sys
from pathlib import Path
R=Path('/scratch/jjyeung/orch_n30/review_tree9');T=R/'pkg/work/tree_r1'
M=[
 ('M01','student_pilot/row_text_audit.py',"r'box unavailable|not seen|unresolved'","r'box unavailable|not seen'"),
 ('M02','student_pilot/row_text_audit.py',"r'<tool_response>[^<]*</tool_response>'","r'<tool_response>[\\s\\S]*</tool_response>'"),
 ('M03','student_pilot/row_text_audit.py',"authored if key == 'runtime_box_status' else text","authored"),
 ('M04','student_pilot/row_text_audit.py',"re.search(pattern,authored if key","re.search(pattern,text if key"),
 ('M05','student_pilot/row_text_audit.py',"re.sub(r'<tool_response>[^<]*</tool_response>', '', str(row.get(k,'')))\n                       for k in ('target','suffix','response','trace'))","str(row.get(k,'')) for k in ('target','suffix','response','trace'));authored=re.sub(r'<tool_response>[^<]*</tool_response>','',authored)"),
 ('M06','student_pilot/routing_requirements.py',"if rates['recovery'] <= 0 or","if rates['recovery'] < 0 or"),
 ('M07','student_pilot/routing_requirements.py',"type(recovery) is not int or recovery <= 0","not isinstance(recovery, int) or recovery <= 0"),
 ('M08','student_pilot/routing_requirements.py',"or any(type(units.get(u)) is not int or units[u] <= 0 for u in UNITS)","or all(type(units.get(u)) is not int or units[u] <= 0 for u in UNITS)"),
 ('M09','student_pilot/b7_inputs.py',"    result.extend(row_blockers(table(), value.get('routing_training_counts')))\n",""),
 ('M10','launch_r2/build.py',"        cfg['b7_blockers'] = sorted(set(cfg['b7_blockers'] + row_blockers(\n            load(output/mix['path']), launch_inputs.get('routing_training_counts'))))","        pass"),
 ('M11','generator/derivgen_v7/derivgen/materialize.py',"                answer = '<answer>' + str(answer) + '</answer>'\n","                pass\n"),
 ('M12','generator/derivgen_v7/derivgen/materialize.py',"_require(old_answer == row['answer'] and old_result == e['result'], 'gt_decision_mismatch')","_require(old_answer == row['answer'], 'gt_decision_mismatch')"),
 ('M13','student_pilot/h1_faithful.py',"    own, gt = (re.fullmatch","    _own, _gt = (re.fullmatch"),
]
TESTS=['tests.test_r2_build9_recovery','tests.test_r2_build9_identity','tests.test_r2_build9_requirements','tests.test_r2_build9_cpu','tests.test_r2_build8','tests.test_r2_build7']
sel=sys.argv[1:] or [m[0] for m in M]
res={}
for mid,f,old,new in M:
    if mid not in sel:continue
    d=R/'mut'/mid
    if d.exists():shutil.move(str(d),str(R/'mut'/(mid+'.old'+str(os.getpid()))))
    shutil.copytree(T,d)
    src=(d/f).read_text();assert src.count(old)==1,(mid,src.count(old));(d/f).write_text(src.replace(old,new))
    env={**os.environ,'PYTHONPATH':str(d)+':'+str(d/'generator/derivgen_v7'),'R2_PROOFS':str(R/'proofs/mut'/mid)}
    (R/'proofs/mut'/mid).mkdir(parents=True,exist_ok=True)
    out={}
    for t in TESTS:
        p=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-s','-B','-m','unittest',t],cwd=d,env=env,capture_output=True,text=True,timeout=900)
        tail=p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ''
        fails=[l for l in p.stderr.splitlines() if l.startswith(('FAIL:','ERROR:'))]
        out[t]=dict(rc=p.returncode,summary=tail,fails=fails[:6])
    res[mid]=dict(file=f,old=old[:120],new=new[:120],caught=any(v['rc'] for v in out.values()),tests=out)
    print(mid,'CAUGHT' if res[mid]['caught'] else 'SURVIVED',{t.split('.')[-1]:v['summary'] for t,v in out.items()},flush=True)
    json.dump(res,open(R/('proofs/MUTANTS_%s.json'%('_'.join(sel) if sys.argv[1:] else 'all')),'w'),indent=1)
