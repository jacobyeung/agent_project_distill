# Own-arm beside tower-arm camera read (R1, step 400/600)

Status: kit built and proven on CPU (`sb_ownread_kit.tar`); not launched; waits for the 400/600 export and a GO.

## Question
How can one Orchard job read the 450 dev-S1 camera items with the own pose head beside the frozen G3T tower, pair them by item, and keep the tower arm identical to A4's read?

## Answer
Fork A4's delivery and change only the operator (`a/6.py`, bundled as `7.py`) and the token. The operator issues one descriptor with `arms=['tower','own']`, types 0, 1 and 2, and 900 expected reads. It runs one worker per camera type, `single_worker` False. Reseal with out3's recipe, which `build_ownread.py` checks by reproducing A4's bytes first, then score with `ownread.py`.

## Evidence
- The payload's per-type `run()` path accepts several arms. Only the single-worker `run_types` refuses an arm other than tower.
- `cpu_proof.py`: A4's operator and the fork write byte-identical tower settings, equal to A4's returned ones. A fixture read gives 900/900 through the real operator, runner and `launch.run`.
- `ownread.py` reproduces the registered step-544 gaps and their 544-RNG intervals from the step-544 rows.

## Options rejected
- Patch the single-worker path to allow own: it changes payload code hashes, breaks the tower identity with A4, and needs a payload review.
- Run the own arm as a separate job with H1-0's kit: a second export pull, different code, and no in-read pairing.
- Change settings to carry an own scale knob: the H1-0 rule (scale 1) lives in code, and a settings change would move the tower settings hash.
- Edit hashes by hand: forbidden; the builder reseals and verifies instead.

## What might not work, and how we would notice
- The per-type path with two arms has not yet run on a GPU. The Orchard CPU check's rehearsal, an incomplete `SUMMARY.json`, or a scorer refusal would show it.
- Wall time: the estimate is 2.12 h and the upper bound 3.05 h, against a 4.5 h admission stop. A partial return scores as incomplete with verdict None.
- The receipt path or object prefix at 400/600 may differ from step 200's; `build_ownread.py` pin validation or `o_pullfill.sh` fails closed.

## Tests that settle it
At step 400/600, the bar is met when all three types are complete and own−tower has a 95% room-bootstrap lower bound above −5 pp. The point estimate at −5 pp or above is the weaker signal.
