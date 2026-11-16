"""Review envelope construction with immutable source rows and pinned grammar."""
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L/'work/tree_r1'))
from student_pilot.p3_provenance import file_pin, digest, write
from student_pilot.r2_contract import CONTRACT
from student_pilot.r2_grammar import SHARED_SHA256
from student_pilot.r2_materialize import materialize
from tests.test_r2_data_path import SOURCES
from student_pilot.carrier_c1_routing import alias_of
FPS_PATH=L/'work/kit07ca49df_meta/m/k/frame_rates.json'
FPS=json.loads(FPS_PATH.read_text())['by_scene']
FPS_SOURCES={key:[dict(path=str(FPS_PATH.relative_to(L)),fps=value)] for key,value in FPS.items()}
for group in ('slices_v3','slices_final'):
    for path in (L/'work/rows_slices'/group).glob('*.jsonl'):
        for index,line in enumerate(path.open()):
            assert index<2000
            record=json.loads(line);si=record.get('student_input',{});pr=record.get('provenance',{})
            fps=si.get('fps') or pr.get('fps_source',{}).get('value')
            if fps is None:continue
            key=(record['dataset']+'/'+record['scene'] if record.get('dataset') else
                 alias_of(record.get('canonical') or pr['canonical']))
            values=FPS_SOURCES.setdefault(key,[])
            if not any(v['fps']==fps and v['path']==str(path.relative_to(L)) for v in values):
                values.append(dict(path=str(path.relative_to(L)),qid=record['qid'],fps=fps))
for key,values in FPS_SOURCES.items():
    clocks={v['fps'] for v in values}
    FPS[key]=next(iter(clocks)) if len(clocks)==1 else None

def envelope(source, dest):
    dest.mkdir(parents=True)
    rows = [json.loads(line) for line in source.open()]
    assert len(rows) <= 2000
    pins = {k: file_pin(L/'work/records'/v) for k,v in SOURCES.items()}
    coverage, frames, bindings = {}, {}, {}
    for row in rows:
        pr = row.get('provenance', {})
        si = row.get('student_input', {})
        key = (row['dataset']+'/'+row['scene'] if row.get('dataset')
               else alias_of(row['canonical']) if row.get('canonical') else '')
        names = [v for v in (key, pr.get('alias'), pr.get('canonical'), row.get('canonical')) if v]
        coverage[row['qid']] = dict(status='known', names=names)
        indices = si.get('frame_indices') or row.get('frame_indices') or pr.get('frame_indices')
        fps = si.get('fps') or pr.get('fps_source', {}).get('value')
        if fps is None and row.get('canonical'):
            fps=FPS.get(alias_of(row['canonical']))
        if fps is None:
            bindings[row['qid']] = digest(row)
            continue
        frames[row['qid']] = dict(fps=fps, total_num_frames=si.get('total_num_frames') or indices[-1]+1,
            frames=[dict(path='/fh/'+hashlib.sha256(key.encode()).hexdigest()+'/'+str(i)+'.jpg',
                sha256=hashlib.sha256((key+'/'+str(i)).encode()).hexdigest(), source_index=i) for i in indices])
        bindings[row['qid']] = digest(row)
    write(dest/'coverage.json', dict(exclusions=pins, rows_sha256=file_pin(source)['sha256'], rows=coverage))
    write(dest/'frames.json', frames)
    program = bool(rows and (rows[0].get('ground_record', {}).get('events') or rows[0].get('events') or rows[0].get('suffix')))
    man = dict(schema='r2-family-manifest-v1', trace_contract=CONTRACT, validator_sha256=SHARED_SHA256,
        family=source.stem, stream='routing' if program else 'vqa', rows=file_pin(source), count=len(rows),
        row_bindings=bindings, scene_coverage=file_pin(dest/'coverage.json'), frame_map=file_pin(dest/'frames.json'),
        exclusions=pins, upstream_receipts=[], withheld_rooms=file_pin(L/'work/shared/WITHHELD_ROOMS_80.json'),
        dev_scene_exclusions=file_pin(L/'work/shared/dev_scene_exclusions_d0.json'))
    write(dest/'manifest.json', man)
    return dest/'manifest.json'

def main():
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write(output/'CLOCKS.json',FPS_SOURCES)
    results = []
    for group in ('slices_v3', 'slices_final'):
        for source in sorted((L/'work/rows_slices'/group).glob('*.jsonl')):
            if len(sys.argv)>2 and source.stem not in sys.argv[2:]:
                continue
            dest = output/group/source.stem
            man = envelope(source, dest)
            report = materialize([man], dest/'proof', metadata_only=True, dense=False)
            rep = report['intake'][0]
            counts = rep['counts'].values()
            result = dict(source=str(source.relative_to(L)), family=source.stem, group=group,
                seen=sum(c['seen'] for c in counts), admitted=sum(c['admitted'] for c in counts),
                refused=len(rep['refusals']), reasons=dict(collections.Counter(r['reason'] for r in rep['refusals'])),
                eval_rooms=sum('eval_rooms' in r['reason'] for r in rep['refusals']),
                status=report['status'], report=str((dest/'proof/materialization.json').relative_to(L)),
                boundary='Synthetic frame paths/hashes and, when absent, bound=max(source ordinals)+1; no RGB read. Published rows unchanged.',
                clock_authority=str(FPS_PATH.relative_to(L)))
            results.append(result)
            print(source.name, result['admitted'], result['refused'], result['reasons'], flush=True)
    write(output/'RESULTS.json', results)

if __name__ == '__main__':
    main()
