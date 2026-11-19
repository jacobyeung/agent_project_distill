"""Placebo for the A8 refit (bash run.sh a8_placebo.py): drop the same number of random non-withheld priced rooms from
every fit fold and count changed OOF choices on comparable objects, to size the selector's refit noise."""
import json, random, statistics
from common import OUT, pin, write
import refit_a8 as RA


def main():
    legality = json.loads(open(OUT/'LEGALITY.json').read()); pin(OUT/'LEGALITY.json')
    withheld = set(legality['withheld_rooms'])
    caps, folds, config, groups = RA.groups_and_folds()
    saved = json.loads(RA.R.read(RA.R.OUT/'nonull/TRAIN_OOF.json'))['oof_choices']
    priced_withheld = {g['room'] for g in groups if g['room'] in withheld}
    others = sorted({g['room'] for g in groups} - withheld)
    rng = random.Random(20261119); draws = []
    for k in range(5):
        drop = set(rng.sample(others, len(priced_withheld)))
        choices, _ = RA.oof(groups, folds, config, drop)
        comparable = [g['object_id'] for g in groups if g['room'] not in drop and g['room'] not in withheld]
        draws.append(dict(dropped_rooms=sorted(drop), dropped_objects=sum(g['room'] in drop for g in groups),
                          changed=sum(choices[o] != saved[o] for o in comparable), comparable_objects=len(comparable)))
        print(json.dumps({k: v for k, v in draws[-1].items() if k != 'dropped_rooms'}), flush=True)
    refit, _ = RA.oof(groups, folds, config, withheld)
    comparable = [g['object_id'] for g in groups if g['room'] not in withheld]
    withheld_changed = sum(refit[o] != saved[o] for o in comparable)
    ch = [d['changed'] for d in draws]
    RA.PINS.update(RA.R.PINS)
    write('A8_PLACEBO.json', dict(rule='same fit and folds as A8_REFIT; each draw drops as many random non-withheld rooms as there are priced withheld rooms; '
                                       'changed = OOF choices that differ from the kit TRAIN_OOF.json on objects outside the dropped and withheld rooms',
                                  placebo_rooms=len(priced_withheld), draws=len(draws), changed_median=statistics.median(ch), changed_min=min(ch), changed_max=max(ch),
                                  withheld_changed=withheld_changed, withheld_comparable_objects=len(comparable), per_draw=draws))


if __name__ == '__main__':
    main()
