"""Independent v7 structural census and native 1,000-step VQA audit."""
import collections
import copy
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from rebind import ROOT,load,write,sha,pin
from build_cprime import SNAP,A
SOURCE=ROOT/'out/records/z.json'
from cprime_gate import B1
from cprime_recovery import local_pin
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
from student_pilot import carrier_c1_run as run,carrier_c1_data as data,type_mix,loader_audit,carrier_c1_routing as routing
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions
from student_pilot.h1_r0 import Reserve

LIST=re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first seen in)\s*:')
PROC=re.compile(r'count (?:it|each) once')

def summarize_draws(report,prepared,local):
    value=type_mix.bound(prepared,local)
    reverse={pos:name for name,positions in value['populations']['vqa'].items() for pos in positions}
    draws=collections.defaultdict(collections.Counter)
    for plan in data.mixed_indices({s:v['count'] for s,v in prepared['streams'].items()},local['recipe']['steps'],
            seed=local['recipe']['seed'],training_mode=local['training_mode'],mix=local['recipe']['mix'],
            world=local['recipe']['world_size'],type_mix=value):
        for stream,positions in plan:
            if stream=='vqa':
                for pos in positions:draws[reverse[pos]][pos]+=1
    report['per_cell_draws']={n:dict(draws=sum(draws[n].values()),unique_rows=len(draws[n]),max_draws_per_row=max(draws[n].values(),default=0))
        for n in local['type_mix']['streams']['vqa']['cells']}
    report['counting_draws_by_form'].update(FS_LIST=0,OTHER=0)
    assert report['planned_steps']==1000
    assert sum(v['draws'] for v in report['per_cell_draws'].values())==128000
    assert max(v['max_draws_per_row'] for v in report['per_cell_draws'].values())<=4
    return report

