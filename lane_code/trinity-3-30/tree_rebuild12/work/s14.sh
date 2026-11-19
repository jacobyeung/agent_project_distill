W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; B=$W/w21/work/build21; R=$W/w21/out/BUILD21_REPORT.md
python3 -c "
import json;d=json.load(open('$B/FINAL_KITS.json'));print(json.dumps({k:(v if len(json.dumps(v))<400 else str(v)[:400]) for k,v in d.items()},indent=1)[:3000])"
python3 -c "
import json;d=json.load(open('$B/UPLOADS.json'));print(list(d.keys()));fs=d['files'];print(len(fs));
import collections;print(sorted(((f.get('bytes',f.get('size',0)),f.get('path',f.get('name'))) for f in fs),reverse=True)[:8] if isinstance(fs,list) else list(fs.items())[:5])" 2>&1 | cut -c1-1500
wc -l $B/OPERATOR.md; head -c 4000 $B/OPERATOR.md
echo; sed -n '66,80p' $R | cut -c1-300; grep -c . $R
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_rev21 | head -1); stat -c '%s %y' $d/transcript.log; ls $d
