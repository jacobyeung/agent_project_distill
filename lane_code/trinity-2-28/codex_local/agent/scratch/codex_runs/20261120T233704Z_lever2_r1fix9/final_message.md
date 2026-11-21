Fixed: submission uses pre-created durable files, no FIFO or collector. The sealed batch enforces 512 KiB file caps; traps and production fetch preserve failure causes. Both submission layers propagate errors.

All **64 tests + two import checks passed**, including sink startup failure, premature exit, overflow and first-line exceptions. [VALIDATION.json](/scratch/jjyeung/orch_n30/lever1_c/r1/out/VALIDATION.json) records `passed=true` for the exact delivery.

- `/project` budget: **48,000,000 bytes**
- Token: **a6f198d3c7b20**
- Delivery: **3,736,824 bytes**
- SHA256: `7e80b0e550709952985e80a9a148f5ff9f134fb60a9ae61e3bf7586fef6cdf68`

PLACE, REPORT and checksums agree. No live submission ran.