def main():
    cfg=load(ROOT/'out/config.json');base=load(SNAP/'out/config.json');binding=load(ROOT/'out/BINDING.json')
    db=Path(binding['database']['path']);assert sha(db)==binding['database_sha256']
    assert sha(SOURCE)==B1
    before=Removals([local_pin(v) for v in base['remove_files']])
    extra=Removals([dict(path=str(SOURCE),sha256=B1)])
    assert extra.source_counts==[17879]
    rule=Exclusions(local_pin(cfg['dev_scene_exclusions']),local_pin(cfg['benchmark_scene_exclusions']))
    held={s:set(v) for s,v in load(local_pin(cfg['exclude_qids'])['path']).items()}
    bench=routing.load_exclusions(local_pin(cfg['exclusions']))
    reported=routing.load_exclusions(local_pin(cfg['reported_exclusions'])) if 'reported_exclusions' in cfg else routing.load_exclusions(pin(A/'work/records/99e6eed6.json'))
    reserve=Reserve(pin(A/'work/reference/auth/R0_ROOMS.txt'))
    cells=cfg['type_mix']['streams']['vqa']['cells'];counts=[collections.Counter(),collections.Counter()]
    ids=[];all_before=[];forms={};seen=set();rejected=collections.Counter();types=set()
    with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as conn:
        for i,raw in conn.execute('select i,row from rows order by i'):
            row=json.loads(raw);types.add(row['question_type'])
            if not before.keep(row):rejected['base_remove']+=1;continue
            if run.held_row(row,'vqa',held,cfg.get('exclude_sources',{})):rejected['held']+=1;continue
            if rule.excluded(row) or reserve.excluded(row):rejected['scene']+=1;continue
            if run.excluded_row(row,bench,reported,'vqa')[0]:rejected['benchmark']+=1;continue
            try:
                data.layout_inputs(row,'duplicate',None,verify_partners=True)
                inp=row['student_input'];anchors=data.anchor_slots(inp);nested=anchors is not None and len(inp['frames'])==64
                assert nested or (len(inp['frames'])==32 and len(inp['frame_indices'])==32)
                assert not nested or (len(anchors)==32 and data.nested_indices([inp['frame_indices'][k] for k in anchors])==(inp['frame_indices'],anchors))
                assert all(set(f)=={'path','sha256'} for f in inp['frames'])
                assert isinstance(row.get('target'),str) and row['target'].strip()
            except (ValueError,KeyError,TypeError,AssertionError):rejected['structure']+=1;continue
            if run.routed_type(row,cfg):rejected['routed']+=1;continue
            name=type_mix.family(row,'vqa',cfg['type_mix']['size_selector'])
            if name=='excluded_room_trace':rejected['room_trace']+=1;continue
            assert row['qid'] not in seen;seen.add(row['qid'])
            all_before.append(i);counts[0][name]+=1
            if not extra.keep(row):continue
            ids.append(i);counts[1][name]+=1
            if name=='counting':forms[i]='FS_LIST' if LIST.search(row['target']) else ('PROC' if PROC.search(row['target']) else 'OTHER')
    print(json.dumps(dict(before=dict(counts[0]),after=dict(counts[1]),forms=dict(collections.Counter(forms.values())),admitted=len(all_before))),flush=True)
    old=load(SNAP/'out/proof/loader_audit.json')['tables']['vqa']
    assert {n:counts[0][n] for n in cells}=={n:v['eligible'] for n,v in old.items()},'C4 census does not reproduce'
    assert len(all_before)==203812
    assert counts[1]['counting']==2617 and counts[1]['totals']==0
    assert collections.Counter(forms.values())=={'PROC':2617}
    # Direction and facing are separate cells in the sealed loader.
    assert counts[1]['direction']+counts[1]['facing']==93370
    for n,v in cells.items():assert v['cents']*1000<=4*counts[1][n]*100,n
    for n in cells:
        if n not in ('counting','totals'):assert counts[0][n]==counts[1][n]
    census=dict(status='PASS_LOCAL_STRUCTURAL',database=binding['database'],remove_sha256=B1,
        before={n:counts[0][n] for n in cells},after={n:counts[1][n] for n in cells},
        ceilings={n:4*counts[1][n]/1000 for n in cells},
        direction_card_discrepancy='373.48 combines direction and facing; the direction cell alone has ceiling 199.604',
        admitted_before=len(all_before),admitted_after=len(ids),counting_forms=dict(collections.Counter(forms.values())),
        exclusions=dict(rejected),scope='Sealed row/scene/REMOVE predicates; no RGB byte verification or production preparation')
    write(ROOT/'out/CENSUS_CPRIME.json',census)
    local=copy.deepcopy(cfg);local['type_mix']['streams'].pop('routing')
    directory=Path(tempfile.mkdtemp(prefix='cprime_audit_',dir=ROOT/'work'));local['preparation_output']=str(directory)
    write(directory/'i.json',ids)
    prepared=dict(config_sha256=binding['config_identity'],streams=dict(vqa=dict(database=binding['database'],count=len(ids),indices=pin(directory/'i.json')),
        **{s:dict(count=1,local_placeholder=True) for s in ('pose','routing','pointing')}))
    prepared=type_mix.prepare(prepared,local)
    report=loader_audit.audit(local,prepared,local_vqa_only=True)
    report.update(requested_config_identity=binding['config_identity'],executed_config_identity=run.identity(local))
    prior=load(SNAP/'out/proof/loader_audit.json')
    for key in ('unit_counts','required_families','absent_on_P','limitations'):
        if key in prior:report[key]=prior[key]
    value=type_mix.bound(prepared,local);form_draws=collections.Counter();draws=collections.Counter()
    for plan in data.mixed_indices({s:v['count'] for s,v in prepared['streams'].items()},local['recipe']['steps'],seed=local['recipe']['seed'],
            training_mode=local['training_mode'],mix=local['recipe']['mix'],world=local['recipe']['world_size'],type_mix=value):
        for stream,positions in plan:
            if stream!='vqa':continue
            for pos in positions:
                index=ids[pos];draws[index]+=1
                if index in forms:form_draws[forms[index]]+=1
    assert form_draws=={'PROC':10460} and max(draws.values())<=4
    report['counting_draws_by_form']=dict(form_draws)
    summarize_draws(report,prepared,local)
    write(ROOT/'out/proof/loader_audit.json',report);write(ROOT/'out/proof/local_config.json',local);write(ROOT/'out/proof/local_prepared.json',prepared)
    print(json.dumps(dict(census=census,draws={k:v['draws'] for k,v in report['by_family'].items()},maximum=max(draws.values()),counting_forms=dict(form_draws))),flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['--summarize']:
        report=load(ROOT/'out/proof/loader_audit.json')
        assert report['requested_config_identity']==load(ROOT/'out/BINDING.json')['config_identity']
        summarize_draws(report,load(ROOT/'out/proof/local_prepared.json'),load(ROOT/'out/proof/local_config.json'))
        write(ROOT/'out/proof/loader_audit.json',report)
    else:main()
