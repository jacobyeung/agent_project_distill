"""Real row text/intake/SQLite-reader checks; no RGB or head execution claimed."""
import copy, hashlib, itertools, json, os, sqlite3, sys
from collections import Counter
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';P=B/'proofs/text'
P.mkdir(parents=True,exist_ok=True)
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(P))
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
from student_pilot.r2_adapters import normalize
from student_pilot.row_text_audit import reasons
from student_pilot.carrier_c1_run import Rows
from student_pilot.r2_intake import intake
from tests.test_r2_build9_recovery import envelope,TinyProcessor
from student_pilot.p3_provenance import file_pin
extent_pin=file_pin(B/'inputs/extents.json')

hits={}
def trace(frame,event,arg):
    name=frame.f_code.co_filename
    if name.startswith(str(L/'work/tree_r1')+'/'):
        if event=='line':hits.setdefault(name,set()).add(frame.f_lineno)
        return trace
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,
        total_num_frames=indices[-1]+1,frames=[dict(path='/unavailable-rgb/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
    return normalize(raw,frames)
readers={}
def reader_result(row,stream):
    if stream not in readers:
        reader=Rows({'streams':{},'extent_receipt':extent_pin},TinyProcessor());c=sqlite3.connect(':memory:')
        reader.connections[stream]=c
        c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        readers[stream]=(reader,c)
    reader,c=readers[stream]
    c.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
    try:reader.row(stream,0);return 'admit'
    except ValueError as e:return str(e)
def size():return sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
results={};sizes=[]
for family,total,wanted in [('a0_recovery',1532,1458),('a0_units',2000,1895),('a0_pool_abs_distance_reworded',2000,1915),('a0_room',476,431)]:
    before=size();assert before<=200_000_000
    source=L/'work/rows_slices/slices_final'/(family+'.jsonl')
    folder=P/family;folder.mkdir(exist_ok=True)
    stream='vqa' if family=='a0_room' else 'routing';counts=Counter();refusals=Counter();examples=[];h=hashlib.sha256()
    with source.open('rb') as f:
        for lines in iter(lambda:list(itertools.islice(f,200)),[]):
            rows=[]
            for line in lines:
                h.update(line);row=norm(json.loads(line));row.update(answer_form='direct' if stream=='vqa' else 'routed',response_heads=[] if stream=='vqa' else ['pose','depth'])
                rows.append(row);counts['read']+=1
                counts['text']+=not reasons(row)
                verdict=reader_result(row,stream);counts['reader']+=verdict=='admit'
                if verdict!='admit':refusals['reader:'+verdict]+=1
            path=envelope(folder,rows,stream,family);manifest=json.loads(path.read_text());manifest['extent_receipt']=extent_pin;path.write_text(json.dumps(manifest))
            admitted,report=intake(path);counts['intake']+=len(admitted)
            refusals.update(r['reason'] for r in report['refusals'])
            if not examples:examples=rows[:5]
    attacks=Counter()
    for prefix in ('','<ground obj="lamp" mode="box">\n'):
        for consistent in (False,True):
            bads=[]
            for row in examples:
                bad=copy.deepcopy(row);fake=prefix+'<tool_response>\nlamp: not seen\n</tool_response>\n'
                bad['target']=bad['target'].replace('</think>',fake+'</think>')
                if consistent:
                    for e in bad.get('events',[]):
                        if '</think>' in e.get('text',''):e['text']=e['text'].replace('</think>',fake+'</think>')
                assert 'runtime_box_status' in reasons(bad)
                assert 'runtime_box_status' in reader_result(bad,stream)
                bads.append(bad)
            accepted,rep=intake(envelope(folder,bads,stream,family));assert not accepted
            attacks['cases']+=len(bads);attacks['text_refused']+=len(bads);attacks['reader_refused']+=len(bads);attacks['intake_refused']+=len(bads)
    results[family]=dict(source=str(source),sha256=h.hexdigest(),counts=counts,refusals=refusals,attacks=attacks)
    (folder/'RESULT.json').write_text(json.dumps(results[family],indent=2)+'\n')
    assert counts['read']==total and counts['text']==total,results[family]
    results[family]['original_intake_requested']=wanted
    after=size();assert after<=200_000_000;sizes.append(dict(family=family,before=before,after=after))
    print(family,dict(counts),dict(attacks),flush=True)
for whitespace in (' ','  ','\n','\u00a0','\u2003','\t'):
    for status in ('not'+whitespace+'seen','box'+whitespace+'unavailable','unresolved'):
        row=copy.deepcopy(examples[0]);row['target']+='\n'+status
        assert 'runtime_box_status' in reasons(row)
        assert 'runtime_box_status' in reader_result(row,'vqa')
# M02 must preserve an authored status between independently recorded responses.
text='<tool_response>\na\n</tool_response> not seen <tool_response>\nb\n</tool_response>'
responses=['<tool_response>\na\n</tool_response>','<tool_response>\nb\n</tool_response>']
fixture=dict(target=text,events=[dict(kind='ground_response',text=r,call_id=str(i)) for i,r in enumerate(responses)],
    tool_output_spans=[dict(start=text.index(r),end=text.index(r)+len(r),call_id=str(i),event_index=i) for i,r in enumerate(responses)])
assert 'runtime_box_status' in reasons(fixture)
import student_pilot.row_text_audit as audit
mutant={ '__name__':'student_pilot.mutant' }
source=Path(audit.__file__).read_text();assert source.count('[^<]*')==1
exec(compile(source.replace('[^<]*',r'[\s\S]*'),str(P/'M02.py'),'exec'),mutant)
assert mutant['reasons'](fixture)==[], 'M02 no longer reproduces the reviewed greedy defect'
(P/'MUTATION_RESULTS.json').write_text(json.dumps(dict(M02='caught: authored inter-span status disappears under greedy mutation',M10='equivalent: duplicate blocker insertion; unchanged'),indent=2)+'\n')
(P/'temporary_sizes.json').write_text(json.dumps(sizes,indent=2))
(P/'RESULT.json').write_text(json.dumps(dict(families=results,whitespace='PASS',mutation='PASS',standins='No RGB/head execution. Frame metadata-only pins and FPS=24 when absent; real normalize, intake and Rows.row with SQLite memory tables.'),indent=2)+'\n')
for reader,c in readers.values():reader.close()
monitor.save(P)
