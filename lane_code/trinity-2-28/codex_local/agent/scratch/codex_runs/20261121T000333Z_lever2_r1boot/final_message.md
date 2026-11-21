Both CPU and GPU jobs now stage runtime/code, boot the real worker, check its import closure, write the receipt, then stage bulk. See [boot_order.py:39](/scratch/jjyeung/orch_n30/lever1_c/r1/boot_order.py:39) and [boot.py:51](/scratch/jjyeung/orch_n30/lever1_c/r1/runtime/boot.py:51).

All **72 tests and 2 import checks passed**. Missing-module failures returned authenticated tracebacks with **zero bulk bytes staged**.

Pre-boot inputs total **15,758,714,418 bytes**. Orchard timing remains unmeasured; local failure checks took 2.622–2.872 seconds.

Token remains `a6f198d3c7b20`. Delivery: **3,717,946 bytes**.

SHA256:
```text
8326c8ee3c46967f9b9228057b18681e33bed984220274105a0399c54cbf7de9
```