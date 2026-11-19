"""Check N's final scene gate, exact removal sets, and per-family retention."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import collections as C
import json,sys
from pathlib import Path
from stage_inputs import sha
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
CFG=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
B3=Path('/scratch/jjyeung/orch_n30/sb_rowB3');REVIEW=Path('/scratch/jjyeung/orch_n30/sb_brev3')
sys.path.insert(0,str(TREE))
from student_pilot.scene_division_gate import check_rows
from student_pilot.r2_contract import validate as native_contract
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions

def load(p):return [json.loads(s) for s in p.read_text().splitlines()]
def dump(name,x):(OUT/name).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
    cfg=json.loads(CFG.read_text());rows=load(OUT/'rows.jsonl');sources=load(ROOT/'inputs/sources.jsonl')
    pins={str(p):sha(p) for p in [Path(__file__),CFG,OUT/'rows.jsonl',ROOT/'inputs/sources.jsonl',REVIEW/'REMOVE_PROPOSED.json',B3/'out/REMOVE.json']}
    for pin in cfg['remove_files']+[cfg['scene_division'],cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions']]:
        assert sha(pin['path'])==pin['sha256'];pins[pin['path']]=pin['sha256']
    seal_path=TREE.parents[1]/'out/TREE_SEAL.json'
    seal=json.loads(seal_path.read_text());pins[str(seal_path)]=sha(seal_path)
    for mod in list(sys.modules.values()):
        p=getattr(mod,'__file__',None)
        if p and str(p).startswith(str(TREE)) and Path(p).is_file():
            pins[p]=sha(p)
            assert pins[p]==seal['files'][str(Path(p).relative_to(TREE))]
    result=check_rows(rows,cfg['scene_division'],removals=Removals(cfg['remove_files']),scene_filter=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions']),stream='vqa')
    assert result==dict(read=len(rows),filtered=0,removed=0,outside=0,heldout=0,admitted=len(rows)),result
    n=next(p for p in cfg['remove_files'] if p['path'].endswith('/records/n.json'))
    outside={r['row_key'] for r in load(Path(n['path'])) if r['reason']=='outside_native_training_division'}
    proposed=load(REVIEW/'REMOVE_PROPOSED.json');drop={r['row_key'] for r in proposed}&outside
    assert len(drop)==117
    actual=load(OUT/'REMOVE.json');wording=load(OUT/'REMOVE_WORDING.json');missing=load(OUT/'REMOVE_MISSING_GT.json')
    assert actual==[r for r in proposed if r['row_key'] not in drop]
    b3=load(B3/'out/REMOVE.json')
    assert wording==[r for r in b3 if r['reason']=='heldout_wording_distance_le_0.05'] and len(wording)==679
    missing_ids=set(json.loads((ROOT/'inputs/GT_REFUSALS.json').read_text())['refused'])
    assert {r['row_key'] for r in missing}==missing_ids and len(missing)==4420
    pins[str(ROOT/'inputs/GT_REFUSALS.json')]=sha(ROOT/'inputs/GT_REFUSALS.json')
    for name in ['REMOVE.json','REMOVE_WORDING.json','REMOVE_MISSING_GT.json']:
        p=OUT/name;rr=load(p);pins[str(p)]=sha(p)
        assert len({r['row_key'] for r in rr})==len(rr)
        assert p.read_text()==''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rr)
        assert all(set(r)=={'pool','question_type','reason','row_key','scene'} for r in rr)
    replaced={r['row_key'] for r in actual};words={r['row_key'] for r in wording}
    assert not (replaced&words or replaced&missing_ids or words&missing_ids)
    assert {r['qid'] for r in sources}==replaced|words|missing_ids|drop
    table={}
    for fam in sorted({r['question_type'] for r in rows}):
        old={r['qid'] for r in sources if r['question_type']==fam}
        delivered=sum(r['question_type']==fam for r in rows)
        old_kept=old-replaced-words-outside
        old_drop=old_kept-missing_ids
        usable=old&replaced
        table[fam]=dict(source_census=len(old),eligible_unique_sources=len(usable),rows_delivered=delivered,
          native_excluded_replaced_sources=len(old&drop),wording_old_removed=len(old&words),missing_gt_sources=len(old&missing_ids),
          missing_gt_already_outside_native=len(old&missing_ids&outside),old_rows_kept_if_missing_kept=len(old_kept),
          old_rows_left_if_missing_dropped=len(old_drop),total_rows_if_missing_kept=delivered+len(old_kept),
          total_rows_if_missing_dropped=delivered+len(old_drop),
          unique_sources_if_missing_dropped=len(usable|old_drop),
          under_1000_delivered=delivered<1000,under_1000_unique_sources_if_missing_dropped=len(usable|old_drop)<1000)
    dump('SCENE_GATE_CHECK.json',dict(status='PASS',input_sha256=pins,native_gate=result,refused=0,dropped_sources=117,dropped_scenes=len({r['scene'] for r in proposed if r['row_key'] in drop}),removal_counts={'replaced':len(actual),'wording':len(wording),'missing_gt':len(missing)}))
    dump('FAMILY_RETENTION.json',dict(status='PASS',input_sha256=pins,families=table,definition='Apply replacement and wording removal lists plus N outside_native_training_division. Delivered rows are added once. Report duplicate-expanded row counts and distinct source coverage separately; the orchestrator chooses whether to apply REMOVE_MISSING_GT.json.'))
    (ROOT/'STATUS.md').write_text(f'N scene_division_gate admits all {len(rows):,} final rows with zero refused, filtered, or removed. Exact compact removal sets and per-family retention counts pass. Independent raster checks and the thirty-row review determine final readiness.\n')
    print(json.dumps({'gate':result,'removals':{'replaced':len(actual),'wording':len(wording),'missing_gt':len(missing)},'families':table},indent=2))
if __name__=='__main__':main()
