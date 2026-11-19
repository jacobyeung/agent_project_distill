set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apb635a315de01e
test ! -e "$P/a/1.txt"
/usr/bin/python3 -I -s -B /project/community/jjyeung/okh7/a15_cot_apb635a315de01e/a/4.py --parts /project/community/jjyeung/okh7/abc123/e/0 /project/community/jjyeung/okh7/abc123/e/1 /project/community/jjyeung/okh7/abc123/e/2 /project/community/jjyeung/okh7/abc123/e/3 --done /project/community/jjyeung/okh7/abc123/e/done --object q8/8865619b/673bc60f_m200.tar --config /project/community/jjyeung/okh7/abc123/e/config --receipt /project/community/jjyeung/okh7/abc123/e/receipt --data-receipt /project/community/jjyeung/okh7/abc123/e/data_receipt --lineage SFT --step 200 --out /project/community/jjyeung/okh7/a15_cot_apb635a315de01e/a/export.json --prep-tar /project/community/jjyeung/okh7/a15_cot_apb635a315de01e/a/6 --base-inputs /project/community/jjyeung/okh7/a15_cot_apb635a315de01e/a/0.json --inputs-out /project/community/jjyeung/okh7/a15_cot_apb635a315de01e/a/1.json
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B /project/community/jjyeung/okh7/a15_cot_apb635a315de01e/3.py check --gpus 1 --time 04:00:00
/usr/bin/python3 -I -s -B - <<'PYCODE'
import hashlib,json
from pathlib import Path
p=Path('/project/community/jjyeung/okh7/a15_cot_apb635a315de01e')
base=json.loads((p/'a/0.json').read_text());filled=json.loads((p/'a/1.json').read_text())
if len(filled['archives'])!=len(base['archives'])+1 or filled['archives'][1:-1]!=base['archives'][1:]:
 raise ValueError('Fill changed base archive')
if filled['archives'][-1]['sha256']!=hashlib.sha256((p/'a/6').read_bytes()).hexdigest():
 raise ValueError('Preparation archive differs')
(p/'a/1.txt').write_text('0\n')

PYCODE
