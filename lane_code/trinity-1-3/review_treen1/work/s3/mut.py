import json,shutil,subprocess,sys,os
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work');T=W/'n1c2/pkg/work/tree_r1'
H='student_pilot/r1_handover.py';RT='student_pilot/r1_training.py';E='launch_r1/entry.py'
M={
'M01':('student_pilot/row_text_audit.py',"(printed is None or responses == printed)","(True)"),
'M07':(RT,"thought, re.I)) < 2 or","thought, re.I)) < 0 or"),
'M09':('student_pilot/scene_division_gate.py',"if counts['outside'] or counts['heldout']:","if counts['heldout']:"),
'M12':(RT,"get('max_own_probability') != 0:","get('max_own_probability') not in (0, 0.1):"),
'H2':(H,"or bound.get('config_sha256') != identity or ","or "),
'H6':(H,"if identity != artifact.get('config_sha256') or identity != value.get('donor_config_sha256'):","if identity != value.get('donor_config_sha256'):"),
'X1':(H,"result.update(lm_lr_scale=cfg.get('lm_lr_scale', 1.0),\n                  pose_lr_scale=cfg.get('pose_lr_scale', 1.0))","result.update(pose_lr_scale=cfg.get('pose_lr_scale', 1.0))"),
'X2':(H,"    for key in ('mdg', 'geometry_online'):\n","    for key in ():\n"),
'X3':(RT,"    if value['continuation_identity'] != target['config_identity']:\n","    if False:\n"),
'X4':(RT,"    if value.get('store_hashes') != target['stores']:\n","    if False:\n"),
'X5':(H,"            or complete.get('binding') != bound):","            ):"),
'X6':(H,"complete.get('step') != artifact.get('step')","False"),
'X7':(H,"    return digest(dict(config_sha256=export_identity(cfg), preparation=cfg.get('preparation')))","    return export_identity(cfg)"),
'X8':(E,"        resolved = (path if path.is_absolute() else job_tmp/path).resolve()","        resolved = (path if path.is_absolute() else job_tmp).resolve()"),
'X9':(E,"        if any(job_tmp.iterdir()):\n","        if False:\n"),
'X10':('student_pilot/row_text_audit.py',"        ('runtime_box_status',r'box *unavailable|not *seen|unresolved',authored),","        ('runtime_box_status',r'box unavailable|not seen|unresolved',authored),"),
'X11':('student_pilot/row_text_audit.py',"        return re.sub(r'\\s+', ' ', ''.join(c for c in value if unicodedata.category(c) != 'Cf'))","        return re.sub(r'\\s+', ' ', value)"),
'X12':('launch_r1/build.py',"if sys.version_info < (3,12):raise RuntimeError('Python 3.12 or newer required')\n",""),
'X13':(RT,"stores=target['stores'], row_plan","stores=deepcopy(value['store_hashes']), row_plan"),
}
mods=['tests.test_r2_build9fix','tests.test_r2_build_n1','tests.test_r2_n1fix','tests.test_r2_n1fix2']
for name in sys.argv[1:]:
    f,a,b=M.get(name,('','',''));R=W/'n1c2/mut'/name;d=R/'work/tree_r1'
    if not d.exists():
        shutil.copytree(T,d)
        for x in (W/'n1c2/pkg/work').iterdir():
            if x.name!='tree_r1':(R/'work'/x.name).symlink_to(x)
        for x in ('fixtures','out'):(R/x).symlink_to(W/'n1c2/pkg'/x)
        if name!='CLEAN':
            p=d/f;s=p.read_text();assert s.count(a)==1,(name,s.count(a));p.write_text(s.replace(a,b))
    subprocess.run([str(W/'s3/run.sh'),'n2mut_'+name,str(d),*mods])
    log=(W/'n1c2/suites'/('n2mut_'+name+'.log')).read_text()
    tail=[l for l in log.splitlines() if l.startswith(('Ran ','OK','FAILED','rc='))]
    fails=[l.split(' (')[0]+' ('+l.split(' (')[1][:60] if ' (' in l else l for l in log.splitlines() if l.startswith(('FAIL:','ERROR:'))]
    json.dump(dict(mutant=name,file=f,old=a,new=b,summary=tail,failing=fails[:20]),open(W/'n1c2/mut'/(name+'.json'),'w'),indent=1)
    print(name,tail,fails[:6],flush=True)
