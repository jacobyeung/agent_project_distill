from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import uuid
import pytest
from conftest import ROOT
import official_adapter as A
import official_score as O
import orchard_launcher as L
import orchard_stage as S
import fixtures as F
import frame_plan


def fresh(name):
    p=ROOT/'tests/runs'/(name+uuid.uuid4().hex[:8]);p.parent.mkdir(parents=True,exist_ok=True);return p


def spec():return A.dataset(ROOT/'inputs/revsi999_rows_t32.json')
def cohort():return O.read_rows(ROOT/'cohort/COHORT_REVSI5.jsonl')
def tasks(s=None):
    from data import tasks_for
    return tasks_for(s or spec(),dict(revsi_video_root='/tmp/v'))


def test_counts_media_and_ground_truth():
    rows=tasks();assert len(rows)==len({r['id'] for r in rows})==679
    assert Counter(r['question_type'] for r in rows)==A.COUNTS
    assert Counter(r['category'] for r in rows)==dict(object_counting=135,object_rel_direction=68,object_rel_distance=140,object_size_estimation=273,route_planning=63)
    media=json.loads((ROOT/'media/NEED_261.json').read_text());assert len(media)==261
    assert {r['scene']+'.mp4' for r in rows}=={r['relative_path'] for r in media}
    assert sum(r['bytes'] for r in media)==318248080
    native=json.loads((ROOT/'inputs/revsi999_rows_t32.json').read_text());gt={r['example_id']:r['ground_truth'] for r in native}
    assert all(r['ground_truth']==gt[r['example_id']] and r['revsi_tier']==32 and len(r['source_frame_indices'])==32 for r in rows)
    assert Counter(O.facing(r['question']) for r in rows if r['category']=='object_rel_direction')==dict(toward=35,away=33)


def test_evaluator_diff_is_only_data():
    for p in (ROOT/'reader/evaluator').rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            rel=p.relative_to(ROOT)
            assert (p.read_bytes()!=(ROOT.parent/'kit'/rel).read_bytes())==(p.name=='data.py')
    for name in ('proof/phase_b.py','reader/out/direct.py','reader/evaluator/metric.py','reader/evaluator/scoring.py'):
        assert (ROOT/name).read_bytes()==(ROOT.parent/'kit'/name).read_bytes()


def test_unfiltered_and_ancestral_guards():
    s=spec();s.pop('question_types');assert len(tasks(s))==999
    for field,value in [('tier',64),('set','cap452'),('sidecar',dict(path='absent',sha256='x'))]:
        with pytest.raises((ValueError,FileNotFoundError)):tasks(dict(spec(),**{field:value}))
    s=spec();s['rows']=dict(s['rows'],sha256='0'*64)
    with pytest.raises(ValueError):tasks(s)


@pytest.mark.parametrize('kinds',[[],['unknown'],['route_planning','object_counting_single'],['route_planning','route_planning'],[1],'route_planning'])
def test_bad_filter(kinds):
    with pytest.raises(ValueError):tasks(dict(spec(),question_types=kinds))


def test_filter_follows_full_cohort_checks():
    p=fresh('tamper');p.mkdir();rows=json.loads((ROOT/'inputs/revsi999_rows_t32.json').read_text())[:-1];file=F.js(p/'rows.json',rows)
    s=spec();s['rows']=dict(path=str(file),sha256=F.sha(file))
    with pytest.raises(ValueError):tasks(s)


def test_protocol():
    assert A.CELL==dict(model='cp1m200',layout='duplicate',benchmarks=['revsi'],frames=32,decoding='greedy',thinking=True,max_tokens=16384,name='a0')
    assert spec()['set']=='official999' and spec()['tier']==32


def scored(rows,value=1):
    return [dict(r,status='complete',score=value,thinking=True,output_tokens=4,max_new_tokens=16384) for r in rows]


def test_equal_subtype_weighting_and_scene_bootstrap():
    rows=cohort();answers=scored(rows)
    for r in answers:r['score']=1 if r['question_type']=='object_counting_single' else 0
    report=O.aggregate(rows,answers,answers)
    assert report['groups']['object_counting']['score']==.5
    assert report['five_category_mean']['score']==.1
    assert report['bootstrap']['repetitions']==10000
    assert report==O.aggregate(rows,answers,answers)
    assert report['direction_by_question_text']['toward']['items']==35
    assert set(report['groups'])==set(O.GROUPS) and 'overall' not in report


