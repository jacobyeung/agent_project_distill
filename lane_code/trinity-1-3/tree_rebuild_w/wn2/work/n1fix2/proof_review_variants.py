"""Replay the exact named variants recorded by the independent reviewer."""
from pathlib import Path
import json,re,sys,sqlite3,hashlib,os
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/review_variants'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(B)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import row_text_audit as audit,carrier_c1_run as run
source=B/'proofs/review_inputs/N3_VARIANTS.json';review=json.loads(source.read_text())
reader=run.Rows(dict(streams={},r1_training={'schema':'r1-training-v1'}),None)
conn=sqlite3.connect(':memory:');reader.connections['vqa']=conn
conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
results={}
for name in review['all']:
    if name.startswith('heading_'):
        text='heading'+{'heading_nbsp':'\u00a0','heading_tab':'\t','heading_2sp':'  '}[name]+'unavailable'
    else:
        code=re.search('[0-9A-F]{4}',name).group();c=chr(int(code,16))
        template=name.replace(code,'{c}')
        text={'not{c}seen':'not{c}seen','not_sp{c}seen':'not {c}seen','box{c}unavailable':'box{c}unavailable',
              'inword_no{c}t_seen':'no{c}t seen','inword_un{c}resolved':'un{c}resolved','heading{c}unavailable':'heading{c}unavailable'}[template].format(c=c)
    row=dict(target='<think>'+text+'</think>\n1')
    gate=audit.reasons(row);assert gate,name
    conn.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
    try:reader.row('vqa',0)
    except ValueError as error:
        assert 'rule_only_text' in str(error),(name,error)
        result=str(error)
    else:raise AssertionError(name)
    results[name]=dict(gate=gate,reader=result)
reader.close()
assert len(results)==review['variants']==111
(O/'RESULT.json').write_text(json.dumps(dict(source=str(source.relative_to(L)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),variants=len(results),refused_both=len(results),results=results),indent=2))
monitor.save(O)
print('All exact reviewer variants refused: '+str(len(results)))
