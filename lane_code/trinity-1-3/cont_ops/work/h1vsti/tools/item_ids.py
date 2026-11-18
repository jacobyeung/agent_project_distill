"""Decode item identities on Trinity; never package this module or its map."""
import json
from pathlib import Path
import re

MAP_PATH=Path(__file__).resolve().parents[1]/'evidence/ID_MAP.json'


def load_map():
    return json.loads(MAP_PATH.read_text())


def logical_item(row,mapping):
    if row.get('family') not in ('a7','r0dev'):
        return row
    opaque_id=row['id']
    source=mapping.get(opaque_id)
    if source is None:
        if re.fullmatch(r'[0-9a-f]{24}',opaque_id):
            raise ValueError('Opaque item ID is absent from the local identifier map')
        return row
    result=dict(row,id=source['id'],source_qid=source['source_qid'],source_line=source['source_line'])
    if result.get('example_id')==opaque_id:result['example_id']=source['id']
    return result


def decode_inventories(root):
    mapping=load_map()
    r6_mapping=json.loads(MAP_PATH.with_name('R6_ID_MAP.json').read_text())
    for path in sorted(Path(root).rglob('ITEMS.jsonl')):
        raw=path.read_text()
        rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        decoded=[]
        for row in rows:
            if row.get('family') == 'r6':
                source=r6_mapping.get(row['id'])
                if source is None:
                    if row['id'] not in {r['id'] for r in r6_mapping.values()}:
                        raise ValueError('Unknown r6 item ID')
                    decoded.append(row)
                else:
                    decoded.append(dict(row, **source))
            else:
                decoded.append(logical_item(row,mapping))
        if decoded!=rows:
            path.write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for row in decoded))
