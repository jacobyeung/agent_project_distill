from pathlib import Path
import json
import os
import subprocess
import sys
import numpy as np
import pytest
from offnative.io import dump, load, sha
from offnative.paths import ROOT
from offnative.media import build, correspondence, stage
from offnative.source import bind_source, validate_mapping


def video(path, arrays):
    import av
    path.parent.mkdir(parents=True,exist_ok=True)
    with av.open(str(path),'w') as out:
        stream=out.add_stream('mpeg4',rate=24);stream.width=16;stream.height=16;stream.pix_fmt='yuv420p'
        for image in arrays:
            frame=av.VideoFrame.from_ndarray(image,format='rgb24')
            for packet in stream.encode(frame):out.mux(packet)
        for packet in stream.encode():out.mux(packet)


@pytest.fixture
def clips(tmp_path):
    indices=list(range(0,620,20))+[630]
    dense=list(range(0,640,10));slots=[dense.index(i) for i in indices]
    arrays=[np.full((16,16,3),30 if i%2==0 else 220,dtype=np.uint8) for i in range(64)]
    video(tmp_path/'clips/b/x.mp4',arrays)
    video(tmp_path/'clips/a/x.mp4',[arrays[i] for i in slots])
    mapping,manifest=build({'x':{'32-frame':indices,'64-frame':dense}},
                           [{'relative_path':'x.mp4','upload_required':True}],clips=tmp_path/'clips')
    return tmp_path/'clips',mapping,manifest


def test_registered_mapping_all_302():
    mapping=load(ROOT/'out/REVSI_DENSE_MAPPING.json')
    validate_mapping(mapping)
    assert len(mapping['clips'])==302
    registered=load(ROOT/'out/REGISTERED_FRAME_INDICES.json')
    for name,row in mapping['clips'].items():
        raw=registered[Path(name).stem]
        assert row['anchor_indices']==raw['32-frame']
        assert row['dense_indices']==raw['64-frame']
        assert row['anchor_slots']==[raw['64-frame'].index(i) for i in raw['32-frame']]
    assert bind_source()['mapping_sha256']==sha(ROOT/'out/REVSI_DENSE_MAPPING.json')


def test_pixel_correspondence_and_mapping_mutation(clips):
    root,mapping,_=clips
    result=correspondence(mapping,root)
    assert result['videos']==1
    row=result['records'][0]
    assert row['matched_mean']<3 and row['neighbour_mean']>150
    mapping['clips']['x.mp4']['anchor_slots'][3]=7
    with pytest.raises(ValueError,match='correspondence'):validate_mapping(mapping)


def test_media_staging_checks_every_hash(tmp_path,clips):
    import tarfile
    root,mapping,manifest=clips
    archive=tmp_path/'media.tar'
    with tarfile.open(archive,'w') as out:
        for prefix in ('a','b'):out.add(root/prefix/'x.mp4',arcname=prefix+'/x.mp4')
    receipt=stage(manifest,tmp_path/'staged',archive=archive,
                  archive_pin={'sha256':sha(archive),'bytes':archive.stat().st_size})
    assert len(receipt)==2
    with pytest.raises(ValueError,match='archive identity'):
        stage(manifest,tmp_path/'bad_archive',archive=archive,
              archive_pin={'sha256':'0'*64,'bytes':archive.stat().st_size})
    manifest['files'][0]['sha256']='0'*64
    with pytest.raises(ValueError,match='identity'):stage(manifest,tmp_path/'bad',archive=archive)
    manifest['hashes_pending']=True
    with pytest.raises(ValueError,match='pending'):stage(manifest,tmp_path/'pending',archive=archive)


@pytest.mark.parametrize('kind',['harness','e2e'])
def test_clip32_refused_for_claims(kind):
    with pytest.raises(ValueError,match='diagnostic'):
        bind_source('clip32',production=True,reader=kind,freeze={'g3t_source':'clip32'})


