# Stop-export attestation for Orchard job 169097

## Status

The local claim collector and stop publisher pass **22 test methods**. Evalx's confirmed consumer accepts the synthetic packet's step, claim, done marker and four-part transport. Its independent check also verifies all eight registered-step refusals at both entry points. ORCH closes the contract check and requires both sides to stay frozen until the final stop export. This confirmation does not admit a real stop packet or evaluation launch.

No native stop claim has been read or stop export published. The single claim-read allowance is unused. The numbered publisher, running production job, installed wrapper and end-of-allocation runbook are unchanged.

## Question and answer

How can the operator attest a final export whose optimizer step is absent from the registered milestone list?

Use the producer's selected stop object and its claim file. The producer can upload a directory named `mN` to `q8/8865619b/469ddece_mstop.tar`, `mstopB.tar` or `mstopC.tar`. The matching `gcs_469ddece_<stop-generation>.claim` contains exactly `mN\n`. The numeric step, stop generation and object name describe different parts of the identity; none substitutes for another.

The claim step, artifact step, trained-groups step and transport step must agree. The done marker names the selected object. Four distinct receipts must name its four parts, cover contiguous offsets and sum to the completed archive's byte count.

Registered steps **1, 50, 100, 200, 400, 600, 800 and 1000** use the unchanged numbered route, including when such a step is the final saved step. The stop route refuses those steps and numbered object names.

## Contract

The wrapper retains the fields of `orchard-export-transport-attestation-v1` and adds:

- Literal boolean `stop_export: true`.
- `stop_claim: {"path": "<absolute local mapping sidecar>", "sha256": "<sidecar SHA256>"}`.

The mapping sidecar has schema `orchard-stop-export-claim-v1` and fields `run`, `kit`, `archive_name`, integer `claim_step`, `artifact_sha256` and `claim`. The run is `469ddece`; the kit is `07ca49df`. The sealed producer's object prefix is `q8/8865619b/`, not the wrapper kit ID.

`claim` contains exactly `path`, `bytes`, `sha256` and `text`. Its path records the producer's source; the consumer does not reread that path. Its filename must match the selected stop generation. Its text must be canonical `mN\n`, with a positive size at most 64 bytes and a matching SHA256.

The operator verifies canonical artifact bytes against the native count and hash. Artifact identity also matches the admitted step-1 pin, and configuration SHA256 is `84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb`. Receipt reconstruction must match the producer log's byte count and SHA256 before the operator selects the four native lines.
