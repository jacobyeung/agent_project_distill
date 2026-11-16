"""Build the toy artifact, inputs and the outside-artifact tables used by the planted variants."""
import json
from pathlib import Path

import numpy as np
import torch

from ..artifact import write_manifest
from . import planted
from .model import MODULES, ToyModel
from .reader import CallHandler, ToyReader

VARIANTS = {
    'clean': ToyReader,
    'table': planted.TableReader,
    'second_entry': planted.SecondEntryReader,
    'threshold': planted.ThresholdReader,
    'guard': planted.GuardReader,
    'cache': planted.CacheReader,
}
QUESTIONS = [('move', 'move|how far did the camera move from frame 1 to frame 2?'),
             ('depth', 'depth|how far is the centre of frame 1?')]


def build(workdir, items_per_type=3, seed=0):
    work = Path(workdir).resolve()
    art, inp, tab = work/'artifact', work/'inputs', work/'tables'
    for d in (art, inp, tab):
        d.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    model = ToyModel(CallHandler)
    torch.save(model.state_dict(), art/'weights.pt')
    write_manifest(art/'ARTIFACT.json', art, {'weights.pt': 'lm'}, MODULES)
    rng = np.random.default_rng(seed)
    items = []
    for k in range(items_per_type):
        frames = rng.normal(size=(4, 12)).astype(np.float32)
        np.save(inp/f'frames_{k}.npy', frames)
        for typ, question in QUESTIONS:
            items.append(dict(id=f'{typ}_{k}', type=typ, frames=str(inp/f'frames_{k}.npy'), question=question))
    (work/'items.jsonl').write_text(''.join(json.dumps(i)+'\n' for i in items))
    (tab/'scale_rule.json').write_text(json.dumps(dict(scale=1.07))+'\n')
    with torch.no_grad():
        towers = {k: model.tower(torch.from_numpy(np.load(inp/f'frames_{k}.npy'))).numpy()
                  for k in range(items_per_type)}
    np.savez(tab/'tower_cache.npz', tower=towers[0])
    return dict(work=str(work), artifact=str(art/'ARTIFACT.json'), items=str(work/'items.jsonl'),
                inputs=str(inp), tables=str(tab))


def make_reader(variant='clean', workdir=None, max_new_tokens=None):
    """Factory used by `eat1.run --reader eat1.toy.build:make_reader`."""
    work = Path(workdir).resolve()
    reader = VARIANTS[variant](work/'artifact', max_new_tokens=max_new_tokens)
    handler = reader.model.call_handler
    if variant == 'table':
        handler.table_path = str(work/'tables'/'scale_rule.json')
    if variant == 'cache':
        handler.tower_cache_path = str(work/'tables'/'tower_cache.npz')
    return reader