def test_native_official_metric_and_aggregate():
    import fakes,scoring
    fakes.fake_torch();scoring._METRIC_CLASS=None
    rows=tasks();answers=[]
    for t in rows:
        t=dict(t,thinking=True);score=scoring.score_item(t,'</think>\n'+t['ground_truth'],4)
        answers.append(dict(t,status='complete',**score))
    report=O.aggregate(rows,answers,answers,repetitions=100)
    metric=scoring.metric_for(rows);metric.update({int(r['example_id']):r['response_text'] for r in answers});native=scoring.clean_metric(metric.compute())
    for cat,g in report['groups'].items():assert g['score']*100==pytest.approx(native[cat+'_acc'])
    assert report['five_category_mean']['score']==1
    # Preserve the pinned implementation's float/int threshold construction.
    t=next(dict(t,thinking=True) for t in rows if t['question_type']=='object_counting_single')
    value=scoring.score_item(t,'</think>\n'+str(float(t['ground_truth'])*1.25),4)['score']
    assert value==pytest.approx(.6)


def test_errors_caps_and_missing_are_in_denominator():
    rows=cohort();answers=scored(rows);sources=copy.deepcopy(answers)
    answers[0].update(status='error',error='fixture',score=1);answers[1].update(parse_failed=True,output_tokens=64,max_new_tokens=64,finish_reason='length');sources[0]['output_tokens']=16384
    report=O.aggregate(rows,answers[:-1],sources,repetitions=100)
    assert sum(g['error_count'] for g in report['groups'].values())==2
    assert sum(g['source_capped'] for g in report['groups'].values())==1
    assert sum(g['continuation_capped'] for g in report['groups'].values())==1
    assert next(r for r in report['rows'] if r['id']==str(rows[0]['id']))['score']==0


def test_paired_bootstrap_identity_and_known_difference():
    rows=cohort();one=scored(rows);zero=scored(rows,0)
    ident=O.paired(rows,one,one)
    assert all(r['delta']==0 and r['percentile_95']==[0,0] for r in ident['comparisons'].values())
    result=O.paired(rows,one,zero)
    assert all(r['delta']==1 and r['percentile_95']==[1,1] for r in result['comparisons'].values())
    with pytest.raises(ValueError):O.paired(rows,one,zero[:-1])
    wrong=copy.deepcopy(zero);wrong[0]['ground_truth']='wrong'
    with pytest.raises(ValueError):O.paired(rows,one,wrong)
    wrong=copy.deepcopy(one);wrong.append(wrong[0])
    with pytest.raises(ValueError):O.paired(rows,wrong,zero)


def test_direction_comes_from_text():
    with pytest.raises(ValueError):O.facing('unrecognized wording')
    rows=[r for r in cohort() if r['category']=='object_rel_direction']
    t=next(r for r in rows if 'forward' in r['question_type'])
    assert O.facing(dict(t,question_type='backward')['question'])=='toward'


def test_media_archive_single_pass_deterministic_and_check(monkeypatch):
    sys.path.insert(0,str(ROOT/'media'));import make_archive,check_on_orchard
    p=fresh('archive');p.mkdir();clip=F.video(p/'a.mp4')
    need=F.js(p/'need.json',[dict(relative_path='a.mp4',source=str(clip),bytes=clip.stat().st_size,sha256=F.sha(clip))])
    opens=[];original=Path.open
    def op(path,*a,**kw):
        if path==clip and a and a[0]=='rb':opens.append(path)
        return original(path,*a,**kw)
    monkeypatch.setattr(Path,'open',op)
    a=make_archive.build(need,p/'a.tar',rate=0);assert len(opens)==1
    b=make_archive.build(need,p/'b.tar',rate=0);assert len(opens)==2 and a['sha256']==b['sha256']
    out=p/'extracted';out.mkdir()
    with tarfile.open(p/'a.tar') as tf:
        assert tf.getnames()==['a.mp4'];tf.extractall(out,filter='data')
    assert check_on_orchard.check(out,need)['verified']
    emitted=subprocess.run([sys.executable,'-B',str(ROOT/'media/check_on_orchard.py'),'--root',str(out),'--need',str(need),'--emit-script'],check=True,capture_output=True)
    checked=subprocess.run([sys.executable,'-I','-s','-B','-'],input=emitted.stdout,check=True,capture_output=True)
    assert json.loads(checked.stdout)['verified']
    (out/'a.mp4').write_bytes(b'bad')
    with pytest.raises(ValueError):check_on_orchard.check(out,need)


