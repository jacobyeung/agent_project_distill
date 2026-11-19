set -euo pipefail
D=/project/community/jjyeung/okh7/a15_cot_ap7e4d49a0f823; P=/project/community/jjyeung/okh7/a15_cot_apfadf2291c654b; cd $D
tail -3 $P/a/0.log; test "$(cat "$P/a/1.txt")" = 0
/usr/bin/python3 -I -s -B - "$P" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
for name in ('dryres.json', 'drypackage.json', '10.json'):
    assert json.loads((p/'a/e'/name).read_text())['passed'] is True
print('fill receipts passed')
PY
bash o_cpucheck.sh; sleep 5; cat $P/a/4.txt; TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T %M %N %R"
