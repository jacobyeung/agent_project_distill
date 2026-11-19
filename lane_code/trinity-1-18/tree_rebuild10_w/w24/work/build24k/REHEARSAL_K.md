Run `nice -n 10 bash work/build24k/go_rehearsal_k.sh` outside the sandbox. This script has not been run.
The builder reads rehearsal3 (or rehearsal2 if rehearsal3 is absent), preserves those inputs, and creates work/build24k/rehearsal_k plus a resealed fixture copy of the 24k GO kit.
The fixture executes a.py r, reviews its exact native selection digest for this fixture, then executes a.py q at the same fresh logical paths. Only production P-row equality is omitted in the synthetic routing pass.
The native q path must produce q/host.json and RESULT.json.host_receipt. h.py consumes that pin directly. No fixture_gates.py or synthetic host writer is called. The only attached host/review receipt is the fixture review.
The tiny model/store/frame-host boundary and zero-GPU trainer authorization remain explicit. The fixture uses four gloo ranks, two threads per rank, a 19-GB aggregate RSS guard, and a fresh optimizer.
Training uses stop_after_step=6; the boundary sets milestone 2 and the step-4 budget-stop export, one-second checkpoint spacing, a long fresh budget and an expired budget phase. The exact effective recipe is recorded per rank. It checks step 1, milestone export/copy, timed checkpoint, budget stop, and resume for one step.
The checker additionally verifies the native host pin. The fixture records every executed stage and refuses any nonzero return without a retry.
