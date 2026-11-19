# Fair out-of-fold selector comparison
Decision: NO WIN. Mean fold gain V − S = -0.025352; 2 × sample fold SD = 0.109730.
Frozen rule: "serving labels win if V - S mean paired gap-MRA gain on K1 train exceeds 2 x fold SD of the paired gain".
Scope: K1 training captures only; five unchanged physical-room folds, seed 20261116. No held-out data or results were read.
Primary: 215 captures; 24 missing S4/G1 tables are excluded from both fitting arms and primary scoring. Exact missing paths appear in SELREFIT2.json.
Secondary: the same fold models score all 239 training captures, including the 24 missing-table captures; neither arm trains on those 24.
S uses native S4/G1 tables; V uses native serving-geometry tables. Their candidate pools and features can differ; this tests the full training-table intervention.
Both arms: 58-feature DeepSets, hidden 32, no name embedding, candidate/null BCE, AdamW lr .003 and wd .001, 15 epochs, batch 16; no search.
Both arms score through own-depth median_ratio scale, serving gravity, null-argmax, and the printed two-decimal socket distance against corrected labels; refusals score zero.

| Scope | Rows | S gap MRA | V gap MRA | V − S | S/V refusals | S/V choice accuracy |
|---|---:|---:|---:|---:|---:|---:|
| primary | 883 | 0.460476 | 0.432050 | -0.028426 | 248/255 | 0.689815/0.683642 |
| all_training | 1037 | 0.452266 | 0.434812 | -0.017454 | 296/288 | 0.690789/0.682895 |
| missing_s4_g1_only | 154 | 0.405195 | 0.450649 | +0.045455 | 48/33 | 0.696429/0.678571 |

| Primary fold | Rows | S gap MRA | V gap MRA | V − S | S/V refusals | S/V choice accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 200 | 0.493000 | 0.403500 | -0.089500 | 53/67 | 0.664234/0.656934 |
| 1 | 180 | 0.511111 | 0.430000 | -0.081111 | 43/55 | 0.780303/0.757576 |
| 2 | 160 | 0.444375 | 0.455000 | +0.010625 | 45/41 | 0.688000/0.680000 |
| 3 | 186 | 0.436559 | 0.453226 | +0.016667 | 62/57 | 0.611940/0.611940 |
| 4 | 157 | 0.405732 | 0.422293 | +0.016561 | 45/35 | 0.708333/0.716667 |

Physical-room bootstrap: 10,000 paired draws, seed 20261119; pooled row/object weighting and percentile 95% intervals.
primary: gap-MRA gain CI [-0.059475, +0.001404]; choice gain CI [-0.028192, +0.015408]; 200 rooms.
all_training: gap-MRA gain CI [-0.046050, +0.010883]; choice gain CI [-0.028188, +0.012229]; 219 rooms.
Commands: `bash run.sh selrefit2.py prepare` produced counts/folds; `bash run.sh selrefit2.py train` fitted both arms;
`bash run.sh selrefit2.py score` produced per-capture distances/choices; `bash run.sh finalize2.py` produced every reported aggregate, bootstrap interval, and decision.
Choice accuracy covers candidate-bearing table objects; bootstrap sums retain rooms with zero distance rows. The JSON includes all fold metrics, coefficients, and input hashes.
Validation: `bash run.sh verify2.py` checks room separation, fold normalization, paired coverage, printed distances, refusal scoring, and all output input hashes.
Archive: `bash run.sh package.py` produces out/sb_selrefit2.tar and out/sb_selrefit2.tar.sha256.
Boundary read: not requested because the frozen rule did not pass.
Table coverage (`bash run.sh finalize2.py`): 30 shared tables are empty in both arms; 185 captures supply 648 training objects per arm. Empty tables supply no fit examples under the fixed recipe.
