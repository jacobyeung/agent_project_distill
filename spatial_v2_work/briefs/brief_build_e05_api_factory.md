# Lane: build_e05_api_factory (Build & Smoke-Test Unlimited Gemini API Spatial/4D Trace Factory Pilot-0)

## Mission
Exploit our **unlimited Google Gemini API key (`gemini-4-neon`, `gemini-4-carbon`, `gemini-4-argon`, `gemini-4-hydrogen`, `gemini-3.8-flash`)** starting TODAY!
Build and live-smoke-test a clean, fast, leak-free **Pilot-0 API Data Factory** under `/scratch/jjyeung/orch_home_distill/e05_api_factory/` that takes ALREADY-LOCAL training scenes/frames + 3D geometry on `trinity-2-28:/scratch` (ZERO heavy NFS reads!) and generates verified, prior-breaking spatial training rows with:
1. **Hard Room-Keyed Exclusion Guard (`BENCH v2` + `R0-dev` + `K1-heldout` + `ReSTI ScanNet`):** Refuses to emit ANY row whose room/scene/venue matches any held-out or benchmark exclusion list!
2. **Deterministic 3D Geometry Ground-Truth Solver + Recompute Gate:** Every numeric answer (metric distance, oriented size, gravity-leveled `(r, bearing_deg, dz)`, facing-away / opposite-direction twins, camera motion, large-set counts `>=5`, small objects `<30 cm`, multi-instance disambiguation) is computed & verified by deterministic Python math (`0` arithmetic errors!).
3. **Gemini API Inline-JPEG Native Labeling & Epistemic Trace Authoring (`Neon`/`Carbon`/`Argon`):**
   - Uses direct `https://generativelanguage.googleapis.com/v1beta/models/...` with `GOOGLE_API_KEY` and **inline base64 JPEGs** (ZERO Gemini File API storage bloat — stays well under the 20.5 GB cap!).
   - Implements the **Prior-Breaker + Epistemic Recovery Trace Generator**:
     - Takes real scene frames + 3D GT + simulated/real OOF head failure cases (`UNSEEN`, `LOW_PARALLAX`, `MULTI_SLOT`, `POSE_UNSTABLE`, wording paraphrases across 40+ templates & 4 units `{m, cm, ft, in}`),
     - Authors concise (`<250`-token), zero-guessing SPLIT-style grounded CoT + `GeoAPI-v2` recovery traces with `Carbon`/`Neon`,
     - Cross-verifies visual visibility & referent unambiguity with an independent `Argon`+`Carbon` agreement gate (`>=96%` precision)!
4. **Live End-to-End Smoke Run (20–50 Real Verified Rows Tonight!):** Run a live 20–50 row Pilot-0 smoke batch against real Gemini API (`carbon` + `argon` / `neon`) on strictly train-only scenes already on `trinity-2-28:/scratch` (or verified local `k1_frames` train split, NEVER held-out/val/bench rooms!), verify 100% pass on exclusion + math recompute + visual agreement, measure rows/min throughput and project 24h scale (`50K–100K` rows/day)!

## Ground-Truth Inputs to Read First (Exact Paths Only)
1. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_api_data_flywheel.md`
2. `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w2_split_internalization_rl.md`
3. `/data2/jjyeung/agent_project_data/distill_design/BENCH_SCENE_EXCLUSIONS_20261108.md` (exact exclusion list path!)
4. `/data2/jjyeung/agent_project_data/distill_design/GEMINI_NATIVE_LABELING_20261111.md` (native inline image-first format!)

## Hard Cluster, IO & Safety Rules (MANDATORY)
- Write ONLY under `/scratch/jjyeung/orch_home_distill/e05_api_factory/`.
- **ZERO DELETIONS** (`rm_guard`), **NO GIT COMMANDS**, **NO broad NFS scans** over `/home`/`/data*`.
- Check local frames on `trinity-2-28:/scratch` first (`ls -1 /scratch/jjyeung/k1_frames /scratch/jjyeung/k1 /scratch/jjyeung/n30_mirror/lever1` — fast local NVMe!).
- Respect Gemini API rate limits gracefully (exponential backoff on 429/503; default `gemini-4-carbon` + `gemini-4-argon`, optional `gemini-4-neon`). NEVER upload raw MP4s to File API.

## Deliverable
1. Complete runnable, unit-tested factory under `/scratch/jjyeung/orch_home_distill/e05_api_factory/` (`exclusions.py`, `geo_solver.py`, `gemini_client.py`, `pilot0_runner.py`, `tests/test_factory.py`) + live `pilot0_smoke.jsonl` (20–50 real verified rows!).
2. Crisp report (max ~160 lines) at `/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_e05_api_factory.md` showing: exclusion proof, 3 sample verified traces, live API throughput (`rows/min`, latency, 429/503 rate, agreement rate), and 1-command launch to scale Pilot-0 to `50,000` rows!

Print a concise <=18-line summary to stdout when done.
