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
    for path in sorted(Path(root).rglob('ITEMS.jsonl')):
        raw=path.read_text()
        rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        decoded=[logical_item(row,mapping) for row in rows]
        if decoded!=rows:
            path.write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for row in decoded))
