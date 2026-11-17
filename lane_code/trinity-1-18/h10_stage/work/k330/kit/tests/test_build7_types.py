import json
from pathlib import Path
import pytest
from h1eval.h10.launch import select_types, selected
from h1eval.modes import read_counts, DEFAULT_MODES
from h1eval.cli import modes

K=Path(__file__).resolve().parents[1]

def test_types_partition_devs1_routed():
    items=json.loads((K/'items/devs1_routed.json').read_text())['items']
    order=['camera_displacement','camera_rotation','camera_movement_direction','object_abs_distance']
    seen=[]
    for i in range(2):
        shard=selected(items,f'{i}/2')
        for t in order:
            chosen=select_types(items,shard,t)
            assert {r['question_type'] for r in chosen}=={t}
            seen+=[r['id'] for r in chosen]
    assert len(seen)==len(set(seen))==600
    per=sum(read_counts(select_types(items,items,t),modes(DEFAULT_MODES),arms=('own',))['reads'] for t in order)
    assert per==600+900
    with pytest.raises(ValueError,match='unknown'):select_types(items,items,'camera_typo')
