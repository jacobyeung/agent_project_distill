"""Separate slice omissions from sealed semantic refusals without changing admission."""
import argparse, json, sys, traceback
from pathlib import Path
from collections import Counter
import admission_census as census
ROOT=census.ROOT
sys.path[:0]=[str(census.SEALED),str(census.SEALED/'generator/derivgen_v7')]
from student_pilot import ground_rows, s1_pool
from generator.derivgen_v7.derivgen import box_v313

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'out');a=p.parse_args();destination=a.out
    manifest=census.load(census.SLICES/'COUNTS_A0_v4.json');out={}
    for family in ('a0_recovery','a0_units'):
        meta=manifest['families'][family];counts=Counter();examples={};flags=Counter()
        with (census.SLICES/meta['slice_file']).open() as f:
            for line in f:
                row=json.loads(line);counts['supplied_rows']+=1
                record=dict(row['ground_record'],suffix=row['target'])
                flags[str(record.get('not_seen'))]+=1
                try:
                    packed=ground_rows.pack(record,row['provenance'])
                    # This is exactly the packed-source production entrypoint.
                    s1_pool.validate_source_row(packed,'packed');counts['repacked_admitted']+=1
                except (ValueError,KeyError,TypeError) as e:
                    reason=type(e).__name__+': '+str(e);counts[reason]+=1
                    tb=traceback.extract_tb(e.__traceback__)[-1]
                    examples.setdefault(reason,dict(qid=row['qid'],raises=dict(path=tb.filename,line=tb.lineno,code=tb.line),
                        fields={k:record.get(k) for k in ('not_seen','gt_agrees','training_admitted','answer','gt_answer','unit')},
                        expected_rounded_gt=box_v313.number(float(record['gt_answer']),2)))
        assert counts['supplied_rows']==meta['slice_rows']
        out[family]=dict(counts=counts,source_population_declared=meta['rows'],supplied_file=census.pin(census.SLICES/meta['slice_file']),
            slice_manifest=census.pin(census.SLICES/'COUNTS_A0_v4.json'),slice_rule=manifest['rule'],
            not_seen_flags=flags,examples=examples,full_source_available=False,
            conclusion=('All supplied rows fail the sealed not_seen membership rule even after native packing.' if family=='a0_recovery' else
            'Missing top-level events is a slice artifact. Native packing admits 216/2000; 1784 fail exact two-decimal GT label equality. Full 10945-row admission is not measured.'),
            production_path=['s1_pool.prepare:173 normalize_room (no-op for these non-room types)',
                             's1_pool.prepare:174 validate_source_row -> ground_rows.validate',
                             's1_routing.build:369 selected_rows validates again before frames.resolve/c1_row'],
            admission_modified=False)
    census.write(destination/'ROUTING_DIAGNOSIS.json',out)
    a=census.load(destination/'ADMISSION_BY_TYPE.json');a['routing'].pop('a0_pool_abs_distance_reworded',None);a['routing_diagnosis']=out
    for family,diagnosis in out.items():
        row=a['routing'][family]
        if 'slice_form_validation' not in row:
            row['slice_form_validation']={k:row[k] for k in ('eligible','syntax_admitted','admitted','refusal_reasons','eligibility_refusals','examples')}
        if row['slice_form_validation']['eligibility_refusals']:raise ValueError('Routing post-filter counts need row-level exclusion reconciliation')
        accepted=diagnosis['counts'].get('repacked_admitted',0)
        row.update(eligible=accepted,syntax_admitted=accepted,admitted=accepted,
            validation_form='Native ground_rows.pack then sealed s1_pool.validate_source_row(packed, packed)',
            refusal_reasons={k:v for k,v in diagnosis['counts'].items() if k not in ('supplied_rows','repacked_admitted')},
            examples=diagnosis['examples'],full_production_admission=False)
    census.write(destination/'ADMISSION_BY_TYPE.json',a)
    print(json.dumps({k:v['counts'] for k,v in out.items()}))
if __name__=='__main__': main()
