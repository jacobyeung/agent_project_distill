"""Report the literal name-policy boundary without certifying unseen runtime archives."""
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
PATTERN=re.compile(r'scannet|r0|vsi|revsi|distill|split|sft|h1',re.I)

def audit():
    extra=json.loads((ROOT/'kit/launcher/EXTRA.json').read_text())
    surfaces=[v['path'] for v in extra['files'].values()]+list(extra['frames'])
    new_hits=[s for s in surfaces if PATTERN.search(s)]
    inherited=[]
    for family in ('main','away','forward'):
        path=ROOT/'readk/kit/build/a4cadd8934b/fetched/x'/family/'a0/results/budget_2048/0/items_a0.jsonl'
        for line in path.read_text().splitlines():
            row=json.loads(line);value=row.get('video_path','')
            if PATTERN.search(value):
                inherited.append(dict(family=family,field='video_path',example=value))
                break
    result=dict(new_asset_names_clean=not new_hits,new_hits=new_hits,
        literal_policy_satisfied=False,inherited_virtual_path_examples=inherited,
        runtime_archive_member_inventory='not supplied locally; live archive names not certified',
        note='Virtual paths occur inside accepted item content. The accepted binder bytes are preserved. This audit does not grant an exception to the literal path rule.')
    (ROOT/'evidence/NAME_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
if __name__=='__main__':print(json.dumps(audit()))
