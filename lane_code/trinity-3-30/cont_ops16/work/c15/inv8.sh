set -u
cd /project/community/jjyeung/distill/okit/in || exit 1
ls -la e00
sz=$(stat -c %s e00)
if [ "$sz" -lt 2000000000 ]; then
  echo "members: $(tar tf e00 | wc -l)"
  tar tf e00 | grep -E 'e84d901c/z/|4c230a7e' | head -20
  for m in $(tar tf e00 | grep -E '4c230a7e\.json$' | head -3); do echo "$m $(tar xOf e00 "$m" | sha256sum | cut -c1-64)"; done
fi
/usr/bin/python3 -I - <<'PY'
import json
r=json.load(open('/project/community/jjyeung/distill/okit/in/cr/524b14f9f180.p00'))
print('sealed vqa receipt keys', sorted(r)); print('division', r.get('division')); print('database', r.get('database')); print('source', str(r.get('source'))[:300])
PY
df -h /project/community | tail -1
TZ=UTC squeue -u jjyeung -o '%i %j %P %T %M %l %R' | head -20
ls -la /project/community/jjyeung/okh7/ | tail -15
ls -la /project/community/jjyeung/okh7/x_07ca49df/runs/469ddece/ | head -30
