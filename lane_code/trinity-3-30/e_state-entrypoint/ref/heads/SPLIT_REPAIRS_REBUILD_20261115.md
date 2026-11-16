# SPLIT repair and exposure top-up rounds rebuilt on trinity-0-13 (2026-11-15)

**Status:** five bundles sealed and CPU-proved (r3162 to r3166); no launch yet. Launcher sheet:
`agent/scratch/devin_lanes/split_repairs_1115/out/NEEDS_LAUNCHER_SPLIT_REPAIRS.md`.

## Question
How do we rerun the SAM3-fault and race-exposed questions of the printed SPLIT cells (Gemini 3.1 Pro and 3.8 Flash,
VSIBench-500 and ReVSI-999) after trinity-3-3, which held every parent package, run and merged cell on RAM disk, went down?

## Answer
Rebuild on trinity-0-13 from durable sources only. Each round is a new bundle under
`/scratch/jjyeung/split_repairs_1115/bundle_r<N>_v2`: the parent package with the round identity and serialised SAM3
client requests, the r2957 service with the NMS lock, the connected-components lock and one-request-at-a-time
handling, the frozen question list, and a controller that attaches to a launcher-owned service.

## Reasons and evidence
- **Parent bundles** came from the 32 MB delivery archive on NFS (SHA-256 `c993a250...`); both bundle seals verified.
- **Parent cells** came from the four registered bank archives (2.19 GB, governed copies). `restore_parents.py` writes
  receipts, raw traces, scoring files and source packages back to the absolute paths the receipts name, so every pin
  verifies with unchanged code. Restored scores equal the registry: 77.98, 62.64, 72.71, 82.63.
- **The lock is the live-proven code.** The rebuilt service entrypoint and the three lock modules are byte-identical
  to the r3083 service whose pilot passed live (`proofs/SERVICE_BYTE_IDENTITY.json` in each bundle).
- **Constants.** 1,185 package constants per bundle, each mapped to a parent constant; zero new origin rows.
- **Inputs.** Only the selected scenes are staged (58 ReVSI, 18 VSIBench); every file keeps the parent's SHA-256 pin.
  VSIBench files were found on the node by hash; ReVSI files came from NFS in two governed streams (2.6 GB).
- **Proof.** Each bundle ran its real controller, namespaces, sealed service entry and locks, native episodes,
  settlement, merge onto the parent, official scorer and bank preparation on CPU, with only the provider transport
  and the video model mocked: 88 episodes and 147 recorded video calls in total.

## Options considered and rejected
