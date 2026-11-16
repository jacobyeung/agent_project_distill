cd /scratch/jjyeung/orch_n30
python3 - <<'PY'
import json
m=json.load(open('b05_owngrd/work/manifests/TEACHER_K1.json'))
r0=json.load(open('b10_reserve/out/R0_SCENES.json'))
print(json.dumps(dict(teacher_k1=dict(sha256='4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9',
  captures=[dict(canonical=c['canonical'],room=c['room'],aliases=c['aliases'],k1_split=c['k1_split']) for c in m['captures']],
  missing_gt=m['missing_gt'], refused=sorted(m['refused'])), r0_scenes=r0)))
PY
