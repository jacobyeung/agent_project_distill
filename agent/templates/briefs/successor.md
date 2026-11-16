
## Role
You continue the work of lane $pred_lane. Its STATUS.md is the state: resume from it, and never redo a step it marks done. Read the newest `*_ORCH_*` events in the events folder before acting; a ruling there wins over the predecessor's brief.

## Predecessor
- Brief: `$pred_brief`
- STATUS: `$pred_status`
- Rotate event: $pred_rotate

## Folders the predecessor used
$pred_folders

## Next step, from the predecessor's STATUS (verbatim)
$pred_next

## Task: the predecessor's Do, unchanged unless the orchestrator edits it below
$pred_do

## Why
$why

## Do (orchestrator's additions)
$do

## Done when
The predecessor's task is done and one RESULT event says so, or your session limit is near and the RESULT `rotate` and STATUS.md let the next successor resume.
