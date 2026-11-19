"""The approved population (orchestrator RULING 1056Z, in/RULING_1056Z.md): out/v2/POPULATION.json.

decision : the 204 K1 training captures outside the withheld-80 rooms (GUARD.json) and their 1,012 rows; every bar reads it.
beside   : all 209 captures and 1,037 rows, reported next to the decision numbers; it decides nothing.
track_order: the decision captures, then the five withheld-room captures, so each arm reaches the decision population first.
population_id is a content digest (mc_common.population_digest); the tracker binds every carried file and its ledger to it.
Usage: python mc_population.py   (p1cpu interpreter)
"""
import json, time
import mc_common as C
import mc_ladder as L


def build(guard, rows_by_capture):
    withheld = sorted(guard['lists']['withheld_80']['hit_captures'])
    caps = sorted(rows_by_capture)
    decision = [k for k in caps if k not in withheld]
    rows = lambda ks: sorted(r for k in ks for r in rows_by_capture[k])
    body = dict(
        decision=dict(captures=decision, rows=rows(decision)),
        beside=dict(captures=caps, rows=rows(caps)),
        track_order=decision + [k for k in caps if k in withheld])
    body['population_id'] = C.population_digest(body)
    body['excluded_from_decision'] = dict(captures=withheld, rooms=guard['lists']['withheld_80']['hit_rooms'], rows=rows(withheld),
                                          reason='withheld-80 rooms (GUARD.json lists.withheld_80)')
    body['counts'] = dict(decision_captures=len(decision), decision_rows=len(body['decision']['rows']), beside_captures=len(caps),
                          beside_rows=len(body['beside']['rows']), excluded_captures=len(withheld),
                          excluded_rows=len(body['excluded_from_decision']['rows']))
    return body


def main():
    t0 = time.monotonic()
    ruling = C.read(C.RULING)
    guard = C.read_json(C.OUT/'GUARD.json')
    rowset = set(C.read(C.ROWSET).decode().split())
    by = {}
    for (arm, rid), r in L.published(('A0_deployed',)).items():
        by.setdefault(r['capture'], []).append(rid)
    if {r for v in by.values() for r in v} != rowset or len(rowset) != 1037:
        raise SystemExit('published A0 rows differ from K1_TRAIN_1037')
    body = build(guard, by)
    n = body['counts']
    if (n['decision_captures'], n['decision_rows'], n['beside_captures'], n['beside_rows']) != (204, 1012, 209, 1037):
        raise SystemExit(f'population counts {n} differ from RULING 1056Z (204/1,012 decision, 209/1,037 beside)')
    body.update(ruling=dict(path=str(C.RULING), sha256=C.PINS[str(C.RULING)],
                            text='make the 204 captures / 1,012 rows the decision population, report the 209/1,037 beside it, '
                                 'reject incompatible resumes'),
                seconds=time.monotonic()-t0)
    C.code_pins()
    C.write_json(C.POPULATION, body)
    print(json.dumps(dict(population_id=body['population_id'], counts=n)), flush=True)
    C.status(f"Population (POPULATION.json, RULING 1056Z): decision {n['decision_captures']} captures / {n['decision_rows']} rows; "
             f"beside {n['beside_captures']}/{n['beside_rows']}; id {body['population_id'][:12]}.")


if __name__ == '__main__':
    main()
