"""Synthetic store boundary; all twin validators execute without substitutions."""
from pathlib import Path
import json,sqlite3
from student_pilot.p3_provenance import file_pin,load,write,digest
from student_pilot import r1_direction_twins as T,r1_rooms as R

def bind(cfg,root):
    import sys
    from refusal_twins import twins
    sys.modules['__main__'].twins=twins
    database=load(cfg['streams']['vqa']['path'])['database']
    R.STORE=database['sha256']
    rows=root/'twins.jsonl';records=root/'twins_binding.jsonl'
    count=0
    with sqlite3.connect(database['path']) as db,rows.open('w') as rf,records.open('w') as bf:
        for raw, in db.execute('SELECT row FROM rows ORDER BY i LIMIT 7971'):
            source=json.loads(raw);key=source['qid']
            twin=dict(source,qid='twin'+str(count),label_row_keys=[key])
            rf.write(json.dumps(twin,sort_keys=True,separators=(',',':'))+'\n')
            bf.write(json.dumps(dict(twin_key=twin['qid'],source_key=key,source_room='scannet/scene9997',twin_sha256=digest(twin)))+'\n')
            count+=1
    assert count==7971
    aliases=root/'twins_aliases.json';write(aliases,dict(complete=True,conflicts=[],quarantined_tokens=[],aliases={}))
    spec=dict(rows=file_pin(rows),binding=file_pin(records),aliases=file_pin(aliases),source_database=database)
    T.ROWS=spec['rows']['sha256'];T.BINDING=spec['binding']['sha256'];T.ALIASES=spec['aliases']['sha256']
    cfg['r1_training']['direction_twins']=spec
    write(root/'TWIN_BOUNDARY.json',dict(synthetic=True,rows=count,substituted_constants=['r1_rooms.STORE','r1_direction_twins.ROWS','r1_direction_twins.BINDING','r1_direction_twins.ALIASES'],
        reason='The capacity source store, frames, and labels are synthetic; the real producers and authentication functions run.',pins=spec))
