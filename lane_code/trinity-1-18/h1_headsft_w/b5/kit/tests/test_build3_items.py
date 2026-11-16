import json
from h1eval import items
from rows.expected_calls import CAMERA_TYPES, expected_calls


def test_ready_sets():
    for name,count in [('revsi999',999),('devs1_routed',636),('devs1_direct_main',1525)]:
        m=items.load_manifest(items.K/'items'/f'{name}.json')
        assert m['count']==count and m['r0_check']['found']==0
        assert m['r0_check']['checked']==count
    m=items.load_manifest(items.K/'items/devs1_routed.json')
    inventory=json.loads((items.K/'items_sources/c8r_inventory.json').read_text())
    assert {r['id'] for r in m['items']}==set(inventory['keys'])
    cameras=[r for r in m['items'] if r['question_type'] in CAMERA_TYPES]
    assert len(cameras)==450
    for r in cameras:
        i,j=r['display_frame_pair']
        family='turn' if r['question_type']=='camera_rotation' else 'move'
        assert expected_calls(r['question'],r['question_type'])==[f'<{family} from={i} to={j}>']


def test_missing_twins(tmp_path):
    m=items.build(tmp_path,sets=['devs1_direct'])['devs1_direct']
    assert m['status']=='unavailable' and '300' in m['reason']


def test_arkit_venue_identity():
    assert items.room_key(dict(dataset='arkitscenes',scene='42897921',room='d3/venue423308'))=='arkitscenes/venue423308'


def test_twin_pins_refuse(tmp_path):
    fake=tmp_path/'twins.jsonl';fake.write_text('{}\n')
    m=items.build(tmp_path,sets=['devs1_direct'],forward_tasks=fake,away_tasks=fake)['devs1_direct']
    assert m['status']=='unavailable' and 'SHA256 mismatch' in m['reason']
