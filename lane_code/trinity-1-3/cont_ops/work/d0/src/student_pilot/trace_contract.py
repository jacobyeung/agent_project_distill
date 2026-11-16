ANSWER_FORMAT_INSTRUCTION = ('Think it through, then finish with the final answer alone on the last line: '
                             'the option letter for a multiple-choice question, or the number for a numeric question.')
EVALUATOR_COMMIT = 'df35a2636d1d198b02592aa2259b7d0647cefb07'
SOURCE_TRAINER_COMMIT = '7f11aa43387f891a2badf2531bf1fb8676bd1039'
SOURCE_ROWS = {
    'path': '/data3/jjyeung/trinity_lanes_20261006/count9_20261009/rows_v3/count_train.jsonl',
    'sha256': 'cd4d280993f2fa1ac0015cf750901054739b91616e0e5f7c0a5921a8aec59ce3',
    'size_bytes': 62986713,
}
HELDOUT_ROWS = {
    'path': '/data3/jjyeung/trinity_lanes_20261006/count9_20261009/rows_v3/scorer_holdout.jsonl',
    'sha256': 'd6836ad1e367f29ac063e768f996f105b2678533c5a03cea81de9a6b004f3f07',
    'size_bytes': 2831030,
}
SEEDS = (17, 18)
TRAINING_ROWS = 6000
WORLD_SIZE = 4
EPOCHS = 1
EFFECTIVE_BATCH_SIZE = 32
OPTIMIZER_STEPS = 188
