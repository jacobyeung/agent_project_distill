No C8r, V1c, build R, offkit, or b04 source file was modified. The following entries describe this build's adapters and the inherited paths they exclude.

| Source location | Build N location | Difference |
|---|---|---|
| C8r `native/out2/nomdg.py:505` | `offnative/readers.py:32` | The harness adapter invokes model generation and never constructs the scripted arm. |
| C8r `native/out2/nomdg.py:506` | `offnative/readers.py:39` | The adapter does not invoke `perception.scripted`. |
| C8r `native/out2/perception.py:320` | `offnative/scoring.py:19` | The scorer receives raw model text without `script_answer` or its unit conversion at line 352. |
| C8r `native/out2/nomdg.py:301` | `offnative/scoring.py:24` | The adapter imports the accepted official ReVSI scorer instead of using the dev-S1 score-record builder. |
| V1c `code/engine.py:52` | `offnative/readers.py:39` | The intended harness adapter has no V1c `camera_only` scope; its production context and original call serving remain unexecuted. |
| V1c `code/proof.py:7` | `offnative/proof.py:19` | The equality signature compares token IDs, full UTF-8 model text, call text, and response bytes without a separate final-answer transform. |
| V1c `code/proof.py:97` | `offnative/proof.py:6` | The fixed proof selection uses five camera and five absolute-distance keys ordered by SHA256. |
| V1c `code/budget.py:15` | `offnative/worker.py:55` | The worker imports the unchanged deadline budget and its 600-second return reserve. |
| Accepted evaluator `media.py:15` | `offnative/frames.py:13` | The adapter passes the bound count to `sample_video` and the count and layout to `frame_list`. |
| Build R `kit/rebind.py:154` | `offnative/cli.py:99` | The transfer adapter delegates to build R's governed-transfer function; it does not create a second IO policy. |
| Build R `kit/revsi/launcher/orchard_stage.py:47` | `offnative/staging.py:6` | The fixture stager uses the reviewed archive reader with links disabled and a bounded local destination. |

The C8r answer-conversion path is excluded by the call graph, not by editing its source. `test_answer_bytes_reach_official_scorer` spies on the actual scorer call and checks exact UTF-8 equality, including whitespace and a unit suffix. The test confirms that the wrapper does not change the model's answer.

The CPU harness fixture uses b04's decode loop, not C8r's real inference stack. Therefore the excluded scripted path and intended harness call graph are reviewable in source, but this build does not claim production C8r parity. The production cache builder, freeze-value application, original-export proof loader, and outer process watchdog still require implementation.
