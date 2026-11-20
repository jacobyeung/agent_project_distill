X=/project/community/jjyeung/okh7/x_22c714e1; f=$(ls $X/u | grep ^5db993b1); ls -la $X/u/$f; sha256sum $X/u/$f; head -c 3000 $X/u/$f; echo
python3 -I -s -B - <<PY
import json
v=json.load(open('$X/u/$f'))
print(type(v).__name__, list(v)[:20] if isinstance(v,dict) else len(v))
PY
