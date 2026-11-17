"""Read bounded published slices; retain counts, hashes and short examples only."""
from collections import Counter
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib,itertools,json,re,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';P=B/'proofs/row_counts';P.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.r2_mix import table,allocation
from student_pilot.r2_exclusions import Exclusions
from student_pilot.r2_withheld import Withheld
from student_pilot.r0_exclusion import reserve
from student_pilot.p3_provenance import file_pin
from student_pilot.carrier_c1_routing import alias_of
sources=dict(benchmark='revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json',dev_ids='dose_pool/out/POOL_S1/EXCLUDE_DEV_S1.tsv',
    eval_ids='dose_pool/out/POOL_S1/EXCLUDE_EVAL_ROOMS.tsv',frames_gate='dose_pool/out/POOL_S1/FRAMES_GATE.json',
    eval_rooms='own_probe/out/EVAL_ROOMS.json',room_split='ofs_e1/out/ROOM_SPLIT.json',dev_manifest='devs1_masks/out/MANIFEST.json')
rules=Exclusions({k:file_pin(L/'fixtures/work/records'/v) for k,v in sources.items()});withheld=Withheld()
statuses=('not seen','unresolved','box unavailable')
paths=list(sorted((L/'work/rows_slices/slices_final').glob('*.jsonl')))
paths += [p for p in sorted((L/'work/rows_slices/slices_v3').glob('*.jsonl'))
          if p.stem not in ('a0_recovery','a0_units','a0_room','pool_abs_distance')]
families={};real=[]
for path in paths:
    counts=Counter();event_counts={s:Counter() for s in statuses};row_counts={s:Counter() for s in statuses}
    units=Counter();eligible_units=Counter();errors=[];examples=[];h=hashlib.sha256()
    for line in itertools.islice(path.open('rb'),2000):
        h.update(line);row=json.loads(line);counts['rows']+=1
        eligible=False
        if path.parent.name=='slices_final':
            provenance=row.get('provenance',{});canonical=row.get('canonical') or provenance['canonical']
            alias=provenance.get('alias') or (row['dataset']+'/'+row['scene'] if row.get('dataset') else alias_of(canonical))
            dataset,scene=alias.split('/',1)
            metadata={**row,'dataset':dataset,'scene':scene}
            coverage=dict(status='known',names=[alias,canonical])
            eligible=not rules.check(metadata,coverage) and not withheld.touches(metadata,coverage) and not reserve().matches(metadata)
            if eligible:counts['eligible_rows']+=1
        text=row.get('target',row.get('suffix',''));events=row.get('ground_record',{}).get('events',[])
        if not events:events=[{'response':s} for s in re.findall(r'<tool_response>.*?</tool_response>',text,re.S)]
        per_row=set()
        for e in events:
            printed=e.get('response','');audit=e.get('audit',{})
            for status in statuses:
                if status in printed.lower():
                    split='simulated' if audit.get('simulated') is True else 'not_simulated'
                    event_counts[status][split]+=1;per_row.add((status,split))
                    if split=='not_simulated':
                        counts['explicit_non_simulated_events' if audit.get('simulated') is False else 'simulation_flag_absent_events']+=1
                        if len(examples)<200:examples.append(dict(qid=row['qid'],status=status,simulated=audit.get('simulated'),row_sha256=hashlib.sha256(line).hexdigest()))
        for status,split in per_row:row_counts[status][split]+=1
        if per_row:
            counts['recovery_rows']+=1
            if eligible:counts['eligible_recovery_rows']+=1
            for split in ('simulated','not_simulated'):
                if any(x[1]==split for x in per_row):counts[split+'_rows']+=1
        if path.stem=='a0_units':
            question=row['question'].lower()
            unit=next((u for u,p in (('cm',r'centimet(?:er|re)s|\bcm\b'),('ft',r'feet|foot|\bft\b'),('in',r'inches|\bin\)')) if re.search(p,question)),None)
            units[str(unit)]+=1
            if eligible:eligible_units[str(unit)]+=1
            lines=[s for s in text.splitlines() if s.startswith('Converting to ')]
            metric=re.findall(r'<tool_response>\s*distance ([0-9.]+) m\s*</tool_response>',text)
            matches=[re.fullmatch(r'Converting to (.+?): ([0-9.]+) x ([0-9.]+) = ([0-9]+(?:\.[0-9]+)?)\.',s) for s in lines]
            why=[]
            if len(matches)!=1 or matches[0] is None:why.append('conversion_line_count_or_format')
            else:
                name,m,factor,answer=matches[0].groups()
                expected={'cm':Decimal('100'),'ft':Decimal('3.28084'),'in':Decimal('39.3701')}.get(unit)
                if len(metric)!=1 or Decimal(metric[0])!=Decimal(m):why.append('operand_differs_from_printed_metres')
                if Decimal(factor)!=expected:why.append('wrong_constant')
                quantum=Decimal(1).scaleb(-len(answer.split('.')[1]) if '.' in answer else 0)
                if (Decimal(m)*Decimal(factor)).quantize(quantum,rounding=ROUND_HALF_EVEN)!=Decimal(answer):why.append('written_arithmetic')
                final=re.search(r'<answer>(.*?)</answer>\s*$',text,re.S)
                if not final or final[1]!=answer or str(row['answer'])!=answer:why.append('unconverted_or_different_answer')
                if re.search(r'\b(?:meters|metres|m)\b',final[1] if final else ''):why.append('metre_answer_unit')
            if why and len(errors)<200:errors.append(dict(qid=row['qid'],reasons=why))
            counts['unit_rows_invalid' if why else 'unit_rows_valid']+=1
    families[path.stem]=dict(source=str(path.relative_to(L)),sha256=h.hexdigest(),counts=dict(counts),
        status_rows={s:{k:row_counts[s][k] for k in ('simulated','not_simulated')} for s in statuses},
        status_events={s:{k:event_counts[s][k] for k in ('simulated','not_simulated')} for s in statuses},
        units=dict(units),units_after_exclusions=dict(eligible_units),unit_errors=errors,examples=examples)
    if counts['not_simulated_rows']:real.append(path.stem)
