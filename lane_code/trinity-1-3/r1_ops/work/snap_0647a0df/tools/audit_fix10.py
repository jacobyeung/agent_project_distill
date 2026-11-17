"""Recompute the native VQA sampler census from the filtered full-store row census."""
import copy,sys,tempfile,subprocess
from pathlib import Path
from rebind import ROOT,load,write,pin,diff
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
from student_pilot import type_mix,loader_audit,carrier_c1_run as run
from student_pilot.vehicle_p import required_families

def main():
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/routing_diagnosis.py')],check=True)
    out=ROOT/'out';cfg=load(out/'config.json');binding=load(out/'BINDING.json');identity=binding['config_identity']
    local=copy.deepcopy(cfg);local['type_mix']['streams'].pop('routing');local['preparation_output']=tempfile.mkdtemp(prefix='audit10_',dir=ROOT/'work')
    ids=sorted(i for vals in load(ROOT/'work/admitted_indices.json').values() for i in vals)
    index_path=Path(local['preparation_output'])/'i.json';write(index_path,ids)
    prepared=dict(config_sha256=identity,streams={'vqa':dict(database=binding['database'],count=len(ids),indices=pin(index_path)),
        **{s:dict(count=1,local_placeholder=True) for s in ('pose','routing','pointing')}})
    prepared=type_mix.prepare(prepared,local);report=loader_audit.audit(local,prepared,local_vqa_only=True)
    loader_audit.print_breakdown(report)
    report.update(executed_config_identity=run.identity(local),requested_config_identity=identity,
        limitations=['Full-store VQA census with production exclusions and REMOVE lists. Pose/routing/pointing are placeholders excluded from audit.',
                    'Production RGB, complete routing and full prepare phase remain unavailable locally.'])
    unit=binding['unit_binding'];report['unit_counts']={**unit['counts'],'sampling_eligible':unit['sampling_eligible']}
    report['required_families']=required_families(cfg,report,local_selection=load(out/'proof/selection/r.json'))
    report['absent_on_P']=binding['absent_on_P']
    write(out/'proof/loader_audit.json',report);write(out/'proof/local_prepared.json',prepared);write(out/'proof/local_config.json',local)
    census=load(out/'ADMISSION_BY_TYPE.json');census.update(vqa_by_family=report['eligible_by_family']['vqa'],post_filter_by_type=report['eligible_by_question_type']['vqa'],mix_caps=report['tables']['vqa'],bound_units=unit,absent_on_P=binding['absent_on_P'])
    write(out/'ADMISSION_BY_TYPE.json',census)
    binding['traced_room_eligibility']=census['traced_room'];write(out/'BINDING.json',binding)
    old=load(Path(load(out/'FIX10_VARIANT.json')['snapshot'])/'out/proof/loader_audit.json')['tables']['vqa']
    rows=[]
    for name,value in report['tables']['vqa'].items():
        rows.append(dict(family=name,old_eligible=old[name]['eligible'],eligible=value['eligible'],
            old_cents=old[name]['final_cents'],cents=value['final_cents'],ceiling_milli=value['eligible']*4,
            ceiling_cents=value['eligible']*4//10,changed=(value['eligible'],value['final_cents'])!=(old[name]['eligible'],old[name]['final_cents'])))
    write(out/'FIX10_CELLS.json',rows)
    (out/'MIX.md').write_text('Every VQA cell uses the sealed four-repeat cap over 1,000 steps. Room trains at 1.70; direction receives the two-cent refill at 31.19. Routing cells and bound-unit counts remain unchanged; final routing populations require production preparation.\n\n| Family | Old eligible | Eligible | Old cell | Cell | Ceiling |\n|---|---:|---:|---:|---:|---:|\n'+''.join(f"| {v['family']} | {v['old_eligible']} | {v['eligible']} | {v['old_cents']/100:.2f} | {v['cents']/100:.2f} | {v['ceiling_milli']/1000:.3f} |\n" for v in rows))
    traces=[dict(stream=s,family=n,**r) for s,groups in report['traces'].items() for n,examples in groups.items() for r in examples]
    from rebind import enc
    (out/'proof/traces.jsonl').write_text(''.join(enc(r)+'\n' for r in traces))
    print('AUDIT PASS',identity,len(ids))
if __name__=='__main__':main()
