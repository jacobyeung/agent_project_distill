import math
import random
from collections import defaultdict


SEEDS = ('17', '18')


def checked_scores(values, expected):
    result = {}
    for row in values:
        qid = str(row['qid'])
        credit = row['credit']
        if qid in result or row['status'] != 'ok' or type(credit) not in (int, float) or not math.isfinite(credit) or not 0 <= credit <= 1:
            raise ValueError('A native score is duplicate, failed, nonfinite or outside [0, 1]')
        result[qid] = (row['category'], credit)
    if list(result) != expected:
        raise ValueError('Native score membership or order differs from the frozen decision cohort')
    return result


def paired_scene_interval(control, treatment, membership, draws=10000, seed=20261012):
    if set(control) != set(treatment) or set(control) != set(SEEDS) or type(draws) is not int or draws < 10000:
        raise ValueError('The paired interval requires two fixed seeds and at least 10,000 draws')
    qids = [str(row['qid']) for row in membership]
    if not qids or len(qids) != len(set(qids)):
        raise ValueError('Frozen membership is empty or duplicated')
    scores = {(arm, training_seed): checked_scores(values[training_seed], qids)
              for arm, values in (('AO', control), ('TR', treatment)) for training_seed in SEEDS}
    groups = defaultdict(list)
    for item in membership:
        qid, category, scene = str(item['qid']), item['category'], item['physical_scene']
        if not isinstance(scene, str) or not scene or any(values[qid][0] != category for values in scores.values()):
            raise ValueError('A paired category or physical scene is missing or inconsistent')
        groups[scene].append(tuple(scores[('TR', training_seed)][qid][1] - scores[('AO', training_seed)][qid][1]
                                   for training_seed in SEEDS))
    clusters = [(len(values), tuple(math.fsum(value[index] for value in values) for index in range(2)))
                for _, values in sorted(groups.items())]

    def statistic(chosen):
        count = sum(cluster[0] for cluster in chosen)
        effects = tuple(math.fsum(cluster[1][index] for cluster in chosen) / count for index in range(2))
        return effects, math.fsum(effects) / 2

    effects, point = statistic(clusters)
    generator = random.Random(seed)
    samples = sorted(statistic([clusters[generator.randrange(len(clusters))] for _ in clusters])[1]
                     for _ in range(draws))
    return {'n': len(qids), 'physical_scene_clusters': len(clusters), 'draws': draws, 'rng_seed': seed,
            'seed_deltas_percentage_points': {training_seed: effect * 100 for training_seed, effect in zip(SEEDS, effects)},
            'point_delta_percentage_points': point * 100,
            'interval_95_percentage_points': [100 * samples[int(draws * 0.025)], 100 * samples[int(draws * 0.975)]],
            'method': 'Paired physical-scene bootstrap with replacement; keep all questions and both arms at both seeds in each scene, then average seed effects.',
            'interval_covers_question_sampling_only': True, 'same_scene_draw_for_both_seeds': True,
            'score_authority': False}
