Fixed and resealed.

- Vendor launcher uses durable paths; exhaustive scan found no discard flags or redirections.
- Startup, supervisor, and scheduler output use capped sinks with truncation markers. Overflow tests passed at 64/128 MiB.
- **59 tests passed**; [VALIDATION.json](/scratch/jjyeung/orch_n30/lever1_c/r1/out/VALIDATION.json) records `passed=true` for the exact SHA. Slurm was simulated.
- Budget: **48 MB `/project`**; workspace **4.95/10 GB**. Allocation forecast: **38.75/50 minutes**.

Token: `a6f198d3c7b20`  
Delivery: **3,715,339 bytes**  
SHA256: `2d65f9aa6aef254c4cd514713984a0a10162dbbd91a5eef40b7a00854d57e6b9`