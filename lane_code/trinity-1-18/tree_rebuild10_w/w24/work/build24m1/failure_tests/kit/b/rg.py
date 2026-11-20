"""Regenerate the native selection for review without training or a GPU."""
from pathlib import Path
import hashlib
import json
import sqlite3
from itertools import zip_longest


def regenerate(cfg, root, *, compare=True):
    from student_pilot.p3_provenance import pinned, load, digest, file_pin
    from student_pilot.s1_routing import build
    from student_pilot.mdg_parent import model_pin
    from z import write
    root=Path(root)
    point=load(pinned(cfg['streams']['pointing']))
    result=build(cfg,root/'selection',point['division'],model_pin(cfg))
    actual=pinned(result['database'])
    rows=0; row_ids=hashlib.sha256(); full=hashlib.sha256()
    with sqlite3.connect(actual.as_uri()+'?mode=ro',uri=True) as db:
        for i,row,target in db.execute('SELECT i,row,target FROM rows ORDER BY i'):
            value=json.loads(row)
            row_ids.update((json.dumps([i,value.get('qid',value.get('id'))],separators=(',',':'))+'\n').encode())
            full.update((json.dumps([i,row,target],separators=(',',':'))+'\n').encode());rows+=1
    inputs=dict(config_sha256=digest(cfg),routing_base=cfg['streams']['routing'],
        s1_routing=cfg['s1_routing'],division=point['division'],base_model=model_pin(cfg))
    comparison=None
    if compare:
        from copy import deepcopy
        p_pin=cfg['r1_training']['p_run']['config'];p=load(pinned(p_pin));pin=p['streams']['routing']
        if pin['sha256']!='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984':
            raise ValueError('P_TRAINED_ROUTING_PIN_DIFFERS')
        receipt=load(pinned(pin));p_db=pinned(receipt['database'])
        if not receipt['database']['sha256'].startswith('4e8e6c04'):raise ValueError('P_TRAINED_ROUTING_DATABASE_DIFFERS')
        materialization=load(pinned(receipt['materialization']))
        pcfg=deepcopy(p);pcfg['s1_routing']=materialization['inputs'];pcfg['streams']['routing']=materialization['legacy']
        from i import refresh
        p_input=write(root/'p0.json',pcfg)
        refreshed=refresh(dict(config=p_input,staged_pins=[p_input]),root/'pi')
        pcfg=load(pinned(refreshed['config']))
        reproduced=build(pcfg,root/'pr',materialization['division'],materialization['base_model'])
        hashes=[hashlib.sha256(),hashlib.sha256()];count=0
        with sqlite3.connect(p_db.as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(pinned(reproduced['database']).as_uri()+'?mode=ro',uri=True) as b:
            for before,after in zip_longest(a.execute('SELECT i,row,target FROM rows ORDER BY i'),b.execute('SELECT i,row,target FROM rows ORDER BY i')):
                if before!=after:raise ValueError('P_TRAINED_SELECTED_ROW_BYTES_OR_ORDER_DIFFER:'+str(count))
                for value,h in zip((before,after),hashes):h.update((json.dumps(value,separators=(',',':'))+'\n').encode())
                count+=1
        comparison=dict(source_p_config=p_pin,source_routing=pin,source_database=receipt['database'],rows=count,
            selected_rows_equal=True,selected_row_hashes=[h.hexdigest() for h in hashes],regenerated_sha256=digest(reproduced))
    value=dict(regenerated_sha256=digest(result),rows=rows,row_id_digest=row_ids.hexdigest(),row_bytes_sha256=full.hexdigest(),
        inputs_pinned=inputs,regenerated_receipt=file_pin(root/'selection/receipt.json'),p_regeneration=comparison,
        logical_output=str(root/'selection'))
    write(root.parent/'routing_selection.json',value)
    return value
