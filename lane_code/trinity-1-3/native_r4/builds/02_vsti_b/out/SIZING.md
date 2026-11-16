The planning rates below are the operator-supplied measurements from job 170056. No `/data2` source was read. These are projections, not measurements of this build.

| Phase | Projection in seconds | Basis |
|---|---:|---|
| Staging and one load | about 1,800 | 170056, excluding geometry |
| Pose tower | 1,181.8 | 311 scenes × 3.8 s at 32 frames; about 10 GB peak |
| Own scale/gravity | 311 × g | g is unmeasured; PHASES.json records this phase |
| Proof geometry | p × g | p is the number of distinct selected captures; original conditioning questions |
| Proof decode and repeat | 159.8–879.8 | Twice (3 × 6.0 + 3 × 7.3 + 4 × [10,100]); rotation is unmeasured, so this range is an assumption |
| Read canary | 86.6–626.6 | 2 × 6.0 + 2 × 7.3 + 6 × [10,100] |
| Remaining camera items | 638.4 | 48 × 6.0 + 48 × 7.3 |
| Remaining other items | 3,440–34,400 | 344 × [10,100], unmeasured |
| Extra checkpoint restorations | L | Unmeasured; separate preparation, proof and read processes |
| Return reserve | 300 | Explicit scheduling allowance, not a measured transfer duration |

The measured-rate subtotal excluding scale/gravity, proof, additional restoration and return is 7,146.8–38,646.8 seconds. The upper estimate exceeds C8r's 21,600-second GPU cap. A complete first job is therefore not promised. The absolute deadline is also enforced across the GPU subprocesses. Staging consumes real time before the deadline but is outside the inherited GPU-phase counter.

`out/CANARY_KEYS.json` contains four camera and six other keys. Preserving those exact keys leaves 96 camera and 344 other items. The requested 90/350 remainder is inconsistent with that fixed canary; the kit preserves the keys.

The worker observes the duration of each complete item pair, including the scripted arm when present. It predicts the next item as 1.25 × the maximum duration observed for its type, with a floor of 6.0 seconds for displacement or 7.3 for direction. An unseen other type starts at 100 seconds. The canary receipt projects all remaining items with the same rule. It starts an item only if current time + prediction is at most deadline − 300 seconds. This rule is conservative relative to observations; it cannot guarantee an unseen slow item finishes before the deadline. The subprocess timeout enforces the bound and the journal preserves the last committed item pair.
