Fixed and rebuilt. Nothing resubmitted.

- **Cause:** unchecked subprocess failure plus discarded stderr explains the missing diagnostics. The actual death remains unresolved. The 193 GiB tmpfs hypothesis conflicts with the existing 200 GiB free-space check. [Evidence and file:line analysis](DEBUG.md).
- **Fixes:** metadata-only head validation, ext4-only staging, 32 GiB CPU address-space cap, and worker supervision preserving code/signal, stage, peak RSS and bounded hex-packed stderr. Production memory remains unmeasured.
- **Tests:** all 27 pass. SIGKILL returns `-9`, signal `9`, stage and stderr through real fetch in both modes. SIGTERM, hard exit and timeout also pass.
- **Token:** `e71c940a6b283`. FROZEN unchanged; delivery documents and hashes agree.

[Delivery](out/delivery.tgz): **4,242,557 bytes**  
SHA-256: `38af33d6461e4a46ddc8cebdc1876466bb8a3d555bd492cebfe235a4284d3532`