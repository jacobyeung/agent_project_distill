The real CP1 journals merged successfully: all 1,525 tasks in ON16k, B2048 and B4096 passed the kit merge and parity gates. The primary stratum contains 1,375 tasks. The 150 routes lack released labels and remain in the own-GT unavailable view.

| Primary type | N | ON16k % | B2048 % | B4096 % | ON16k C/U/P | B2048 C/U/P | B4096 C/U/P |
|---|---:|---:|---:|---:|---:|---:|---:|
| object_abs_distance | 150 | 38.8667 | 38.8667 | 38.8667 | 0/0/0 | 0/0/0 | 0/0/0 |
| object_counting | 150 | 58.4000 | 58.4000 | 58.4000 | 4/4/4 | 0/0/0 | 0/0/0 |
| object_rel_direction_easy | 150 | 91.3333 | 91.3333 | 91.3333 | 0/0/0 | 0/0/0 | 0/0/0 |
| object_rel_direction_hard | 150 | 78.6667 | 78.6667 | 78.6667 | 0/0/0 | 0/0/0 | 0/0/0 |
| object_rel_direction_medium | 150 | 88.6667 | 88.6667 | 88.6667 | 0/0/0 | 0/0/0 | 0/0/0 |
| object_rel_distance | 150 | 72.0000 | 72.0000 | 72.0000 | 0/0/0 | 0/0/0 | 0/0/0 |
| object_size_estimation | 150 | 68.1333 | 68.1333 | 68.1333 | 0/0/0 | 0/0/0 | 0/0/0 |
| relative_count | 139 | 56.1151 | 59.7122 | 59.7122 | 10/10/10 | 0/0/0 | 0/0/0 |
| relative_size_object | 150 | 92.0000 | 92.0000 | 92.0000 | 0/0/0 | 0/0/0 | 0/0/0 |
| room_size_estimation | 36 | 55.5556 | 55.5556 | 55.5556 | 0/0/0 | 0/0/0 | 0/0/0 |
| route_planning | 0 | — | — | — | 0/0/0 | 0/0/0 | 0/0/0 |
| OVERALL | 1375 | 71.2800 | 71.6436 | 71.6436 | 14/14/14 | 0/0/0 | 0/0/0 |

C/U/P means capped / unanswered / unparsed. Counts overlap; each row still contributes once to the denominator. Scores are item-weighted means, not official VSI benchmark overall scores.

The two budget arms improve primary relative_count from 56.1151% to 59.7122%; all other primary per-type scores are identical. This raises primary overall from 71.2800% to 71.6436%. Both arms retain 139 relative_count items.

The original request binding remains `7b59641acde12c96517b601892e31646ccdea8670d9615177b17946208d461e9`. The exact kit archive remains `d27804f736545f7ebed6b55124b4bd215991695d96ed9106d82a142e91302aaa`. Source request and six source journal/receipt/parity files match their recorded SHA256 hashes after merge. No rebind, generation, kit edit, or GPU work occurred.

`merge_results/` contains all three row-level report exports, kit summaries, the original request, and merge receipts. `MERGE_RESULTS.json` includes primary per-type counts and full-stratum summaries. The full merged items are in `work/r5/real_cp1_final/results`.

The reviewed budget merger verified each continuation against its ON source, token IDs, forced close and receipts. B2048 contains 31 forced-close and 3 stopped-unclosed derivations; B4096 contains 29 forced-close and 3 stopped-unclosed derivations. Both arms have zero derivation errors over all 1,525 items.

No empirical f17 comparison is claimed. All paired checkpoint comparisons and pass-4 family checks in this delivery use synthetic journal answers.
