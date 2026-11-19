"""Diff scale_donor.feature_contract between three ways of building CarrierC1's private depth:

fixture_train : the fixture training base (config -> Qwen3_5ForConditionalGeneration(...).float()), as the test uses
production_train : carrier_c1_run.load_model's loader, from_pretrained(dtype=bf16, attn_implementation='sdpa')
runtime : mdg_runtime._empty_base (config.json -> sdpa/bf16 config fields, no_init_weights)
Usage: python contract_diff.py <tree> <resume_dir>
"""
import copy, json, os, sys, tempfile, types
from pathlib import Path

W = Path(__file__).resolve().parent; NAME = sys.argv[1]; T = W / NAME; R = W / sys.argv[2]
OUT = Path(tempfile.mkdtemp(prefix=f'contract_{NAME}_', dir=W))
os.environ.update(TMPDIR=str(OUT), CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
tempfile.tempdir = str(OUT); os.chdir(T); sys.path.insert(0, str(T))
pk = types.ModuleType('tests'); pk.__path__ = [str(T / 'tests')]; sys.modules['tests'] = pk
import torch
torch.set_num_threads(8)
from transformers import Qwen3_5ForConditionalGeneration
from tests.test_carrier_c1_final import final_fixture
from student_pilot import mdg_runtime as runtime, scale_donor as D
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.p3_provenance import digest, load

receipt = load(R / 'prep_donor/receipt.json'); BINDING = receipt['scale_donor']
FX, _, _ = final_fixture()

def carrier(base):
    return CarrierC1(base, receipt['camera'], receipt['depth'], 5, receipt['carrier_placement'], receipt['training_mode'],
                     receipt['depth_enabled'], receipt['recipe'], receipt.get('skip_unsupervised_lm'),
                     receipt.get('frame_layout', 'spread'), receipt.get('depth_fov_source', 'private'))

torch.manual_seed(31)
fixture_train = Qwen3_5ForConditionalGeneration(copy.deepcopy(FX.config)).float()
snap = OUT / 'snapshot'
fixture_train.save_pretrained(snap)
production_train = Qwen3_5ForConditionalGeneration.from_pretrained(
    snap, local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16, attn_implementation='sdpa')
runtime_base = runtime._empty_base(snap)

contracts = {}
for name, base in (('fixture_train', fixture_train), ('production_train', production_train), ('runtime', runtime_base)):
    fc = D.feature_contract(carrier(base).auxiliary_heads.depth)
    contracts[name] = dict(digest=digest(fc), fc=fc)

def diff(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            out += diff(a.get(k, '<absent>'), b.get(k, '<absent>'), f'{path}.{k}')
        return out
    return [] if a == b else [f'{path}: {a!r} != {b!r}']

res = dict(tree=NAME, binding_feature_contract=BINDING['feature_contract_sha256'],
           digests={k: v['digest'] for k, v in contracts.items()},
           binding_equals_fixture_train=BINDING['feature_contract_sha256'] == contracts['fixture_train']['digest'],
           fixture_train_vs_runtime=diff(contracts['fixture_train']['fc'], contracts['runtime']['fc']),
           production_train_vs_runtime=diff(contracts['production_train']['fc'], contracts['runtime']['fc']),
           fixture_train_vs_production_train=diff(contracts['fixture_train']['fc'], contracts['production_train']['fc']))
(W / f'CONTRACT_{NAME}.json').write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
