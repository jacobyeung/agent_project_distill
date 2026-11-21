Fixed: supervisor/sink exceptions now return nonzero and replace prior success receipts with authenticated FAILED returns containing the cause. This prevents success from hiding lost diagnostics.

All **67 tests passed**, including three successful-child/late-sink regressions through production fetch. `out/VALIDATION.json` records `passed=true` for this exact delivery.

- Token: `a6f198d3c7b20`
- Delivery: `out/delivery.tgz`
- Bytes: **3,737,273**
- SHA256: `9ac72506077fb4ca0ce24b4c691e076c748d6c9d9c2f6e67e71de821b0f42b0e`