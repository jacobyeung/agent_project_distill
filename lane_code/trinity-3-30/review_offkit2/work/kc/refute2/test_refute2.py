"""Re-review (review_offkit2): each test PASSES while its defect exists."""
import json
import pytest
from offkit import report as R, bind as B, adapt_native as N
from test_hold import agg, harness, e2e_pass

# Fix 5, BLOCKING. The real C8r record nests the script fields in `decode`: perception.scripted() puts
# script_answer/script_mode into the decoded record, nomdg.make_record() stores it as row['decode'] via
# reader_policy.journal_decode (a deepcopy). from_journal checks only top-level fields, so a scripted
# record under any arm label other than exactly 'scripted' is scored.
def _c8r_scripted_row(arm, stringify):
    dec = dict(text='<think>\n<gap a="x" b="y">\n</think>\n\n10.83', finish='stop', script_answer='10.83',
               strict_no_answer=False, script_mode='native_v314_measurement_no_lm_answer')
    return dict(key='devrows:1', arm=arm, question_type='object_abs_distance', call_count=3,
                scores={'answer': 0.9, 'released_answer': None}, decode=str(dec) if stringify else dec)

@pytest.mark.parametrize('arm', ['unflagged', 'forced_route', 'Scripted'])
@pytest.mark.parametrize('stringify', [False, True])
def test_R5_c8r_schema_script_row_scored_under_other_arm_label(tmp_path, arm, stringify):
    p = tmp_path / 'j.jsonl'; p.write_text(json.dumps(_c8r_scripted_row(arm, stringify)) + '\n')
    u = N.from_journal(p, arm)
    assert u[0]['status'] == 'complete' and u[0]['score'] == 0.9 and not u[0]['refusal']

# Fix 1, non-blocking residual. binding_sha256 is an unkeyed self-hash: any caller can edit a binding and
# re-hash it (offnative/cli.py:30-32 does so for read_config), and ReadMode kind is the caller's choice.
def test_R1_rehashed_binding_and_e2e_readmode_give_claimable_words_on_harness_items(tmp_path):
    rep = agg('e2e')                                   # harness-served items, aggregated as e2e
    b = json.loads(json.dumps(harness(tmp_path)))
    b['reader'] = dict(kind='e2e', id='e2e manifest x', eat1=dict(passed=True)); b['arms'] = ['primary']
    b['binding_sha256'] = B.binding_sha256(b)
    lab = R.label_report(rep, binding=b, arm='primary', role='primary')
    assert lab['number_words'] == [] and R.HARNESS_WORDS not in lab['first_line']

# Fix 2, non-blocking. A whitespace override reason admits a mismatched layout.
def test_R2_whitespace_override_reason_admits_64_spread(tmp_path):
    b = B.bind('vsibench5130', 'step544', 'direct', ledger=tmp_path / 'l', frames=(64, 'spread'), frames_override_reason=' ')
    assert b['frames']['count'] == 64 and not b['frames']['layout_override_reason'].strip()
