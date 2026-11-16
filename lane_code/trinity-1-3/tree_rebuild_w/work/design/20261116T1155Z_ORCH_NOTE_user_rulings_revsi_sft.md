# ORCH NOTE (USER rulings ~12:00Z, bind every lane)
1. ReVSI first: rank analysis, error tables and reads by ReVSI (official999) from now on; its questions are answerable from the frames viewed. VSI-Bench stays a secondary check.
2. 64 frames is probably better than 32: design kits so frame count is a parameter (32 and 64), reads match the training layout, and state the cost of 64.
3. SFT first, RL later: the near-term goal is head routing that works under SFT on concrete ground-truth traces (the model calls the right head at the right point, the heads are accurate, the model uses their outputs). RL kits are built ahead, not run.
4. SAM 3 may be part of the checkpoint weights. Unit conversion and number formatting are done by the MODEL in its CoT; constants are fine, but no reader, wrapper or post-processor converts or reformats answers for it.
