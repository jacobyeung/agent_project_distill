# Native pilot 169501: why the parity probe made no camera call

## 1. Cause (confidence high, about 90%)
The probe's question lies outside the leg's training distribution, so the leg treats it as a direct question: it closes its think block at once and writes free-form tags with a literal `<` (id 27), so it never samples an opener id and no call opens. The gate also accepts only `<pose ` calls, which this lineage never makes; the leg's camera calls are `<move from=i to=j>` and `<turn from=i to=j>`, and the reader already detects and serves both.

## 2. Evidence
- **The 33 ids** (PARITY_DECODE.json). Pieces come from the same ids in the prompt and in the plain read: 198 `\n`, 248069 `</think>`, 271 `\n\n`, 27 `<`, 3899 ` frame`, 28 `=`, 16 `1`, 29 `>`, 198, 27, 2404 ` turn`, 28, 15 `0`, 29, 198, 27, 15105 ` zoom`, 28, 16, 13 `.`, 15, 15, 15, 29, 198, 510 `</`, 2404, 29, 198, 510, 3899, 29, 248046 `<|im_end|>`. No generated id is at or above 248070, and none decodes to an empty string. P1 matched argmax 33/33 and the full sequence, so this is the model's real greedy output under the native runtime.
- **The job's tokenizer has the openers.** The probe prompt (GPU_PARITY P3 prompt_ids) encodes the question's `<pose` as 248079. The openers are `<depth_at` 248077, `<move` 248078, `<pose` 248079, `<turn` 248080 and `<box_3d` 248081 (carrier_c1_routing.py:38, 652-665).
- **Where calls are detected.** A head call opens only when the model samples an opener id: `if token in self.state.openers` (student_pilot/carrier_c1_batch_decode.py:120). Ground, gap and calculator calls are matched in the decoded text (lines 127-133; GROUND_TAIL and GAP_TAIL at carrier_c1_decode.py:34-37). The served head forms are depth_at, move, pose and turn (carrier_c1_decode.py:28-33). The gate is nomdg.py:283, `c['call'].startswith('<pose ')`. The sealed tree's own gate also accepts `<move ` and `<turn ` head calls (evalpath/parity.py:297).
- **The training rows' syntax.** I sampled 1,500 rows by primary key from each local DB. The routing DB (5e1d07a4/r16, the leg's camera DB) teaches `<move from=i to=j>` for displacement and direction and `<turn from=i to=j>` for rotation, inside `<think>`. None of the sampled rows in any DB contains `<pose`, `frame=1>` or "Read the camera pose". The VQA DB (vxm_m4) and the pointing DB contain no head calls. The pose-stream rows (a2v3, "Describe this scene.") have exactly the target `<think>\n\n</think>\n\n`, the empty-think form the probe produced.
- **The parent never ran this probe on real weights.** NATIVE_CPU_SMOKE.json used a tiny random Qwen3.5 with controlled token choices (an 85-token prompt with forced `<depth_at …>` and `<move from=2 to=9>`). It tested plumbing, not learned behaviour. The reader inherited the probe from routed.py:133 (the MDG reader) and evalpath/routed_types.py:29.
- **The leg on real items** (plain step-200 read bffa0d6ef, same export baccafbf, with token_ids stored):
  - All 450 camera items emit an opener id inside think: 248078 `<move` on 300/300 displacement and direction items, and 248080 `<turn` on 150/150 rotation items. On 449/450 the first call carries the question's frame pair.
  - The vLLM tokenizer lacks the openers and decodes them to an empty string. That is why that read shows `  from=18 to=23>`; the spaced text seen in the brief comes from that read, not from this pilot.
  - Absolute distance: the first call is `<ground obj="X" mode="box">` on 149/150 items, and every named operand is one of the scripted operands (150/150).
  - Room size: the first call is `<ground mode="room">` on 36/36 items.
  - Over all 1,975 items, the leg never emits `<pose` (248079).

## 3. What it means for the scored read (636 items)
- **Known.** Real items make calls that the reader serves. All 450 camera items should open `<move`/`<turn` by id, which HEAD_FORMS parses and which the scripted arm also uses (perception.py:292-293). All 186 distance and room items open with a text form that GROUND_TAIL detects and the scripted arm uses (perception.py:267-286).
- **Not known until a GPU decode:**
  - whether the native load emits the same ids as vLLM on real items (no native real-item decode exists yet);
  - what the leg does after an injected response: its later ground and gap calls, and its answers;
  - the call and version error counts (R1 requires zero) and the learned call rate (at least 95%);
  - whether the mask cache covers the leg's later ground operands;
  - seconds per item.
- The plain read's caps (122/150 distance and 34/36 room items hit the cap) do not predict the native read. Those runs looped because no response ever came back.

## 4. Smallest correct fix
- **File:** nomdg.py `run`, lines 271-285, plus test_nomdg.py. Make three changes:
