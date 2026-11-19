"""End-to-end reader refusals through run.load_artifact on native exports (both variants)."""
import copy, json, os, sys, tempfile, types, uuid
from contextlib import ExitStack
from pathlib import Path
from unittest import mock
import torch

W = Path(__file__).resolve().parent; T = W / 'new'
os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
out = W / 'export'; out.mkdir(exist_ok=True); os.environ['LANE_TEST_OUTPUT'] = str(out); tempfile.tempdir = str(out)
torch.set_num_threads(8)
from tests.test_carrier_c1_final import final_fixture
from student_pilot import scale_donor as D, carrier_c1_run as run, full_ft
from student_pilot.p3_provenance import digest, file_pin


def fixture():
    m, b, t = final_fixture(); m.auxiliary_heads.depth.model.visual.requires_grad_(False); return m


def export(m, root):
    with ExitStack() as st:
        st.enter_context(mock.patch('student_pilot.fsdp_training.publication_state', side_effect=lambda w: w.state_dict()))
        for n_, v_ in (('get_rank', 0), ('get_world_size', 1)):
            st.enter_context(mock.patch.object(run.dist, n_, return_value=v_))
        st.enter_context(mock.patch.object(run.dist, 'barrier'))
        run.export(root, m, m, dict(base_identity='fixture', trace_program_version='3.13'), 2)
    return root


def forge(src, heads_fn=None, art_fn=None):
    """Copy an export, edit heads.pt and/or artifact.json, and repin."""
    dst = out / ('f_' + uuid.uuid4().hex); dst.mkdir()
    for f in src.iterdir():
        if f.is_file() and not (heads_fn and f.name == 'heads.pt'): (dst / f.name).write_bytes(f.read_bytes())
    art = json.loads((src / 'artifact.json').read_text())
    art['full_weights'] = art['full_weights']
    if heads_fn:
        state = torch.load(src / 'heads.pt', weights_only=True); heads_fn(state)
        full_ft._write_payload(dst / 'heads.pt', state)
    art['heads'] = file_pin(dst / 'heads.pt')
    if art_fn: art_fn(art)
    (dst / 'artifact.json').write_text(json.dumps(art))
    return file_pin(dst / 'artifact.json')


results = []
def expect(name, refuse, fn):
    try:
        fn(); ok = not refuse; err = None
    except Exception as e:
        ok = refuse; err = f'{type(e).__name__}: {str(e)[:120]}'
    results.append(dict(case=name, expected_refusal=refuse, ok=ok, error=err))


for variant in ('V1', 'V2'):
    m = fixture(); depth = m.auxiliary_heads.depth
    src = out / ('src_' + uuid.uuid4().hex); src.mkdir(); torch.save(m.auxiliary_heads.state_dict(), src / 'heads.pt')
    (src / 'artifact.json').write_text(json.dumps(dict(schema='carrier-c1-artifact-v1', pose_backing='lm_final_norm', step=400, heads=file_pin(src / 'heads.pt'))))
    cfg = dict(schema=D.SCHEMA, checkpoint=file_pin(src / 'artifact.json'), fov_source=variant,
               visual_sha256=D.visual_identity(depth.model.visual), feature_contract_sha256=digest(D.feature_contract(depth)))
    D.attach(m, cfg)
    exp = export(m, out / ('e_' + uuid.uuid4().hex))
    good = file_pin(exp / 'artifact.json')
    other = 'V2' if variant == 'V1' else 'V1'

    def reader(binding=cfg):
        f = fixture(); D.attach(f, binding); return f
    def bump(prefix):
        def fn(s):
            k = sorted(k for k in s if k.startswith(prefix))[0]; s[k] = s[k].clone(); s[k].reshape(-1)[0] += 1e-3
        return fn
    expect(f'{variant} clean export', False, lambda: run.load_artifact(reader(), good))
    expect(f'{variant} no attach', True, lambda: run.load_artifact(fixture(), good))
    expect(f'{variant} other FoV variant', True, lambda: run.load_artifact(reader(dict(cfg, fov_source=other)), good))
    for prefix in ('scale_donor.point_depth.', 'scale_donor.frame_queries', 'scale_donor.fov.', 'depth.model.visual.'):
        if prefix == 'scale_donor.fov.' and variant == 'V2':
            continue
        expect(f'{variant} changed {prefix}', True, lambda p=prefix: run.load_artifact(reader(), forge(exp, bump(p))))
    def drop(s): s.pop(sorted(k for k in s if k.startswith('scale_donor.'))[0])
    expect(f'{variant} missing donor tensor', True, lambda: run.load_artifact(reader(), forge(exp, drop)))
    def bf16(s):
        k = 'scale_donor.point_depth.vit_projs.0.weight'; s[k] = s[k].to(torch.bfloat16).to(torch.float32); assert not torch.equal(s[k], torch.load(exp / 'heads.pt', weights_only=True)[k])
    expect(f'{variant} bf16-rounded donor tensor', True, lambda: run.load_artifact(reader(), forge(exp, bf16)))
    def forged(s):
        bump('scale_donor.point_depth.')(s)
        md = s['_scale_donor']; st = {k.removeprefix(D.PREFIX): v for k, v in s.items() if k.startswith(D.PREFIX)}
        md['tensors'] = D.tensor_pins(st)
    def forged_art(a):
        st = torch.load(Path(a['heads']['path']), weights_only=True); a['scale_donor'] = st['_scale_donor']
    expect(f'{variant} forged heads+artifact metadata', True, lambda: run.load_artifact(reader(), forge(exp, forged, forged_art)))
    expect(f'{variant} artifact metadata dropped', True, lambda: run.load_artifact(reader(), forge(exp, None, lambda a: a.pop('scale_donor'))))
    def strip(s):
        for k in [k for k in s if k.startswith('scale_donor.')] + ['_scale_donor']: s.pop(k)
    expect(f'{variant} donor stripped from export', True, lambda: run.load_artifact(reader(), forge(exp, strip, lambda a: a.pop('scale_donor'))))
    expect(f'{variant} stripped export, reader without attach', False, lambda: run.load_artifact(fixture(), forge(exp, strip, lambda a: a.pop('scale_donor'))))

bad = [r for r in results if not r['ok']]
(W / 'EXPORT_MINE.json').write_text(json.dumps(dict(status='PASS' if not bad else 'FAIL', results=results), indent=1))
for r in results: print('ok ' if r['ok'] else 'BAD', r['case'], '|', r['error'])
