# Carry kit: CPU-validated, bars-first GPU launch

The patched kit passes 109 tests and all nine stub parity checks. The independent verdict and exact commands are in `out/CACHK_VERDICT.md` and `out/check/EVIDENCE.json`. No GPU result is available; the producer's full-capture CPU check remains PARTIAL.

The decision population contains 204 captures and 1,012 rows. The report also shows 209 captures and 1,037 rows. The frozen bars retain SHA256 `edff8724b27328f6874b4adb0dd93727cc70fdfd4ddf2fb301cf572a46ceaaf4`; `BARS_AMENDMENT.json` registers positive-score empty masks as incorrect added members and identifies the decision population.

Scoring, summary and launch entry points refuse missing or changed frozen bars before writing. Scoring also refuses existing per-item output files. Use fresh scoring destinations. The launcher checks before creating logs or directories; killed passes cannot resume.

Stage the 20 items in `STAGING.json` at their recorded absolute paths: 14,924,717,613 bytes (14.925 GB). They include the local environment, model/source, frames, phrase provenance, seed metadata, population and pinned vnice scripts. The launcher sets `PYTHONNOUSERSITE=1`; set it for CPU checks too.

The GPU pass needs one native-bf16 card with at least 24e9 bytes, two occupancy readings 300 seconds apart at no more than 1,024 MiB, and local vnice. The cumulative budget is two hours. Assumed costs are 0.80031 GPU-h for the decision arm and 2.45160 GPU-h for all arms; the ten-capture receipt replaces these assumptions. The estimated 7.410 GB footprint supports a 24 GB trial but is not a measured CUDA peak.

`out/GUARD.patch` applies to the producer's kit and reproduces the patched code byte for byte. Launch with `bash kit_v2/launch_gpu.sh`; run CPU pricing and summary afterward with `PYTHONNOUSERSITE=1 bash kit_v2/post_gpu.sh`. GPU carry bars remain MISSING until valid complete outputs exist.
