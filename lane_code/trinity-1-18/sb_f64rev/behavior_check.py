"""Independent contract counterexamples plus the kit's layout tests on CPU."""
import hashlib
import importlib.util
import importlib.machinery
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'sb_f64'
KIT = SRC / 'out/kit'
TREE = SRC / 'pkg/work/tree_f64'
sys.path[:0] = [str(TREE), str(KIT / 'scripts'), str(KIT / 'read')]
os.environ.update(F64_TREE=str(TREE), F64_READER_ROOT=str(SRC / 'work/read_a/root'),
                  F64_META=str(SRC / 'in/qwen35_9b_meta'), F64_CONFIG=str(KIT / 'configs/r1_config_f64.json'))
tmp = ROOT / 'tmp/behavior'
tmp.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(tmp)
class RetainedDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None, **kw):
        self.name = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(tmp))
    def __enter__(self): return self.name
    def __exit__(self, *args): return False
    def cleanup(self): pass
tempfile.TemporaryDirectory = RetainedDirectory
reads = {str(Path(__file__))}
def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(os.fsdecode(args[0])).absolute()
        if (args[2] or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            if not p.is_relative_to(ROOT): raise RuntimeError('Write outside review: ' + str(p))
        elif p.is_relative_to(SRC): reads.add(str(p))
sys.addaudithook(guard)
import torch
torch.set_num_threads(8)
from student_pilot import frame_input as F
import f64_read as R
import token_audit
import nest_store

observations = {}
layout = R.training_layout({'frame_layout': 'duplicate'}, {'frame_count': 32, 'frame_input': F.NESTED})
observations['export_without_frame_input_accepts_nested_config'] = R.check_layout(R.READ_FRAMES, layout)
install = tmp / 'install/src/b/e2e_reader'
install.mkdir(parents=True, exist_ok=True)
(install / 'f64_read.py').write_bytes((KIT / 'read/f64_read.py').read_bytes())
observations['documented_install_top_level_import_found'] = importlib.machinery.PathFinder.find_spec('f64_read', [str(install.parent)]) is not None
empty = tmp / 'empty_shard.jsonl'
empty.write_text('')
summary = tmp / 'empty_summary.json'
token_audit.summarize(SimpleNamespace(shards=[str(empty)], out=str(summary)))
observations['empty_token_audit'] = json.loads(summary.read_text())
store = SRC / 'work/dryrun/n32/a43/pose/rows.sqlite'
observations['nest_store_missing_pins'] = nest_store.apply(store, {}, tmp / 'empty_nested.sqlite')
reads.add(str(store))

# Independent real-architecture count uses meta tensors and allocates no weights.
from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
meta = SRC / 'in/qwen35_9b_meta/config.json'
config = Qwen3_5Config.from_dict(json.loads(meta.read_text()))
with torch.device('meta'):
    model = Qwen3_5ForConditionalGeneration(config)
groups = dict(vision=0, merger=0, llm_layers=0, llm_root=0)
for name, p in model.named_parameters():
    key = ('merger' if 'merger' in name else 'vision') if '.visual.' in '.' + name else ('llm_layers' if '.layers.' in name else 'llm_root')
    groups[key] += p.numel()
observations['architecture'] = dict(groups=groups, total=sum(groups.values()),
    layers=len(model.model.language_model.layers), vision_depth=len(model.model.visual.blocks),
    full_attention=config.text_config.layer_types.count('full_attention'),
    linear_attention=config.text_config.layer_types.count('linear_attention'))
base, lm = sum(groups.values()), groups['llm_layers'] + groups['llm_root']
observations['sharded_master_grad_adam_gib_world4'] = (base * 4 + lm * 12) / 4 / 2**30
observations['gpu_formula_not_measurement'] = dict(
    gib_at_9127=57 + 2.7 * (9127 - 4500) / 1000,
    gib_at_10215=57 + 2.7 * (10215 - 4500) / 1000,
    gib_at_16384=57 + 2.7 * (16384 - 4500) / 1000,
    tripwire_tokens=4500 + (76 - 57) / 2.7 * 1000)

spec = importlib.util.spec_from_file_location('review_layout_suite', KIT / 'tests/test_f64_layout.py')
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
observations['layout_tests'] = dict(tests=result.testsRun, failures=[(str(t), m) for t, m in result.failures],
                                  errors=[(str(t), m) for t, m in result.errors], skipped=[(str(t), m) for t, m in result.skipped])
provenance = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(reads) if Path(p).is_file()}
provenance[str(empty)] = hashlib.sha256(empty.read_bytes()).hexdigest()
for p in (summary,):
    v = json.loads(p.read_text()); v['input_sha256'] = provenance
    p.write_text(json.dumps(v, indent=2) + '\n')
(ROOT / 'out/behavior_review.json').write_text(json.dumps(dict(command='bash run_cpu.sh behavior_check.py',
    input_sha256=provenance, **observations), indent=2) + '\n')
print(json.dumps(observations, indent=2))
