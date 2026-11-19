"""Reproduce native VQA admission with exact production filter bytes on local paths."""
import collections,copy,json,sqlite3,sys,tempfile,traceback
from unittest.mock import patch
from pathlib import Path
from rebind import ROOT,H,load,write,pin,sha,enc
sys.path[:0]=[str(ROOT/'work/tree'),str(ROOT/'work/tree/generator/derivgen_v7')]
from student_pilot import carrier_c1_data as data
from student_pilot.s1_exclusions import Exclusions
from student_pilot.row_removals import Removals
DB=Path('/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
SOURCE=DB.parent/'receipt.json'
DIV=Path('/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json')
SNAP=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_8246a4dd')
def inputs():
    cfg=load(SNAP/'out/config.json'); k=H/'build/fx/k'
    def local(v):
        p=k/Path(v['path']).name
        assert sha(p)==v['sha256']
        return {**v,'path':str(p)}
    removes=[local(v) for v in cfg['remove_files']]
    exclusions=[local(cfg[k]) for k in ('dev_scene_exclusions','benchmark_scene_exclusions')]
    assert sha(DIV)==load(SOURCE)['division']['sha256']
    return cfg,removes,exclusions

def build(out,extra=None):
    cfg,removes,exclusions=inputs()
    if extra:removes.append(pin(extra))
    return data.build_stream(pin(SOURCE),pin(DIV),out,'vqa',training_mode=cfg['training_mode'],
        geometry_online=cfg.get('geometry_online'),remove_files=removes,source_receipt=True,scene_filter=Exclusions(*exclusions))

def main():
    directory=Path(tempfile.mkdtemp(prefix='prepare10_',dir=ROOT/'work'))
    cfg,removes,exclusions=inputs(); d=load(DIV);train=set(d['train_scenes']);held=set(d['heldout_scenes'])
    rule=Exclusions(*exclusions);remove=Removals(removes);bad=[];counts=collections.Counter();seen=set();duplicates=[]
    with sqlite3.connect(DB.as_uri()+'?immutable=1',uri=True) as conn:
        for i,text in conn.execute('select i,row from rows order by i'):
            r=json.loads(text);counts['input']+=1
            if not rule.keep(r,'vqa'):counts['scene_removed']+=1;continue
            if not remove.keep(r):counts['list_removed']+=1;continue
            counts['post_filter']+=1
            scene=r['dataset']+'/'+r['scene']
            if r['qid'] in seen:duplicates.append(r['qid'])
            seen.add(r['qid'])
            if scene not in train or scene in held:
                bad.append(dict(i=i,qid=r['qid'],type=r.get('question_type'),pool=r.get('pool'),scene=scene))
    assert not duplicates
    target=ROOT/'out/records/n.json'
    target.write_text(''.join(enc(dict(row_key=r['qid'],reason='outside_native_training_division',pool=r['pool'],question_type=r['type'],scene=r['scene']))+'\n' for r in bad))
    write(ROOT/'out/FIX10_OFFENDERS.json',dict(rows=bad,counts=dict(counts),by_pool_type=dict(collections.Counter(r['pool']+'::'+r['type'] for r in bad)),removal=pin(target),division=pin(DIV),exclusions=exclusions,existing_removals=removes,duplicates=duplicates))
    print('OFFENDERS',len(bad),dict(collections.Counter(r['pool']+'::'+r['type'] for r in bad)),flush=True)
    result=dict(directory=str(directory),source=pin(SOURCE),division=pin(DIV),database=pin(DB),removal=pin(target),tree_sha256=load(ROOT/'out/BINDING.json')['tree_sha256'])
    try:build(directory/'native_unmodified')
    except FileNotFoundError as e:
        result['native_unmodified']=dict(status='BLOCKED_LOCAL_RGB',error=str(e))
    else:raise AssertionError('Expected missing production RGB')
    write(ROOT/'out/FIX10_BUILD.json',result)
    # Test boundary only: retain every sealed row/filter/division predicate and
    # every frame pin. Missing RGB content cannot be certified on this node.
    def pin_only(path,expected=None,**kwargs):
        assert isinstance(expected,str) and len(expected)==64
        return dict(path=str(path),sha256=expected)
    with patch('student_pilot.common.binding',new=pin_only):
        structural(directory,result,target)

def structural(directory,result,target):
    result['scope']='STRUCTURAL ONLY: common.binding RGB byte reads mocked; all sealed row, scene, REMOVE, division and uniqueness predicates execute unchanged.'
    try:build(directory/'without')
    except ValueError as e:
        assert str(e)=='C1 data violate scene division or unique row identity',str(e)
        result['without']=dict(status='EXPECTED_FAILURE',error=str(e));print('BASELINE FAILED AS EXPECTED',flush=True)
    else:raise AssertionError('Baseline unexpectedly passed')
    write(ROOT/'out/FIX10_BUILD.json',result)
    rebuilt=build(directory/'with',target)
    result['with']=dict(status='PASS_STRUCTURAL_ONLY',receipt=pin(directory/'with/receipt.json'),count=rebuilt['count'])
    write(ROOT/'out/FIX10_BUILD.json',result)
    print('FIXED BUILD PASS',rebuilt['count'],flush=True)
if __name__=='__main__':main()
