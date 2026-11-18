import json,os,sys,sqlite3
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c3');T=W/'pkg/work/tree_r1'
os.environ.update(R2_FIXTURES=str(W/'pkg/fixtures'),R2_PROOFS=str(W/'tmp'));sys.path[:0]=[str(T)]
from student_pilot import row_text_audit as A
from student_pilot.row_text_audit import reasons
from unittest.mock import patch
from student_pilot.carrier_c1_run import Rows
from student_pilot.p3_provenance import file_pin
from tests.test_r2_build9_recovery import TinyProcessor
PIN=file_pin(W/'pkg/work/n1fix3/inputs/extents.json')
DB='/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
src=sqlite3.connect('file:'+DB+'?mode=ro',uri=True)
real=[json.loads(r) for r, in src.execute("SELECT row FROM rows WHERE row LIKE '%<think>%' LIMIT 50")]
r=Rows({'streams':{},'extent_receipt':PIN,'r1_training':{'schema':'r1-training-v1'}},TinyProcessor())
c=sqlite3.connect(':memory:');r.connections['vqa']=c;c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
def reader(row):
    c.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
    try:r.row('vqa',0);return 'ADMIT'
    except Exception as e:return 'REFUSED '+str(e)[:60]
base=next(x for x in real if reader(x)=='ADMIT')
key='target' if 'target' in base else 'suffix'
V={}
for name,ch in [('200B','\u200b'),('200C','\u200c'),('200D','\u200d'),('2060','\u2060'),('FEFF','\ufeff'),('00AD','\u00ad'),('180E','\u180e'),('2061','\u2061'),('2062','\u2062'),('2063','\u2063'),('034F','\u034f'),('200E','\u200e'),('200F','\u200f'),('202C','\u202c'),('2066','\u2066'),('115F','\u115f'),('3164','\u3164')]:
    V['not'+name+'seen']='not'+ch+'seen';V['not_sp'+name+'seen']='not '+ch+'seen';V['box'+name+'unavailable']='box'+ch+'unavailable'
    V['inword_no'+name+'t_seen']='no'+ch+'t seen';V['inword_un'+name+'resolved']='un'+ch+'resolved';V['heading'+name+'unavailable']='heading'+ch+'unavailable'
V.update({'heading_nbsp':'heading\u00a0unavailable','heading_tab':'heading\tunavailable','heading_2sp':'heading  unavailable','NOT_SEEN_upper':'NOT SEEN','Box_Unavailable':'Box unavailable','Unresolved':'Unresolved','fullwidth_seen':'not ｓｅｅｎ','cyrillic_e':'not s\u0435\u0435n','combining':'not se\u0301en'})
out={}
for n,s in V.items():
    row=json.loads(json.dumps(base));t=row[key];row[key]=t.replace('<think>','<think>'+s+' ',1)
    g=reasons(row);rv=reader(row)
    with patch.object(A,'reasons',side_effect=AssertionError('gate called')),patch.object(A,'PATTERNS',{}),patch.object(A,'normalized_text',side_effect=AssertionError('gate norm called')):
        ri=reader(row)
    out[n]=dict(gate=bool(g),reader=rv[:40],reader_gate_disabled=ri[:60])
leak={n:v for n,v in out.items() if not v['gate'] or v['reader']=='ADMIT' or 'rule_only' not in v['reader_gate_disabled']}
EX={'Me_20DD':'no\u20ddt seen','Mn0_0E31':'no\u0e31t seen','braille_2800':'not\u2800seen','Mn_1D167':'no\U0001d167t seen','hangul_1160_inword':'no\u1160t seen','ideo_sp_3000':'not\u3000seen','ZW_no_space_join':'notseen','smallcap':'ɴᴏᴛ sᴇᴇɴ','math_bold':'𝐧𝐨𝐭 𝐬𝐞𝐞𝐧','greek_omicron':'n\u03bft seen','cyr_o':'n\u043et seen','Cf_FFF9':'no\ufff9t seen','Cf_0600':'no\u0600t seen','cyr_dze_s':'not \u0455een','cyr_T_upper':'NO\u0422 SEEN','greek_Nu':'\u039dOT SEEN','greek_Tau':'NO\u03a4 SEEN','cyr_a_box':'box un\u0430vailable','cyr_i_heading':'heading unava\u0456lable','cyr_es_tower':'tower_s\u0441ale_rule','armenian_o':'n\u0585t seen','cyr_u_unresolved':'unres\u043elved','Me_0489':'no\u0489t seen','latin_dotless_i_heading':'heading unava\u0131lable'}
extra={}
for n,s_ in EX.items():
    row=json.loads(json.dumps(base));row[key]=row[key].replace('<think>','<think>'+s_+' ',1)
    extra[n]=dict(gate=bool(reasons(row)),reader=reader(row)[:40])
res=dict(extra=extra,base_qid=base.get('qid'),field=key,variants=len(V),leaks=leak,refused=len(V)-len(leak))
print(json.dumps(res,indent=1));(W/'N3_VARIANTS_C3.json').write_text(json.dumps(dict(res,all=out),indent=1))
