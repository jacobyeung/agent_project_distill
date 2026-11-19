W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; B=$W/w21/work/build21
python3 -c "
import json;d=json.load(open('$B/UPLOADS.json'));print(d['total_bytes'],len(d['files']));print(json.dumps(d['files'][:2],indent=0)[:800]);import collections;print(collections.Counter(f.get('source','').split('/')[0:3].__str__() for f in d['files']).most_common(5))"
wc -l $B/upload.py; cat $B/upload.py | head -60
tail -2 $W/work/conf21c/focused_untar2.log; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21d | head -1); stat -c %s $d/transcript.log
