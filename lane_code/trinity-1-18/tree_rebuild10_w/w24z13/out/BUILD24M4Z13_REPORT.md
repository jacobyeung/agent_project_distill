jn4.sh SHA-256 `80c80de72e9909f7567844ad9d14ba069b99b5de2aedac03439f7c1972eead83`; 15 local cases PASS; source kit unchanged. ORCH ruling file absent; no remote submission.
| Test | jn3 → jn4 status; final publishes | Evidence under work/build24m4z13/ |
|---|---|---|
| Zero / two GPUs | 3 → 3; 0 → 1; refusal absent → present | a2/g0_{3,4}/ and a2/g2_{3,4}/events.jsonl, result.json |
| Seal E13 / missing DONE.json E10 | 1 → 1; 0 → 1; refusal absent → present | a2/s_{3,4}/ and a2/r_{3,4}/events.jsonl, result.json |
| Child / TERM / USR1 | 23 / 37 / 38 unchanged; 1 → 1 | a2/{c,t,u}_{3,4}/events.jsonl, result.json; a2/checks.log |
| Publisher failure | status 3 retained; one attempt | a2/p_4/; tests2.log, a2/results.json. Failed setup outputs: input.log (shell quoting), tests.log (harness TypeError). Actual tails: X/o/<job>/j2.{log,err}; details: a2/NOTES.txt. |
