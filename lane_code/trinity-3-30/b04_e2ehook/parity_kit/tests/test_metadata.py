import copy
from pathlib import Path
import sys

import pytest

from parity_kit.common import C8R, DENSE, FRAMES, OLD, key, module, read, rows, tasks
from e2e_reader import parity


def test_request_is_exactly_636():
    assert len(tasks({})) == 636


def test_real_metadata_rows_match_routed():
    # routed.trainer_row has no side effects; importing its launcher does not install its tree.
    sys.path.insert(0, str(C8R))
    import routed
    captures, dense = parity._captures(FRAMES), parity._captures(DENSE)
    chosen = [t for t in tasks({}) if len(dense[t['native']]['frames']) == 64][:3]
    for t in chosen:
        bound = parity.bind_item(t, dict(frames_root='/absent', frames_json=FRAMES, dense_manifest=DENSE), verify=False)
        assert bound['row'] == routed.trainer_row(t, captures[t['native']], '/absent', verify=False)
        assert len(bound['frames']['native_frames']) == 64
        assert [bound['frames']['dense_indices'][s] for s in bound['frames']['anchor_slots']] == captures[t['native']]['anchor_indices']


def test_bad_anchor_refused():
    dense = copy.deepcopy(read(DENSE))
    t = next(t for t in tasks({}) if len(dense['captures'][t['native']]['frames']) == 64)
    dense['captures'][t['native']]['frames'][0]['sha256'] = 'bad'
    with pytest.raises(ValueError, match='dense anchors differ'):
        parity.bind_item(t, dict(frames_root='/absent', frames_json=FRAMES, dense_manifest=dense), verify=False)


def test_recorded_scores_twenty_keys():
    ts = {key(t): t for t in tasks({})}
    old = [r for r in rows(OLD) if r['arm'] == 'unflagged' and r.get('decode')]
    chosen = []
    for typ in sorted({r['question_type'] for r in old}):
        chosen.extend([r for r in old if r['question_type'] == typ][:4])
    assert len(chosen) == 20
    for r in chosen:
        assert parity.score(ts[r['key']], r['decode']) == r['scores']


def test_unclosed_think_scores_zero():
    t = tasks({})[0]
    assert parity.score(t, dict(text=t['answer'], finish='eos')) == dict(answer=0.0, released_answer=0.0)


def test_all_selected_dense_bindings_and_short_captures():
    settings = dict(frames_root='/absent', frames_json=read(FRAMES), dense_manifest=read(DENSE))
    counts = {}
    for t in tasks({}):
        b = parity.bind_item(t, settings, verify=False)
        n = len(b['frames']['native_frames'])
        counts[n] = counts.get(n, 0) + 1
    assert counts == {32: 69, 64: 567}
    short = next(t for t in tasks({}) if len(settings['dense_manifest']['captures'][t['native']]['frames']) == 32)
    with pytest.raises(ValueError, match='require_dense64'):
        parity.bind_item(short, dict(settings, require_dense64=True), verify=False)
