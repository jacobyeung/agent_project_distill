"""Reviewer refute tests (review_offnative). Each asserts the contract the brief states."""
from copy import deepcopy
from types import SimpleNamespace as NS
import pytest
from offnative.io import dump, sha
from test_n3 import clips  # noqa: F401  (reuse the builder's 32/64 clip fixture)


@pytest.mark.parametrize('MODE',['prompt','indices'])
def test_R1_revsi_original_prompt_keeps_clip_frame_indices(tmp_path, clips, MODE):
    """The model must see the 32-frame clip exactly as the direct kit does: its own frame
    indices 0..31 and timestamps, with only G3T moving to the 64-frame clip."""
    from offnative.production import Runtime
    from offnative.frames import sample
    from offkit.frames import bind_frames
    from offnative.source import bind_source
    from offnative.c8 import install
    root, mapping, manifest = clips
    p = tmp_path/'mapping.json'; dump(p, mapping)
    target = tmp_path/'runtime'; (target/'revsi_media/b').mkdir(parents=True); (target/'bootstrap').mkdir()
    dump(target/'STAGE_READY.json', {})
    (target/'revsi_media/b/x.mp4').write_bytes((root/'b/x.mp4').read_bytes())
    media = tmp_path/'media'; media.mkdir()
    h = sha(root/'a/x.mp4'); (media/(h+'.mp4')).write_bytes((root/'a/x.mp4').read_bytes())
    binding = {'benchmark':'revsi999t32','reader':{'kind':'harness'},'read_config':{
        'g3t':bind_source(mapping=p,reader='harness'),'frames':bind_frames()}}
    item = dict(id='1',dataset='fixture',scene_name='x',question_type='object_counting_single',question='How many chairs?')
    rt = Runtime(target,[item],binding,{'media':[{'relative_path':'x.mp4','sha256':h}],
                 'media_root':str(media),'original_mapping':str(p)})
    rt.frames(bind_frames())
    _, direct = sample(media/(h+'.mp4'), bind_frames())
    cap = rt.captures['fixture:x']
    install()
    from routed import trainer_row
    from student_pilot.carrier_c1_data import layout_inputs
    row = trainer_row(dict(item, scene='fixture:x', native='fixture:x', options=[]), cap, rt.store)
    assert cap['total_num_frames'] == 32
    if MODE == 'prompt':
        layout_inputs(row, 'duplicate')   # the trainer prompt path the harness Context uses
    assert cap['anchor_indices'] == direct['indices'], (cap['anchor_indices'][-3:], direct['indices'][-3:])


def test_R2_unserved_decode_uses_registered_budget(monkeypatch):
    """Secondary arms must decode under the binding's budget (B2048 + 64), as the primary does."""
    from offnative.production import Unserved
    from offnative.c8 import install
    install()
    import student_pilot.carrier_c1_decode as D
    seen = {}
    def fake(model, processor, batch, **kw):
        seen.update(kw); return dict(text='<think>x</think>1', tokens=[1], calls=[], finish='stop')
    monkeypatch.setattr(D, 'generate', fake)
    ctx = NS(prompt=lambda frames, q: (None, {}))
    Unserved(NS(), NS(), ctx).generate(None, {})
    assert seen.get('logits_processor') is not None, 'no ThinkingBudget guard: up to %s tokens' % seen.get('max_new_tokens')


def test_R3_reduced_proof_reports_e2e_distance():
    """Brief: for e2e the camera items must be identical and the distance items are reported."""
    from offnative.proof import compare, LOSS_RECORD_SHA256
    from test_repin2 import reference, pin
    rows = reference(); changed = deepcopy(rows)
    k = next(i for i, r in enumerate(changed) if r['question_type'] == 'object_abs_distance')
    changed[k]['decode']['text'] = '<think>x</think>3'
    assert compare(rows, changed, 'e2e', mode='reduced', loss_pin=pin())['passed']


def test_R4_submit_argv_is_opaque():
    from offnative.transport import submission_argv, FORBIDDEN
    c = {'job_name':'a15_cot_ap'+'0'*16,'job':{'time_limit_s':21600},'pool':'/p','token':'a'*24}
    # cli.submission lines 95-96 append this --export argument to the sbatch argv.
    argv = submission_argv(c, '/p/x/1.sh')[:-1]+['--export=ALL,OFFNATIVE_PACKET_SHA256='+'0'*64, '/p/x/1.sh']
    text = ' '.join(argv).lower()
    assert not [w for w in FORBIDDEN if w in text]
