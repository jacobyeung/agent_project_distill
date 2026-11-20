cd /scratch/jjyeung/orch_n30/sb_own400 && tail -3 out/fov544_score.log; ls out/fov544_score; F=/scratch/jjyeung/orch_n30/fb_pack/fov/crev/REVIEW_VERDICT.md; sha256sum $F | cut -c1-16; grep -n -A4 "SHOULD\|Note\|NOTE" $F | cut -c1-450 | head -30
[ -f out/fov544_score/FOV_RESULT.json ] && sha256sum out/fov544_score/*.json | cut -c1-16,65- && /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json
d=json.load(open('out/fov544_score/FOV_RESULT.json'))
print('keys',list(d))
for k in ('status','choice','criteria','synthetic'):
  if k in d: print(k, json.dumps(d[k])[:1500])
P
