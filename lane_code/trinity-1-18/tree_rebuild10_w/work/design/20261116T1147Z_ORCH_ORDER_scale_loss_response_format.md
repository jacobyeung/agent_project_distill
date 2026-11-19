# ORCH ORDER (from NEXT_QUEUE_20261116 section 3, adopted): scale-head loss and frozen response format in the next-leg kits
- Supervise the pose head's scale token (weight_scale > 0, value from NEXT_QUEUE_20261116.md section 3 or the brief 04 design) so metric scale can come from the model, not tower_scale_rule.json.
- Freeze the <tool_response> text format (fields, units, number formatting) as one versioned spec shared by rows, trainer and every reader; a test checks rows and reader against it.
- Claim A2 only through a reader that passes lane b03_e2etest's acceptance test.
- Room size: the next leg trains room DIRECT (A0) and claims neither form until a passing reader measures both.
