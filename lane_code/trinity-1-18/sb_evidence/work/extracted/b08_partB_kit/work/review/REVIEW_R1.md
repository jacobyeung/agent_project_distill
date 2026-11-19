VERDICT: NO-GO

Findings below use the supplied eligible-scene fixture, matching masks, and provenance unless stated otherwise. Assignment counterexamples were reproduced in memory; sealed-validator incompatibilities follow directly from its checks.

1. **High — `code/headrows/assign.py:98`: options are compared by first character.**  
   GT `"B"` with prediction `"Banana"` or `"B but actually C"` produces `head`. GT and prediction both `None` also produce `head`. These are not exact option-letter matches.

2. **High — `code/headrows/assign.py:85`, `:97`: floating-point conversion breaks exact counting.**  
   GT `"3"` with prediction `"3.0000000000000001"` produces `head`. Likewise, GT `"9007199254740992"` accepts `"9007199254740993"`. Distinct answers collapse to the same float.

3. **High — `code/headrows/assign.py:105`: mask verification does not require every operand’s GT IDs.**  
   With `operands=["chair","table"]`, `gt_instances={"chair":["chair:3"]}`, and identical `selected`, a correct option prediction produces `head`. The missing table GT never gets checked, contrary to the required direct assignment.

4. **High — `code/headrows/assign.py:69`, `:76`: eligibility discards identifiers that the sealed checker supports.**  
   Using the fixture scene `scannet/scene0232_02`, setting `room="d1/scene0155"` remains eligible, although the sealed checker reports a dev match. Setting `room` or `physical_group` to `"scannet/scene0011_00"` similarly bypasses a benchmark match.  
   Also, `dataset="scannet", scene="arkitscenes/41069053"` remains eligible because assignment removes the scene’s dataset prefix; the ARKitScenes identifier is dev-excluded. These inconsistencies are admitted instead of refused.

5. **High — `code/headrows/assign.py:115`, `:119`: status classification admits missing statuses and false recoveries.**  
   Removing `status` produces `head`. `"no answer required; success"` produces `recovery`, as does `"chair: not seen yesterday; ok now"`. These are not verified real runtime failures; unknown statuses must drop.

6. **High — `code/headrows/assign.py:133`: provenance requires only truthiness.**  
   `pipeline_sha256="not-a-sha256"` produces `head`. The row therefore passes without SHA-256 provenance.

7. **High — `code/headrows/assign.py:166`: the room cap applies to raw strings, not physical rooms.**  
   Four counting head rows with `room="d1/scene0232"` plus four with `room="scannet/scene0232"` select all eight. These aliases identify one room, exceeding four per `(type, room, form)`.  
   Separately, `select(..., cap=2001)` selects 2,001 rows; the public override does not enforce the specification’s maximum.

8. **Medium — `code/headrows/assign.py:94`: valid numeric boundary answers become direct rows.**  
   GT `"1"` and prediction `"0.85"` return false because floating-point subtraction exceeds the computed threshold. GT `"0"` and prediction `"0"` also return false. Both satisfy the stated tolerance; zero has no stated exclusion.

9. **High — `code/headrows/assign.py:143`; sealed `student_pilot/ground_rows.py:100`: assignment and packing disagree on count answers.**  
   Prediction `"3.0"` against GT `"3"` produces `head`, but the sealed validator requires string equality for counting and rejects that answer pair. Thus an assigned head row is not necessarily usable by the advertised packing/validation path.

10. **High — `code/headrows/assign.py:124`; sealed `student_pilot/ground_rows.py:49`, `:58`, `:81`: assignment does not establish a valid, matching Session record.**  
    The minimal test response receives `head` without events, suffix, or the required Session fields. Adding `printed="<answer>4</answer>"` while keeping `pred="3"` also receives `head`; assignment never binds its correctness check to the text that would be copied.  
    Packing requires the event/suffix record, and validation additionally requires `gt_agrees=True`, false `not_seen`, and `training_admitted=False`. Assignment checks none of these prerequisites.

Checked and found sound:

- All three authorization-file hashes match their pins.
- The 12 tests that require no writes pass. The end-to-end test could not run because it requires temporary files.
- Tested ScanNet++, ScanNetPP, ScanNetPPv2, and ARKitScenes dataset aliases correctly exclude known scenes when identifiers are consistent.
- Unsupported datasets fail closed; ordinary unknown statuses and the exact listed operator-fault strings drop.
- Wrong instance sets, extra operands, empty GT sets, and ordinary `unmatched` results fail mask verification. Duplicate IDs correctly collapse under the specified set semantics.
- Mask tests confirm the stated IoU threshold and rejection of unknown frames and mismatched shapes.
- With canonical room strings and default limits, minority-family selection, per-form caps, recovery inclusion, and ordering across reversed input are correct.