counts_source=L/'work/rows_slices/slices_final/COUNTS_A0_v4.json';source_counts=json.loads(counts_source.read_text())
for name,v in source_counts['families'].items():
    assert families[name]['sha256']==v['slice_sha256']
    assert families[name]['counts']['rows']==v['slice_rows']
mix=table(both_path={'minority_count':2000});draws=allocation(mix)
rates={c['type']:Fraction(c['numerator'],c['denominator']) for c in mix['cells']}
unit_counts=families['a0_units']['units'];population=families['a0_units']['counts']['rows']
training_counts=dict(recovery=families['a0_recovery']['counts']['eligible_recovery_rows'],units={u:families['a0_units']['units_after_exclusions'].get(u,0) for u in ('cm','ft','in')},
    source_pins={k:{'path':v['source'],'sha256':v['sha256']} for k,v in families.items() if k in ('a0_recovery','a0_units')},
    scope='bounded published slices after unchanged sealed scene exclusions; production store bindings remain absent')
value=dict(families=families,non_simulated_status_families=real,training_counts=training_counts,
    mix_source='out/MIX_A0.json',counts_source=str(counts_source.relative_to(L)),counts_source_sha256=hashlib.sha256(counts_source.read_bytes()).hexdigest(),
    expected={arm:dict(recovery_rows_per_step=float(rates['recovery']),recovery_draws_per_step=draws['recovery']/mix['steps'],
        recovery_simulated_per_step=float(rates['recovery'])*families['a0_recovery']['counts'].get('simulated_rows',0)/families['a0_recovery']['counts']['rows'],
        recovery_not_simulated_per_step=float(rates['recovery'])*families['a0_recovery']['counts'].get('not_simulated_rows',0)/families['a0_recovery']['counts']['rows'],
        units_rows_per_step=float(rates['units']),unit_rows_per_step={u:float(rates['units']*n/population) for u,n in unit_counts.items()},
        unit_rows_per_step_after_exclusions={u:float(rates['units']*n/sum(training_counts['units'].values())) for u,n in training_counts['units'].items()},
        registered_unit_draws_per_step={u:draws['units']/mix['steps']*n/population for u,n in unit_counts.items()}) for arm in ('a0','a2')},
    expectation_scope='Conditional on sampling the bound slice proportions. COUNTS_A0_v4 does not supply full-store unit marginals. Actual post-exclusion store expectation remains unqualified until D3 is bound.',
    source_limit='At most 2000 rows per family; final A0 slices replace their older copies. No external cache, full store or deployment log was read.')
(P/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(families=len(families),non_simulated_status_families=real,units=unit_counts,unit_invalid=families['a0_units']['counts'].get('unit_rows_invalid',0),expected=value['expected'])))
with (B/'STATUS.md').open('a') as f:f.write('\nItems 2 and 2a: bounded status and unit census recorded in `work/build9/proofs/row_counts/RESULT.json`. Input refusal gates are next.\n')
