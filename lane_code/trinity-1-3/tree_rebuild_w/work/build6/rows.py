"""Stream bounded real slices through real renderers and the pinned grammar."""
import collections, hashlib, json, re, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/('work/contracts_r6/tree_copy' if 'build5' in sys.argv else 'work/tree_r1');B=L/'work/build6';P=B/('proofs/rows_build5' if 'build5' in sys.argv else 'proofs/rows');P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(T))
from student_pilot import ground_rows, r2_grammar as G
try:
    from trace_format.contracts import contract_epoch
except ImportError:
    from contextlib import nullcontext
    def contract_epoch(enabled):return nullcontext()
from student_pilot.p3_provenance import digest
G.check_shared()
counts=json.loads((L/'work/rows_slices/slices_final/COUNTS_A0_v4.json').read_text())
mix=json.loads((L/'out/MIX_A0.json').read_text());rate=next(c['rows_per_step'] for c in mix['cells'] if c['type']=='units')
result=[];unit_counts=collections.Counter();unit_errors=[];square_feet=0
for name,entry in counts['families'].items():
    path=L/'work/rows_slices/slices_final'/entry['slice_file']
    assert path.stat().st_size==entry['slice_bytes']
    h=hashlib.sha256();n=0;examples=[];arms={str(k):dict(admitted=0,deferred=0,reasons=collections.Counter(),hash=hashlib.sha256()) for k in (False,True)}
    with path.open('rb') as f:
        for raw in f:
            n+=1;assert n<=2000;h.update(raw);row=json.loads(raw)
            if 'suffix' in row and 'target' not in row:
                events=[]
                for match in re.finditer(r'(<[a-z][a-z_0-9]*\b[^>\n]*>)\n(<tool_response>[\s\S]*?</tool_response>)',row['suffix']):
                    call,response=match.groups();audit={}
                    if row.get('simulated_misses') and 'not seen' in response.lower():audit=dict(simulated=True,status='not seen')
                    events.append(dict(call=call,response=response,audit=audit))
                row=ground_rows.pack({**row,'events':events},row.get('provenance',{}))
            elif row.get('ground_record') and not row.get('events'):
                row={**row,**ground_rows.pack(dict(row['ground_record'],suffix=row['target']),row.get('provenance',{}))}
            if name=='a0_units':
                unit=row['ground_record']['unit'];unit_counts[unit]+=1
                lines=[line for line in row['target'].splitlines() if line.startswith('Converting to ')]
                factor={'centimeters':Decimal('100'),'centimetres':Decimal('100'),'feet':Decimal('3.28084'),'inches':Decimal('39.3701')}.get(unit)
                try:
                    assert len(lines)==1,(len(lines),lines)
                    m=re.fullmatch(r'Converting to '+re.escape(unit)+r': ([0-9.]+) x ([0-9.]+) = ([0-9.]+)\.',lines[0])
                    assert m,lines[0]
                    a,b,c=map(Decimal,m.groups());assert b==factor
                    assert Decimal(str(round(float(a)*float(b),2)))==c and c==Decimal(str(row['answer']))
                    assert re.search(r'distance '+re.escape(str(m.group(1)))+r' m',row['target'])
                except (AssertionError,ValueError) as e:unit_errors.append(dict(qid=row['qid'],reason=str(e),lines=lines))
            if name=='a0_room':square_feet+=bool(re.search(r'square feet|square foot|sq\.? ft',row['student_input']['question'],re.I))
            outcomes={}
            for enabled in (False,True):
                arm=arms[str(enabled)]
                with contract_epoch(enabled):
                    try:
                        if row.get('events'):
                            target,spans=ground_rows.validate(row)
                            assert target==row['target']
                            G.validate_program({**row,'student_input':dict(question=row['question'],options=row['options'],frames=[None]*len(row.get('frame_indices',row.get('ground_record',{}).get('frame_indices',list(range(32))))))})
                        else:
                            target=row['target'];G.validate_direct(target,row['student_input']['question'],32)
                        arm['admitted']+=1;arm['hash'].update(target.encode());outcomes[str(enabled)]='admitted'
                    except (KeyError,ValueError,AssertionError,TypeError) as e:
                        arm['deferred']+=1;arm['reasons'][str(e)]+=1;outcomes[str(enabled)]=str(e)
            if len(examples)<200:examples.append(dict(qid=row['qid'],target_sha256=hashlib.sha256(row['target'].encode()).hexdigest(),outcomes=outcomes))
    assert h.hexdigest()==entry['slice_sha256'] and n==entry['slice_rows']
    for arm in arms.values():arm['hash']=arm['hash'].hexdigest()
    (P/(name+'.json')).write_text(json.dumps(dict(source=str(path.relative_to(L)),sha256=h.hexdigest(),examples=examples),indent=2)+'\n')
    result.append(dict(family=name,source=str(path.relative_to(L)),rows=n,sha256=h.hexdigest(),arms=arms))
units=dict(source='work/rows_slices/slices_final/a0_units.jsonl',count_source='work/rows_slices/slices_final/COUNTS_A0_v4.json',
           rate_source='out/MIX_A0.json',admitted_population=counts['families']['a0_units']['rows'],rows_per_step=rate,
           slice_counts=dict(unit_counts),errors=unit_errors,slice_projected_rows_per_step={k:rate*v/sum(unit_counts.values()) for k,v in unit_counts.items()},
           per_unit_rate_note='GUESS: slice frequency projection only; the supplied full-population census has no per-unit counts.',
           square_feet_room_rows=square_feet,room_source='work/rows_slices/slices_final/a0_room.jsonl',tree=str(T.relative_to(L)))
(P/'UNITS.json').write_text(json.dumps(units,indent=2)+'\n')
(P/'RESULTS.json').write_text(json.dumps(dict(families=result,grammar_sha256=G.SHARED_SHA256,
  boundary='Real packed-row reader and renderer plus grammar. No RGB, full scene intake or native model reader was run here.',
  build5_byte_parity='See PARITY.json: packed-output hashes match the authenticated build5 tree copy. Historical full-intake output receipts are absent.'),indent=2)+'\n')
print(json.dumps(dict(families=result,units=units))[:4500])
