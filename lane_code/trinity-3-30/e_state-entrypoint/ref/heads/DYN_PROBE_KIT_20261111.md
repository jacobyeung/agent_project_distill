# Dynamic-scene geometry probe

## Question

Does scene motion degrade the student's camera pose and depth enough to justify robust-pose or dynamic training, and does the frozen G3T teacher share the failure?

## Answer

The kit measures this without training. It compares the student's own T0 heads, its frozen G3T tower, a local π3 hook, and an identity-pose/median-depth baseline. CPU tests use known synthetic errors and controlled-noise stubs. They cannot answer whether any real model degrades on dynamic scenes.

## Evidence

The experiment follows Stage 0, lines 85–90 of `/data2/jjyeung/agent_project_data/distill_design/DYNAMIC_SCENES_VLA_PLAN_20261108.md`. Model entry points come from the named `integ_v3/work/tree/student_pilot` source files. The inventory identifies the T0 m800 full export and heads; its bundle configuration specifies the duplicate-frame layout.

`out/DATA.md` records complete archives, byte sizes and measured SHA-256 hashes. `out/ENVIRONMENT.json` records CPU dependencies. `out/RUN_CARD.md` contains commands, metrics, bootstrap intervals and the decision rule. `out/tests_cpu.log` records 47 passing CPU tests in 148.26 seconds. The native T0 prompt builds on CPU with 32 viewpoint carriers and 64 RGB inputs; the native G3T model imports and builds 32×3×518×518 CPU inputs. The readout labels every controlled-noise result as a stub result.

All 12 archives pass serial CPU ingestion. Bonn's static control marks 0.0754% of assessable pixels as moving, with 60.6% assessable coverage. The TUM static control's four tested clips have residual moving fractions between 0.00009% and 0.0033%, with approximately 69.5–72.3% assessable pixels. This validates the empty-mask check on those clips. It does not establish moving-object recall on dynamic clips.

## Options considered and rejected

- Training before measuring the failure would spend GPUs before the pre-registered gate can be evaluated.
- Treating `walking_static` as a static control would mislabel moving people. The kit uses `long_office_household` as the TUM static control and keeps sitting clips in a separate low-motion stratum.
- The generic 16-anchor `HeadSession` API cannot represent the T0 bundle's 32 viewpoint outputs. The T0 adapter uses `CarrierC1.readout` and preserves its native duplicate layout.
- Fitting a teacher scale to sensor depth would leak evaluation GT. The native G3T scale uses the student's predicted depth, with its dependence recorded. A raw-units option provides an independent scale diagnostic.
- Expanding all archives would consume the storage allowance. The loader retains full archives and caches only the selected frames and their consecutive neighbours.
- Treating residual masks as semantic motion GT would overstate the evidence. The kit records mask coverage and rejects static controls that fail the emptiness or coverage checks.

## Risks and how we would notice

- Consecutive-frame residuals can miss textureless or slow motion. Very few moving pixels, or disagreement with labelled moving-object interiors, would reveal poor recall. Split depth scores are conditional on this conservative mask.
