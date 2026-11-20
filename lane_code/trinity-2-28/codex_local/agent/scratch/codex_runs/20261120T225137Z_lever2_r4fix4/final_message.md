Implemented all four fixes. **33 tests pass**, including forced early failures in both modes through real fetch.

- Both streams are captured to opaque files; every return includes bounded hex tails.
- Aggregate `/project` budget: **44 MB**. Delivery plus extraction: **19,496,748 bytes**. Staging uses ext4 job_tmp.
- GPU request: **200G**; estimated peak **187 GB** (96 + 71 + 20 GB), unmeasured. Guard stops at **180 GiB**. Returns include host/GPU memory telemetry.
- CPU/GPU submission parity is tested; necessary differences are documented.

FROZEN unchanged. Manifests agree. [Report](/scratch/jjyeung/orch_n30/lever1_c/r4kit/REPORT.md).

Token: `e71c940a6b283`  
[Delivery](/scratch/jjyeung/orch_n30/lever1_c/r4kit/out/delivery.tgz): **4,247,712 bytes**  
SHA-256: `4662e14cbefe9d149a3cdb7ca58bd3ff8f9030ae5e6ff98b96bc53867b67f989`