import json, sys
from pathlib import Path
for f in sys.argv[1:]:
    r = json.loads(Path(f).read_text())
    rt = r.get('routing') if isinstance(r.get('routing'), dict) else {}
    s1 = r.get('s1_source')
    print(f, '| qid', r.get('qid'), '| routing.qid', rt.get('qid'), '| type', r.get('question_type', r.get('type')), rt.get('question_type'),
          '| s1_source', (s1 or {}).get('name') if isinstance(s1, dict) else s1, '| r1_source', r.get('r1_source'),
          '| routing.s1', 's1_source' in rt, '| prov keys', sorted((r.get('provenance') or {}).keys())[:6], '| answer_form', r.get('answer_form'), '| not_seen', r.get('not_seen'))
