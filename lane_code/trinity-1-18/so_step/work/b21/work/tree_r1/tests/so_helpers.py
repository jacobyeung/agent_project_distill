"""Retained synthetic RGB/SQLite inputs and the tree's native tiny Qwen fixture."""
import copy
import json
import os
from pathlib import Path
import random
import sqlite3
import tempfile
from types import SimpleNamespace

import numpy as np
from PIL import Image
import torch

from student_pilot import carrier_c1_run as run
from student_pilot.p3_provenance import file_pin
from tests.so_processor import TinyProcessor
from tests.test_carrier_c1_final import final_fixture


def reset_switches(test):
    """Isolate process-local startup state in tests that train or change switches."""
    from student_pilot import c1_switches
    c1_switches._frozen = None
    test.addCleanup(setattr, c1_switches, '_frozen', None)


def root():
    return Path(tempfile.mkdtemp(prefix='so_', dir=os.environ['LANE_TEST_OUTPUT']))


def inputs(directory):
    image = directory/'rgb.png'
    Image.new('RGB', (32,32), (30,70,110)).save(image)
    frame = file_pin(image)
    target = dict(camera=[[0.,0.,0.,0.,0.,0.,1.,1.,1.]]*32, camera_mask=[True]*32,
        trajectory_scale=1., gravity=[0.,-1.,0.], gravity_mask=True,
        point_depth=dict(uv=[[[500.,500.]]]*32, depth=[[2.]]*32, mask=[[True]]*32))
    source = dict(question='Where is the chair?', options=[], frames=[frame]*32,
                  frame_indices=list(range(32)), timestamps=[i/30 for i in range(32)], fps=30,
                  total_num_frames=32, recording_id='synthetic-so', width=32, height=32)
    # Native duplicate layout uses these frame indices/timestamps unchanged.
    streams = {}
    for stream in ('pose','vqa','routing','pointing'):
        db = directory/(stream+'.sqlite')
        conn = sqlite3.connect(db)
        conn.execute('CREATE TABLE rows (i INTEGER PRIMARY KEY, row TEXT, target TEXT)')
        for index in range(32):
            row = dict(qid=f'{stream}-{index}', dataset='synthetic', scene='test',
                       target='<think>\n\n</think>\n\nA', student_input=source)
            if stream == 'routing':
                row['routing'] = dict(qid=row['qid'], events=[dict(kind='canonical_text', text='The chair is visible.')],
                                      answer='<answer>A</answer>')
            conn.execute('INSERT INTO rows VALUES (?,?,?)', (index,json.dumps(row),json.dumps(target)))
        conn.commit()
        conn.close()
        streams[stream] = dict(database=file_pin(db), count=32)
    return dict(streams=streams, training_mode='final', frame_layout='duplicate')


def native(world=1, factor=2):
    model, _, _ = final_fixture()
    # The existing lossless CPU processor uses character IDs. Enlarge only the
    # synthetic fixture's vocabulary; both arms use these exact initial weights.
    model.model.language_model.embed_tokens = torch.nn.Embedding(512,32)
    model.lm_head = torch.nn.Linear(32,512,bias=False)
    model.config.text_config.vocab_size = 512
    model.frame_layout = 'duplicate'
    model.auxiliary_heads.depth.config.p3['frame_layout'] = 'duplicate'
    model.recipe = {**model.recipe, 'world_size':world, 'reference_world_size':world*factor,
                    'global_batch':world*factor*4}
    model.r1_training = True
    model.train()
    return model


def compact_processor():
    """Lossless timestamp tokens keep native CPU backward tests small."""
    processor = TinyProcessor()
    processor.tokenizer.special = {**processor.tokenizer.special,
        **{f'<{i/10:.1f} seconds>':300+i for i in range(21)}}
    return processor


def plan(world=1, factor=2):
    return [(stream, [i*world+r for r in range(world)])
            for stream in ('pose','vqa','routing','pointing') for i in range(factor)]


def rng_state():
    return random.getstate(), copy.deepcopy(np.random.get_state()), torch.get_rng_state().clone()


def same_rng(a, b):
    return (a[0] == b[0] and a[1][0] == b[1][0] and np.array_equal(a[1][1],b[1][1])
            and a[1][2:] == b[1][2:] and torch.equal(a[2],b[2]))


def assert_nested(test, a, b):
    if isinstance(a, torch.Tensor):
        test.assertEqual(a.dtype,b.dtype)
        test.assertTrue(torch.equal(a,b))
    elif isinstance(a, dict):
        test.assertEqual(a.keys(),b.keys())
        for k in a:
            assert_nested(test,a[k],b[k])
    elif isinstance(a,(tuple,list)):
        test.assertEqual(len(a),len(b))
        for x,y in zip(a,b):
            assert_nested(test,x,y)
    else:
        test.assertEqual(a,b)
