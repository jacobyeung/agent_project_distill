import json,shutil,subprocess,sys,os
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');T=W/'n1c/pkg/work/tree_r1'
M={
'M01':('student_pilot/row_text_audit.py',"(printed is None or responses == printed)","(True)"),
'M07':('student_pilot/r1_training.py',"thought, re.I)) < 2 or","thought, re.I)) < 0 or"),
'M09':('student_pilot/scene_division_gate.py',"if counts['outside'] or counts['heldout']:","if counts['heldout']:"),
'M12':('student_pilot/r1_training.py',"get('max_own_probability') != 0:","get('max_own_probability') not in (0, 0.1):"),
'H1':('student_pilot/r1_handover.py',"    if dict(positions) != expected['sampler_positions']:\n","    if False:\n"),
'H2':('student_pilot/r1_handover.py',"or bound.get('config_sha256') != identity or ","or "),
'H3':('student_pilot/r1_handover.py',"('steps', 'warmup_ratio', 'learning_rate',","('steps', 'learning_rate',"),
'H4':('student_pilot/r1_handover.py',"if mapping != dict(schema='r1-handover-map-v1', artifact_sha256=cfg['init_artifact']['artifact']['sha256'],\n                           step=expected['step'], source=actual, target=target):","if mapping.get('schema') != 'r1-handover-map-v1':"),
'H5':('student_pilot/r1_handover.py',"source.get('r1_training') or plan['offset']","source.get('r1_training')"),
'H6':('student_pilot/r1_handover.py',"if identity != artifact.get('config_sha256') or identity != value.get('donor_config_sha256'):","if identity != value.get('donor_config_sha256'):"),
'H7':('student_pilot/r1_handover.py',"if (len(rows) != counts[name] or len(set(rows)) != len(rows)","if (len(set(rows)) != len(rows)"),
'T1':('student_pilot/row_text_audit.py',r"box[\s\u200b-\u200d\u2060\ufeff]+unavailable|not[\s\u200b-\u200d\u2060\ufeff]+seen",r"box[\s\u200b-\u200d\u2060]+unavailable|not[\s\u200b-\u200d\u2060]+seen"),
'R4':('student_pilot/carrier_c1_run.py',"        if self.b7_inputs or getattr(self, 'r1_training', False):","        if self.b7_inputs:"),
'J1':('launch_r1/entry.py',"    elif job_tmp.exists():\n        raise ValueError('R1_HOST_JOB_TMP_NOT_FRESH')","    elif False:\n        raise ValueError('R1_HOST_JOB_TMP_NOT_FRESH')"),
'J2':('launch_r1/entry.py',"        if '..' in path.parts or (path.is_absolute() and not path.resolve().is_relative_to(job_tmp)):","        if '..' in path.parts:"),
}
mods=['tests.test_r2_build9fix','tests.test_r2_build_n1','tests.test_r2_n1fix']
for name in sys.argv[1:]:
    f,a,b=M[name];R=W/'n1c/mut'/name;d=R/'work/tree_r1'
    if not d.exists():
        shutil.copytree(T,d)
        for x in (W/'n1c/pkg/work').iterdir():
            if x.name!='tree_r1':(R/'work'/x.name).symlink_to(x)
        for x in ('fixtures','out'):(R/x).symlink_to(W/'n1c/pkg'/x)
        p=d/f;s=p.read_text();assert s.count(a)==1,(name,s.count(a));p.write_text(s.replace(a,b))
    subprocess.run([str(W/'s2/run.sh'),'mutc_'+name,str(d),*mods])
    log=(W/'n1c/suites'/('mutc_'+name+'.log')).read_text()
    tail=[l for l in log.splitlines() if l.startswith(('Ran ','OK','FAILED','rc='))]
    fails=[l.split(' (')[0] for l in log.splitlines() if l.startswith(('FAIL:','ERROR:'))]
    json.dump(dict(mutant=name,file=f,old=a,new=b,summary=tail,failing=fails[:20]),open(W/'n1c/mut'/(name+'_c.json'),'w'),indent=1)
    print(name,tail,fails,flush=True)