@pytest.mark.parametrize('fault',['bytes','hash','escape'])
def test_staging_rejects_media_corruption(monkeypatch,fault):
    p=fresh('stage_media');p.mkdir();package=p/'p';(package/'cohort').mkdir(parents=True)
    source=p/'a.mp4';source.write_bytes(b'abc')
    row=dict(relative_path='../x' if fault=='escape' else 'a.mp4',bytes=4 if fault=='bytes' else 3,sha256='0'*64 if fault=='hash' else F.sha(source))
    F.js(package/'cohort/MEDIA_MANIFEST.json',[row]);monkeypatch.setattr(S,'video_source',lambda *a:source);monkeypatch.setattr(S,'room',lambda *a:None)
    with pytest.raises(ValueError):S.stage_videos(p,dict(spec=dict(package=str(package)),media_root='/project/community/jjyeung/okh7/0123456789abcdef'),lambda r,x:Path(x))


def test_media_root_and_phase_b_switch():
    p=fresh('prepare');cfg=L.prepare('p0123456789',p,mode='proof',media_root='/project/community/jjyeung/okh7/0123456789abcdef',phase_b=False)
    assert not cfg['phase_b'];assert cfg['spec']['inputs']['video_root'].endswith('/v0')
    L.validate_batch((p/'BATCH.sh').read_text(),cfg)
    with pytest.raises(ValueError):L.prepare('p0123456789',fresh('invalid'),media_root='/data2/anything')


def test_real_timing_receipt_and_wrong_tier(monkeypatch):
    import media
    p=fresh('timing');p.mkdir();clip=F.video(p/'a.mp4');t=tasks()[0];t=dict(t,video_path=str(clip),video_sha256=F.sha(clip))
    _,audit=media.decode(t,'duplicate');source=t['source_frame_indices']
    assert audit['anchor_indices']==list(range(32))
    assert audit['metadata']['frames_indices']==[x for x in source for _ in range(2)]
    assert audit['metadata']['fps']==24*(source[-1]+1)/32
    with pytest.raises(ValueError):media.decode(dict(t,revsi_tier=64),'duplicate')


def test_nonuniform_native_category_formula():
    import fakes,scoring
    fakes.fake_torch();scoring._METRIC_CLASS=None
    rows=tasks();answers=[];native_answers={}
    for i,t in enumerate(rows):
        answer=t['ground_truth'] if i%3==0 else ('0' if t['question_type'] in ('object_counting_single','object_counting_multiple','object_size_estimation') else 'Z')
        native_answers[int(t['example_id'])]=answer
        answers.append(dict(t,status='complete',**scoring.score_item(dict(t,thinking=True),'</think>\n'+answer,4)))
    metric=scoring.metric_for(rows);metric.update(native_answers);native=scoring.clean_metric(metric.compute())
    report=O.aggregate(rows,answers,answers,repetitions=100)
    for name,value in report['groups'].items():assert value['score']*100==pytest.approx(native[name+'_acc'])
    assert report['five_category_mean']['score']==pytest.approx(sum(native[k+'_acc']/100 for k in O.GROUPS)/5)


def test_cluster_resampling_keeps_same_scene_answers_together():
    rows=[];answers=[];parent=[]
    for scene,value in [('a',0),('b',1)]:
        for kinds in O.GROUPS.values():
            for typ in kinds:
                t=dict(id=str(len(rows)),question_type=typ,dataset='fixture',scene_name=scene,question='If I am standing by the chair and facing the desk, where is the door?')
                rows.append(t);answers.append(dict(t,status='complete',score=value));parent.append(dict(t,status='complete',score=1-value))
    result=O.paired(rows,answers,parent,allow_partial=True)
    assert result['comparisons']['five_category_mean']['delta']==0
    assert result['comparisons']['five_category_mean']['percentile_95']==[-1,1]


def test_tier32_manifest_pins():
    videos=json.loads((ROOT/'inputs/revsi999_videos_t32.json').read_text())
    assert videos['tier']==32 and len(videos['files'])==302
    assert sum(v['bytes'] for v in videos['files'].values())==365324049
    for row in json.loads((ROOT/'media/NEED_261.json').read_text()):
        v=videos['files'][row['relative_path'][:-4]]
        assert row['sha256']==v['sha256'] and row['bytes']==v['bytes'] and v['frames']==32
        assert row['source']=='/data2/jjyeung/agent_project_data/external_benchmarks/revsi/32_frame/'+row['relative_path']
