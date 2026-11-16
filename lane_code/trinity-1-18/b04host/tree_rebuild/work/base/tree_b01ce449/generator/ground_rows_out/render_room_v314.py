"""Scene admission, exact replay, token gates and packing for room programs."""
import copy
import hashlib
import re
from collections import Counter
from derivgen import ground_v312 as G, ground_v313 as I
from derivgen.room_rows_v314 import QUESTION, agrees, validate_computation
from derivgen.ground_v313_tokens import gate_positions
from derivgen.programs_v314 import render


def physical_room(canonical):
    return re.sub(r'_\d{2}$', '', canonical)


def check_row(row, item, clip, backend, tokenizer, dev):
    from orchard_ground_adapter import pack, validate
    from student_pilot.live_trace313 import parse_response
    from trace_format.ground_v313 import Session as DecoderSession
    checks = Counter()
    canonical = row['canonical']
    devrooms = {physical_room(s) for s in dev}
    if canonical in dev or physical_room(canonical) in devrooms or row.get('physical_group') in devrooms:
        raise G.RowRefusal('dev_scan_or_room')
    checks['dev_exclusion'] += 1
    if row['frame_indices'] != item['frame_indices']:
        raise G.RowRefusal('room_frame_binding_mismatch')
    if row['question'] != QUESTION or row['options']:
        raise G.RowRefusal('room_question_template_mismatch')
    checks['template'] += 1
    if not agrees(row['answer'], item['gt_answer']) or row['gt_answer'] != item['gt_answer']:
        raise G.RowRefusal('room_label_mismatch')
    checks['label_equality'] += 1
    G.replay(row, I.Session(backend, clip.geo, clip.masks, multi_instance=True))
    checks['exact_replay'] += 1
    decoder = DecoderSession(backend, clip.geo, clip.masks, program_version='3.14', geometry_mode='sensor')
    for e in row['events']:
        body = decoder.execute(e['call'])
        parse_response(e['call'], body, '3.14')
        if G.wrap(body).encode() != e['response'].encode():
            raise G.RowRefusal('room_decoder_byte_mismatch')
    checks['decoder_bytes'] += 1
    validate_computation(row); checks['printed_computation'] += 1
    encoding = tokenizer.encode(row['suffix'], add_special_tokens=False)
    gates = gate_positions(tokenizer, row['suffix'])
    if (not gates or gates != row['mdg_gate_token_positions'] or
            row['suffix_tokens'] != len(encoding.ids) or row['suffix_tokens'] > 5000):
        raise G.RowRefusal('room_tokens_or_gates')
    if tokenizer.encode('<ground', add_special_tokens=False).ids != [tokenizer.token_to_id('<ground')]:
        raise G.RowRefusal('non_atomic_ground_opener')
    checks['tokens_and_gate_positions'] += 1
    if (row['training_admitted'] or not row['gt_accepted'] or not row['gt_agrees']
            or row['not_seen'] or row['simulated_misses']):
        raise G.RowRefusal('room_membership_flags')
    packed = pack(row, row['gt_authority'])
    target, _ = validate(packed)
    if target.encode() != row['suffix'].encode():
        raise G.RowRefusal('room_pack_byte_mismatch')
    checks['pack_roundtrip'] += 1
    return dict(checks), packed


def prepare(source, clip, backend, tokenizer, *, canonical, pin, frames, dev):
    item = copy.deepcopy(source)
    if not isinstance(canonical, str) or '/' not in canonical:
        raise G.RowRefusal('room_canonical_scene_required')
    if item.get('frame_indices', frames) != frames:
        raise G.RowRefusal('room_frame_binding_mismatch')
    item['frame_indices'] = list(frames)
    if item.get('canonical', canonical) != canonical:
        raise G.RowRefusal('room_scene_binding_mismatch')
    authority = item.get('gt_authority')
    if not isinstance(authority, dict) or authority.get('gt') != pin or authority.get('frame_indices') != frames or authority.get('canonical') != canonical:
        raise G.RowRefusal('room_gt_authority_binding_mismatch')
    devrooms = {physical_room(s) for s in dev}
    if canonical in dev or physical_room(canonical) in devrooms or item.get('physical_group') in devrooms:
        raise G.RowRefusal('dev_scan_or_room')
    session = I.Session(backend, clip.geo, clip.masks, multi_instance=True, geometry_mode='sensor')
    row = render(item, session, lambda s: len(tokenizer.encode(s, add_special_tokens=False).ids))
    identity = '\0'.join([item['qid'], canonical, pin['sha256'], repr(frames), row['suffix']])
    row.update(candidate_id=hashlib.sha256(identity.encode()).hexdigest(), canonical=canonical,
               scene=canonical, physical_group=item.get('physical_group'), roles={}, frame_indices=frames,
               gt_input=pin, diagnostic_only=True, training_admitted=False,
               mdg_gate_token_positions=gate_positions(tokenizer, row['suffix']),
               geometry_source='gt', mask_source='none')
    checks, packed = check_row(row, item, clip, backend, tokenizer, set(dev))
    row['room_checks'] = checks
    return row, packed
