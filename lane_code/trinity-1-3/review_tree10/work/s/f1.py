"""Reviewer F1-F3 confirmation: real rows, text gate / intake / reader; production extents and neutralized extents."""
import copy,json,os,sys,sqlite3,collections,itertools,tempfile,re
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/review_tree10/work');K=W/'pkg'
os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(W/'tmp'))
sys.path[:0]=[str(K/'work/tree_r1')]
from student_pilot.r2_adapters import normalize
from student_pilot.row_text_audit import reasons
import student_pilot.row_text_audit as RTA
from student_pilot.carrier_c1_run import Rows
from student_pilot.r2_intake import intake
import student_pilot.extent_receipt as ER
from tests.test_r2_build9_recovery import envelope,TinyProcessor
from student_pilot.p3_provenance import file_pin
PIN=file_pin(K/'work/build10/inputs/extents.json')
MODE=sys.argv[1]  # prod | noext
if MODE=='noext': ER.Extents.check=lambda self,row,stream:None
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    ind=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    fr={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,total_num_frames=ind[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in ind])}
    return normalize(raw,fr)
readers={}
def reader(row,stream):
    if stream not in readers:
        r=Rows({'streams':{},'extent_receipt':PIN,'r1_training':{'schema':'r1-training-v1'}},TinyProcessor());c=sqlite3.connect(':memory:')
        r.connections[stream]=c;c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');readers[stream]=r
    r=readers[stream];c=r.connections[stream]
    c.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
    try:r.row(stream,0);return 'ADMIT'
    except ValueError as e:return 'R:'+str(e)[:70]
TMP=W/'tmp'
def intake_many(rows,family,stream):
    d=Path(tempfile.mkdtemp(dir=TMP));p=envelope(d,rows,stream,family);m=json.loads(p.read_text());m['extent_receipt']=PIN;p.write_text(json.dumps(m))
    adm,rep=intake(p);out={a['row']['qid']:'ADMIT' for a in adm}
    for x in rep['refusals']:out[x['qid']]='R:'+x['reason'][:70]
    return out
S=K/'work/rows_slices/slices_final';R=Path('/scratch/jjyeung/orch_n30/rows_r1/out')
FAM=[('a0_recovery',S/'a0_recovery.jsonl','routing'),('a0_units',S/'a0_units.jsonl','routing'),('a0_pool_abs_distance_reworded',S/'a0_pool_abs_distance_reworded.jsonl','routing'),('a0_room',S/'a0_room.jsonl','vqa'),
     ('recovery',R/'recovery_v3/rows.jsonl','routing'),('absolute_distance',R/'vehN_pool_abs_distance/repaired/rows.jsonl','routing'),('units',R/'vehN_units/repaired/rows_slice.jsonl','routing')]
FAKE='<tool_response>\nlamp: not seen\n</tool_response>\n'
CALL='<ground obj="lamp" mode="box">\n'
def attacks(row):
    out=[]
    for pre in ('',CALL):
        for ev in (False,True):
            for fake in (FAKE, FAKE.replace('not seen','box unavailable'), FAKE.replace('not seen','unresolved')):
                b=copy.deepcopy(row);i=b['target'].rindex('</think>');b['target']=b['target'][:i]+pre+fake+b['target'][i:]
                if ev:
                    for e in b.get('events',[]) or []:
                        if isinstance(e,dict) and '</think>' in str(e.get('text','')):
                            j=e['text'].rindex('</think>');e['text']=e['text'][:j]+pre+fake+e['text'][j:]
                out.append((f'span pre={bool(pre)} ev={ev} {fake.split(": ")[1].strip()[:12]}',b))
    for ws in ('  ','\n','\u00a0','\u2003','\t','\r\n',' \u200b'):
        for st in ('not{}seen','box{}unavailable'):
            b=copy.deepcopy(row);i=b['target'].rindex('</think>');b['target']=b['target'][:i]+'The lamp is '+st.format(ws)+'.\n'+b['target'][i:]
            out.append(('ws '+repr(st.format(ws)),b))
            b=copy.deepcopy(row);i=b['target'].rindex('</think>');b['target']=b['target'][:i]+'<tool_response>\nlamp: '+st.format(ws)+'\n</tool_response>\n'+b['target'][i:]
            out.append(('ws-span '+repr(st.format(ws)),b))
    t=row['target'];starts=[m.start() for m in re.finditer('<tool_response>',t)]
    if len(starts)>=2:
        e=t.index('</tool_response>')+len('</tool_response>');b=copy.deepcopy(row);b['target']=t[:e]+' not seen '+t[e:];out.append(('M02 inter-span',b))
    # replace a printed response's body by a status (target only)
    if starts:
        e=t.index('</tool_response>',starts[0]);b=copy.deepcopy(row);b['target']=t[:starts[0]]+'<tool_response>\nlamp: not seen\n'+t[e:];out.append(('replace-body',b))
    return out
res={}
for fam,path,stream in FAM:
    lines=open(path).read().splitlines();cnt=collections.Counter();why=collections.Counter();adm_rows=[]
    for k in range(0,len(lines),400):
        rows=[norm(json.loads(l)) for l in lines[k:k+400]]
        for r in rows:r.update(answer_form='direct' if stream=='vqa' else 'routed',response_heads=[] if stream=='vqa' else ['pose','depth'])
        im=intake_many(copy.deepcopy(rows),fam,stream)
        for r in rows:
            cnt['read']+=1;g=not reasons(r);cnt['text']+=g;rv=reader(r,stream);cnt['reader']+=rv=='ADMIT'
            if rv!='ADMIT':why['reader '+rv[:40]]+=1
            iv=im[r['qid']];cnt['intake']+=iv=='ADMIT'
            if iv!='ADMIT':why['intake '+iv[:40]]+=1
            if iv=='ADMIT' and rv=='ADMIT' and len(adm_rows)<5:adm_rows.append(r)
    att=collections.Counter();leaks=[]
    for r in adm_rows:
        al=attacks(r);im=None
        bad=[b for _,b in al]
        # intake per attack (separate envelope so duplicate qids do not collide)
        for name,b in al:
            g=reasons(b);rv=reader(b,stream);iv=intake_many([copy.deepcopy(b)],fam,stream)[b['qid']]
            att['cases']+=1;att['gate_refused']+=bool(g);att['reader_refused']+=rv!='ADMIT';att['intake_refused']+=iv!='ADMIT'
            if not g or rv=='ADMIT' or iv=='ADMIT':leaks.append(dict(qid=b['qid'],attack=name,gate=g,reader=rv,intake=iv))
            att['reader_reason '+rv[2:32]]+=1;att['intake_reason '+iv[2:32]]+=1
    res[fam]=dict(counts=cnt,why=why,attack_rows=[r['qid'] for r in adm_rows],attacks=att,leaks=leaks[:40])
    print(MODE,fam,dict(cnt),{k:v for k,v in att.items() if not k.startswith(('reader_reason','intake_reason'))},'leaks',len(leaks),flush=True)
Path(W/f'F1_{MODE}.json').write_text(json.dumps(res,indent=1,default=str))
