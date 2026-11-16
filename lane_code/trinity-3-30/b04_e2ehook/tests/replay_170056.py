"""Hook parity, token for token, on the recorded native read (Orchard job 170056, 636 dev-S1 items).

For every item of the model-written (unflagged) arm: feed the recorded token stream through the
CallHook as the decode loop would (sampled tokens via push_sampled, EOS via push_eos). At each call
the hook detects, it must report the recorded call text at the recorded position, and the ids it
returns must equal the recorded forced ids. Responses are computed from the SAME tensors the old
runtime used: the job's geometry export per clip (camera calls) and the recorded ground queries
(masks + geometry; ground/gap/room via the tree's AuditSession re-lift). No gravity guard is
applied (the job's guard refused no capture of this arm's geometry exports; refusals are counted).

Usage: python -B replay_170056.py <R1.json> <geometry_dir> <tokenizer_dir> <out.json> [--error-suffix]
"""
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449']


def tokenizer(path):
    from transformers import AutoTokenizer
    from student_pilot.carrier_c1_routing import add_routing_tokens
    tok = AutoTokenizer.from_pretrained(path)
    proc = NS(tokenizer=tok)
    tokens = add_routing_tokens(proc)
    return tok, tokens['ids']


def policy_audit():
    from copy import deepcopy
    from student_pilot.live_trace313 import AuditSession

    class PolicyAudit(AuditSession):
        """AuditSession + the C8r PerceptionSession rule: recorded instances whose depth cut was
        applied by the backend carry their (already cut) points as points_cut."""
        def _instances(self, name):
            q = self.pending[0] if self.pending else {}
            applied = {str(i['instance_id']): i.get('depth_cut_applied', False) for i in q.get('instances', [])}
            objects = super()._instances(name)
            for obj in objects:
                if obj.get('seen') and 'points_cut' not in obj and applied.get(str(obj['instance_id'])) is True:
                    obj['points_cut'] = deepcopy(obj['points'])
            return objects
    return PolicyAudit


def main():
    r1, gdir, tdir, out = sys.argv[1:5]
    suffix = '--error-suffix' in sys.argv
    from e2e_reader.callhook import CallHook
    from e2e_reader.servers import ReadServers
    from e2e_reader import geometry as G
    PolicyAudit = policy_audit()
    tok, openers = tokenizer(tdir)
    data = json.loads(Path(r1).read_text())
    rows = data['arms']['unflagged']
    result = dict(items=0, decoded=0, calls=0, call_text_equal=0, position_equal=0, forced_equal=0,
                  mismatches=[], guard=dict(sealed=[], reviewed=[]), by_family={}, seconds=0.)
    t0 = time.time()
    for row in rows:
        result['items'] += 1
        dec = row.get('decode')
        if not dec:
            continue
        result['decoded'] += 1
        clip = row['perception']['clip']
        geometry = G.from_npz(Path(gdir) / (clip + '.npz'))
        v = geometry.guard_verdicts
        if v['sealed_guard_refuses']:
            result['guard']['sealed'].append(clip)
        if v['reviewed_guard_refuses']:
            result['guard']['reviewed'].append(clip)
        queries = dec['heads'].get('ground_queries', [])
        # R1 stores most ground queries as a digest only; those items check detection and
        # positions, and their ground/gap/room responses are counted as not compared.
        session = PolicyAudit(queries, '3.14') if isinstance(queries, list) else None
        servers = ReadServers(geometry, session, serve_room=True)
        hook = CallHook(tok, openers.values(), ground_layout=True, error_suffix=suffix)
        hook.begin(servers.mapping())
        eos = {248046, tok.eos_token_id}
        tokens, recorded = dec['tokens'], dec['calls']
        i, k = 0, 0
        while i < len(tokens):
            t = tokens[i]
            if t in eos:
                hook.push_eos(t)
                i += 1
                continue
            forced = hook.push_sampled(t)
            i += 1
            if hook.records and len(hook.records) > k:
                rec, want = hook.records[k], (recorded[k] if k < len(recorded) else None)
                fam = rec['family']
                stats = result['by_family'].setdefault(fam, dict(calls=0, forced_equal=0))
                stats['calls'] += 1
                result['calls'] += 1
                ok_text = want is not None and rec['call'] == want['call']
                ok_pos = want is not None and rec['at_token'] == want['at_token']
                if not rec['served'] and want is not None:
                    forced = tokens[i:i + want['forced_tokens']]
                    stats['not_compared'] = stats.get('not_compared', 0) + 1
                    result['not_compared'] = result.get('not_compared', 0) + 1
                    ok_forced = True
                else:
                    expect = tokens[i:i + len(forced)]
                    ok_forced = want is not None and forced == expect and len(forced) == want['forced_tokens']
                result['call_text_equal'] += ok_text
                result['position_equal'] += ok_pos
                result['forced_equal'] += ok_forced
                stats['forced_equal'] += ok_forced
                if not (ok_text and ok_pos and ok_forced) and len(result['mismatches']) < 40:
                    result['mismatches'].append(dict(key=row['key'], k=k, call=rec['call'],
                        want_call=want and want['call'], hook_response=rec.get('response'),
                        want_response=want and want['response'], served=rec['served']))
                for f in forced:
                    hook.push_forced(f)
                i += len(forced)
                k += 1
        if k != len(recorded):
            result['mismatches'].append(dict(key=row['key'], detected=k, recorded=len(recorded)))
    result['seconds'] = time.time() - t0
    result['forced_compared'] = result['calls'] - result.get('not_compared', 0)
    result['pass'] = (result['calls'] == result['call_text_equal'] == result['position_equal'] == result['forced_equal']
                      and not result['mismatches'])
    Path(out).write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'mismatches'}, indent=1))
    print('mismatches', len(result['mismatches']))
    for m in result['mismatches'][:5]:
        print(json.dumps(m)[:600])


if __name__ == '__main__':
    main()
