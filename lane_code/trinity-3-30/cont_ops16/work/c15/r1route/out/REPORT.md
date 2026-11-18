# R1 step-200 read packages

A: [b1/REPORT.md](b1/REPORT.md), token `d72cdcff1e22a`, 636 dev-S1 items.

B: [b2/REPORT.md](b2/REPORT.md), token `b9188e9225a85`, 134 room items (36 dev-S1 + 98 R0-dev).

Both packages use candidates_argmax and share one four-part export pull. Their real-preparation fill proofs and local CPU tests pass. They await review, Orchard fill, allocated CPU checks, and sequential one-GPU reads. The baseline self-pairing has zero differences and zero 95%/99.29% intervals. Start with each package's OPERATIONS_R1ROUTE.md; place both, fill A, then fill B from A's verified cache.
