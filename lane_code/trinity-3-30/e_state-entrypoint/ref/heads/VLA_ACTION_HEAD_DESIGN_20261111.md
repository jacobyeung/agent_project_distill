# VLA action heads, own-heads arms and VLA tests for the 9B student (design lane vla_design, 2026-11-11)

Status: DESIGN. This lane read files and the web and wrote only this record, its schema (`/scratch/jjyeung/orch_cd/vla_design_review/VLA_SCHEMA.md`) and its INDEX row. Labels: FACT = measured, with the file named; E = estimate, with the arithmetic; HYP = hypothesis; UNVERIFIED = no primary source confirmed it. The schema (`vla_schema_v2`) is the binding cross-lane contract; where this record and the schema differ, the schema wins. `schema_examples.py` beside the schema computes every worked example.

## Question
On 2026-11-11 the user asked: "how's the design for the model? did you design the vla tests? how would we add on the action head? a diffusion head? is all the code developed? we should preemptively develop all this code and test it! so when it's time to actually run, we don't need to debug and waste time!" Later that morning the user added: "i wonder if we also need to look at dynamic scenes for the VLA - interesting to study" and "my current hope and vision is to use pose and depth to answer where things are in the reasoning trace." At about 05:05 PT the user asked how other VLAs, π0.5 in particular, handle different robot bodies, and whether each one is fine-tuned separately. The user also set the order of work: the spatial understanding must first work very accurately.

This record answers seven questions:
1. How does an action head attach to the 9B student, as regression, flow or tokens, behind one interface?
2. Which arm can only our model run, and what does it need from our code?
3. Which comparisons support which claim, under the no-controls ruling?
4. Which VLA tests run, in what order and at what cost?
5. What must the build lanes implement and test before any GPU?
6. Do dynamic scenes matter?
7. How do published VLAs handle several robot bodies?

## Answer
- **Recommendation:** every build lane implements `VLA_SCHEMA.md`. The runs fall into two kinds:
  - Shake-downs on today's checkpoint (CP1 m200) prove the kits and support no claim.
  - The decisive runs use the final spatial student. Test L compares U1 with B1 on LIBERO-Spatial at 5 demonstrations per task. Test N compares NU with N1 on R2R-CE at 10% of the training data.
  - The base references B0 and N0 are the single open question (§9). Every control-only training run, B0 and N0 included, stays disabled until the user says yes to it; a method arm's win does not authorise one.
- **Code today (FACT, lane STATUS files, 12:35-12:49Z):** nothing VLA-specific has run on a GPU yet.
  - vla_heads passes its CPU suites on interface v2.
  - vla_nav's runner passes 36 CPU tests and scored the visually blind priors on all 1,839 val-unseen episodes.
  - vla_libero restored the StarVLA stack on Orchard; its resume is exact on a tiny Qwen3.5, and its first GPU test is queued.
  - vla_where and dyn_probe are building.
- **Head:** one `ActionHead` interface makes the head type a config value.
  - (a), the default, is StarVLA's QwenOFT L1 regression head (about 0.17B parameters, the October pilot's head), with zero-initialised proprio and where inputs.
  - (b) is a flow-matching expert that reads LM taps 16 and the final layer by cross-attention, with a detached backbone and a FAST token loss.
  - (c) is tokens written by the LM.