@pytest.mark.parametrize('kind',['harness','e2e'])
def test_native_production_frame_mapping_uses_64_clip_positions(tmp_path,clips,kind):
    from offnative.production import Runtime
    from offkit.frames import bind_frames
    from offnative.paths import V1,module
    root,mapping,manifest=clips
    p=tmp_path/'mapping.json';dump(p,mapping)
    target=tmp_path/'runtime';(target/'revsi_media/b').mkdir(parents=True)
    (target/'bootstrap').mkdir()
    # Runtime accepts an outer stage receipt, whose live identity is checked by stage().
    dump(target/'STAGE_READY.json',{})
    (target/'revsi_media/b/x.mp4').write_bytes((root/'b/x.mp4').read_bytes())
    media=tmp_path/'media';media.mkdir()
    h=sha(root/'a/x.mp4');(media/(h+'.mp4')).write_bytes((root/'a/x.mp4').read_bytes())
    binding={'benchmark':'revsi999t32','reader':{'kind':kind},'read_config':{
        'g3t':bind_source(mapping=p,reader=kind),'frames':bind_frames()}}
    runtime=Runtime(target,[dict(id='1',dataset='fixture',scene_name='x',question_type='object_counting_single',
        question='How many chairs?')],binding,{'media':[{'relative_path':'x.mp4','sha256':h}],
        'media_root':str(media),'original_mapping':str(p)})
    runtime.frames(bind_frames())
    G=module('_n3_dense_validation',V1/'sj/orch_cd/evalx/work/milestone/native/out2/geometry.py')
    capture=runtime.captures['fixture:x'];dense=runtime.dense['fixture:x']
    assert G.validate_dense(runtime.geometry_captures['fixture:x'],dense)==(list(range(64)),mapping['clips']['x.mp4']['anchor_slots'])
    assert len(dense['frames'])==64 and len(capture['frames'])==32
    assert len(runtime.sampled['fixture:x']['native_frames'])==64
    assert len(runtime.sampled['fixture:x']['model_frames'])==32


def test_vsi_full_cohort_inventory_and_admission():
    from offnative.cohort import cohort,media_manifest,name_inventory,canary
    from offkit.report import ReadMode,check_cohort
    from offnative.admission import check
    q=cohort('vsibench5130');mode=ReadMode('vsibench5130','harness')
    assert len(q)==5130 and len(media_manifest('vsibench5130',q))==288
    assert name_inventory(q)['unresolved']==[]
    assert name_inventory(q)['name_video_pairs']==845
    assert len(canary(q,mode))==10
    with pytest.raises(ValueError):check_cohort(mode,q[:-1])
    b={'mode':'production','benchmark':'vsibench5130','reader':{'kind':'harness','freeze_values':{}},
       'read_config':{'g3t':bind_source(benchmark='vsibench5130'),'frames':{'count':32}}}
    reasons=check(b,None)
    assert any('288 videos' in r for r in reasons)
    assert not any('not implemented' in r or 'original_mapping' in r for r in reasons)


@pytest.mark.parametrize('kind',['harness','e2e'])
def test_vsi_whole_worker(tmp_path,kind):
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    with (tmp_path/'execution.log').open('wb') as log:
        subprocess.run([sys.executable,'-B','-m','offnative.rehearse',str(tmp_path/'run'),kind,'vsibench5130'],
                       env=env,cwd=ROOT,stdout=log,stderr=log,check=True,timeout=120)
    result=load(tmp_path/'run/RESULT.json')
    assert result['passed'] and result['items']==20
    assert result['production_config_transport_only'] is False
    receipt=load(tmp_path/'run/return/receipts/01.json')
    assert all(row['dense']['count']==64 and len(row['dense']['anchor_slots'])==32 for row in receipt['result'])


def test_pinned_sources_and_no_offkit_copy():
    from offnative.paths import B04,R,C8,V1,TREE
    for root in (B04,R,C8,V1,TREE):
        assert root.is_relative_to(ROOT/'vendor')
        pins=load(root/'PIN.json')
        assert all(sha(root/name)==h for name,h in pins['files'].items())
    from offnative.portable import sources
    files,_=sources()
    assert not any(n.startswith('d/00/') for n in files)


def test_current_offkit_rejects_scripted_answers(tmp_path):
    from offkit.adapt_native import from_journal
    p=tmp_path/'journal.jsonl'
    p.write_text(json.dumps({'arm':'primary','key':'x','script_answer':'2'})+'\n')
    with pytest.raises(ValueError,match='scripted'):from_journal(p,'scripted')
    with pytest.raises(ValueError,match='script answer'):from_journal(p,'primary')
